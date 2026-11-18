# ADR 0008: Sign the evidence chain

**Status:** Accepted. Ed25519 signature over canonical JSON, verified before the policy/witness/regression checks. Exit code 4.
**Date:** 2026-11-19

## Context

0.1.0 recorded four things about one action: the policy decision, the sealed
effect, the observed outcome, and the regression case. `check_chain()` read all
four out of the same JSON file and treated them as facts:

```python
if chain.decision.outcome != DecisionOutcome.allow:  return EXIT_POLICY
if chain.witness is None or chain.witness.matched_expected is not True:  return EXIT_WITNESS
```

Nothing bound the file to the run that produced it. Editing the document after
the fact produced these results:

| Mutation | 0.1.0 |
| --- | --- |
| `event.payload.amount_minor` → `999999` | **0 (pass)** |
| `effect_ref.target_resource` → another payee | **0 (pass)** |
| `effect_ref.manifest_hash` → `sha256:000…` | **0 (pass)** |
| `witness.detail` → rewritten | **0 (pass)** |
| `witness.matched_expected` → `false` | 2 |

The README claimed the pack answered "did this exact action happen as
approved". It answered "does this JSON say so". Those are different questions,
and the difference is the whole product.

## Decision

**Sign the canonical JSON of the chain with Ed25519, and verify before anything
else.** Integrity is exit code `4`, and it outranks policy, witness and
regression: an unverifiable chain says nothing about any of them.

Three parts:

1. **`agenttrust.evidence.signing`.** `sign_chain()` returns an envelope
   `{"chain": {...}, "signature": {"alg": "ed25519", "key_id": ..., "sig": ...}}`.
   The signature covers `canonical_json(chain)` — `sort_keys`, no whitespace — so
   reformatting the file does not invalidate it but changing a value does.
   Verification re-parses and re-canonicalizes, so verification never depends on
   how the file was written.
2. **A trust anchor is required.** A signature checked against a public key
   embedded in the same document proves only self-consistency. `verify_document()`
   returns "no trust anchor supplied" unless the caller passes one. The CLI takes
   `--public-key` (a PEM path) or `--demo-key`.
3. **Signing is a required dependency.** `cryptography>=42,<50` moves from the
   `karmasakshi` extra to `dependencies`. KarmaSakshi already pulled it in, so a
   full install is unchanged; a core install now gets a signature-capable wheel.

## What stays the same

`check_chain(chain, ...)` keeps its signature and its exit codes. The existing
tests that hand it a validated `Chain` are untouched. Signing is a layer above
it: `check_evidence(text, ...)` verifies, then delegates.

The bare `evidence-pack/chain.json` is still written, because the report app
reads it and ADR 0004 fixes that layout. The demo additionally writes
`chain.signed.json`, which is the artifact a third party verifies.

## Known limits

- The demo key is derived from a published seed, so anyone can re-sign a forged
  pack with it. `--demo-key` is a convenience for the checked-in demo, not a
  deployment trust anchor. Real use signs with a key the verifier already trusts.
- The signature covers the chain, not the external world. It proves the pack was
  not edited after signing, not that KarmaSakshi's witness is honest. That gap is
  the adapter's job (ADR 0006).
- No key rotation, expiry or revocation. One key, one `key_id`, one anchor.

## Consequences

- Six forgeries that exited 0 now exit 4.
- An unsigned chain exits 4 unless the caller passes `--allow-unsigned`. This is
  a behaviour change for anyone piping a bare chain into `python -m agenttrust.ci`.
- Version is 0.2.0.
