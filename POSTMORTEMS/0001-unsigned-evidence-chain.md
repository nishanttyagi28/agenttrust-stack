# 0001: The evidence chain was not tamper-evident

**Severity:** high
**Affected:** `nishanttyagi-agenttrust` 0.1.0, `packages/ci/agenttrust/ci/check.py`
**Introduced:** 2026-10-06  **Found:** 2026-11-19  **Fixed:** 2026-11-19
**Time it existed undetected:** 44 days

## What we believed

The README shipped this sentence:

> "Teams that let agents move money or send mail tend to end up with three
> separate pieces of evidence... None of them alone answers **'did this exact
> action happen as approved'**"

and this limitation:

> "Alpha (0.1.0). It has only been run offline against simulators, not real
> payment or mail providers."

The limitation was about the *environment*. There was no limitation about the
*evidence itself*, because I believed the evidence was the strong part.

## What was true

The check read the amount, the payee, the manifest hash and the witness outcome
out of the same JSON file it was judging, and treated all four as facts.

```python
if chain.decision.outcome != DecisionOutcome.allow:  return EXIT_POLICY
if chain.witness is None or chain.witness.matched_expected is not True:  return EXIT_WITNESS
```

Nothing bound the document to the run that produced it. There was no signature
anywhere in `models.py`, and `canonical_json()` was defined but nothing ever
signed it.

So the pack answered *"does this JSON say so?"*. It did not answer *"did this
action happen?"*. Those are different questions, and the difference is the
entire product.

A forged pack could claim ₹9,999.99 to any beneficiary and pass CI.

## How it was found

An adversarial review of the repo cloned it, ran the demo on Python 3.12, then
edited fields in `evidence-pack/chain.json` and re-ran the check, recording the
exit code each time:

| Mutation | Exit | Expected |
| --- | --- | --- |
| `event.payload.amount_minor` → `999999` | **0** | non-zero |
| `effect_ref.target_resource` → another payee | **0** | non-zero |
| `effect_ref.manifest_hash` → `sha256:000…` | **0** | non-zero |
| `witness.detail` → rewritten | **0** | non-zero |
| `witness.matched_expected` → `false` | 2 | 2 (correct) |

Three of the five edits passed a check whose only job was to detect exactly
that.

## Why it survived review and CI

Three reasons, and the third is the process failure:

1. **The tests tested the schema, not the threat.** Every test constructed a
   `Chain` in Python and called `check_chain()`. Not one of them started from a
   file on disk that had been edited. The property under test was "does a
   well-formed chain produce the right code" instead of "can a wrong chain
   produce the right code".
2. **Exit codes created false confidence.** 0/1/2/3 with a documented table
   *looks* like a security model. A reviewer reads the table and assumes the
   boundaries are load-bearing. They were conventions.
3. **The demo produced evidence nobody attacked.** `python -m agenttrust.demo`
   generated a correct chain and verified it. A check that only ever sees
   honest input is an assertion, not a control.

The 48 passing tests were real and all of them were compatible with the bug.
That is the lesson worth keeping: **a green suite measures what you thought to
ask, and an attacker asks what you did not.**

## What changed

- [ADR 0008](../docs/adr/0008-signed-evidence.md): Ed25519 signature over the
  canonical JSON, verified before the policy/witness/regression checks.
- Integrity is exit **4** and outranks 1–3, because an unverifiable chain says
  nothing about policy, witness or regression.
- Verification refuses to run without a caller-supplied trust anchor. A key
  shipped inside the same document proves only self-consistency.
- `cryptography>=42,<50` moved from the `karmasakshi` extra to `dependencies`.
- `check_chain()` was left unchanged — the fix is a layer above it, so the
  existing tests still mean what they meant.

Tests added in `tests/evidence/test_signing.py` (22), including the four that
would have caught this directly:
`test_editing_a_signed_chain_is_caught`,
`test_tampered_amount_exits_4_through_the_ci_check`,
`test_unsigned_chain_is_rejected_by_default`,
`test_signature_without_a_trust_anchor_is_rejected`.

CI now runs `python -m agenttrust.ci evidence-pack/chain.signed.json --demo-key`,
so a tampered pack fails the build rather than being described in prose.

## What we did not fix

- The signature covers the chain, not the world. It proves the pack was not
  edited after signing. It does not prove KarmaSakshi's witness is honest — that
  is the adapter's job (ADR 0006).
- The demo key is derived from a published seed. `--demo-key` is a convenience
  for the checked-in demo and is not a deployment trust anchor.
- No key rotation, expiry or revocation.
- Exit 3 still compares a synthesized baseline against a synthesized replay
  rather than two real AgentEval report files. That gate demonstrates
  integration; it does not yet demonstrate regression detection.

## What we would do differently

When a README makes a security claim, the threat model should be written as a
**test that attacks the claim** in the same commit as the claim — not 44 days
later, by someone else. "Signature verified" is now a test name; "the pack is
tamper-evident" is not.
