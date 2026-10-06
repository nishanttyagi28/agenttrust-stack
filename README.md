# AgentTrust Stack

**Status: Alpha (`0.1.0`).** PyPI: [`nishanttyagi-agenttrust`](https://pypi.org/project/nishanttyagi-agenttrust/).

[![agenttrust](https://github.com/nishanttyagi28/agenttrust-stack/actions/workflows/agenttrust.yml/badge.svg)](https://github.com/nishanttyagi28/agenttrust-stack/actions/runs/37513293615)

Green Actions run `37513293615` (commit `4c3ac8c`, 45 passed, evidence pack uploaded): https://github.com/nishanttyagi28/agenttrust-stack/actions/runs/37513293615

Later green run with the AgentEval pin, `37514451545`: https://github.com/nishanttyagi28/agenttrust-stack/actions/runs/37514451545

Artifact `evidence-pack` (chain JSON + HTML, 1022 bytes): https://github.com/nishanttyagi28/agenttrust-stack/actions/runs/37513293615/artifacts/11436485460

The control record for consequential agent actions. A payment, an email, a delete, or a release does not ship unless policy allowed it, a human sealed the exact effect, an independent witness confirmed the outcome, and any failure is an approved CI regression.

This repository is the thin product layer over [AgentEval](https://github.com/nishanttyagi28/agenteval), [KarmaSakshi](https://github.com/nishanttyagi28/karmasakshi-protocol), and [CodeGovernor](https://github.com/nishanttyagi28/codegovernor). It imports their evidence. It does not fork them, merge their histories, or reimplement their cryptography.

Eval suites, seal protocols, and policy hooks each prove one clause. The joint chain is the gap in [docs/research/top20-comparison.md](docs/research/top20-comparison.md) and [docs/research/gap-matrix.md](docs/research/gap-matrix.md).

## Business problem

Teams that put agents on money, mail, data, and deploys already own three separate tools.

- An eval suite can score whether the model behaved.
- A seal and witness protocol can bind one effect to a human grant.
- A policy hook can deny a tool call.

None of those artifacts, alone, answers the question a risk owner, an auditor, or a release manager actually asks: **did this exact action leave the building, and can the same failure fail the next build?**

The gap shows up as operational loss.

- A refund agent sends ₹1501 when finance sealed ₹1500.
- A payee changes from Priya to Ravi after the grant was signed.
- A policy deny exists in one log, a trace exists in another, and CI stays green because nobody joined them.
- A human "approves" a failure by chatting about it. The case never becomes a regression.

AgentTrust Stack is the joint record those three tools were missing.

## Impact

For a finance, security, or platform owner, the product changes the release rule.

| Before | After |
|---|---|
| A deny lives in a hook log | CI exits **1** on `deny` or `unknown` |
| A sealed payment can still be attempted wrong | The wrong attempt never reaches commit |
| A witness mismatch is a dashboard note | CI exits **2** when an allowed effect is unwitnessed or unmatched |
| A known failure is tribal knowledge | A human approval writes one golden case; a later miss exits **3** |

Measured on one offline run, 2026-10-06, Python 3.12, `karmasakshi-protocol` 0.2.0. `python -m pytest -q` → **43 passed**.

| Scenario | Result |
|---|---|
| Agent proposes ₹1501 (150100 minor units) to Priya | Exit **1**, rule `AT-PAY-001`, no effect, no witness |
| Finance seal is ₹1500 (150000) to Priya and the agent matches it | Exit **0**, `matched_expected=True`, adapter `payment.simulator`, target `payment:beneficiary/Priya` |
| Later replay text `settled 150100` against the approved golden `blocked` | Exit **3** |
| Replay text that still contains `blocked` | Exit **0** |

That run's manifest hash was `sha256:7c7d7bf38d6ffe3aeabab396a392b27bad6150fbe28765a044809e77f3cdd449`. KarmaSakshi `prepare` draws a nonce, so the hash changes on the next run. The product asserts a non-empty hash and a true witness.

## Solution

One evidence chain. Four clauses. One CI check.

1. **Policy.** `Decision.outcome` is `allow`, `deny`, or `unknown`. Missing policy evidence is `unknown`, and `unknown` fails closed.
2. **Seal.** On allow, `EffectRef` points at the KarmaSakshi manifest hash, adapter, and target resource. On deny or unknown, the effect is null.
3. **Witness.** `Witness.matched_expected` must be true. A false or missing witness fails the allow path.
4. **Regression.** A human sets `EvalCase.approval` to `approved`. Only then is the case written to golden YAML. A later replay that drops the expected ground truth fails CI.

The buyer-facing object is that chain, rendered as one JSON document and one HTML page. There is no second control center in this repo.

## Approach

```text
proposed action
    → gate (rule IDs in code)
        → deny: chain stops, pending eval case, CI red
        → allow: KarmaSakshi prepare → seal → authorize → commit → verify
            → witness attached
                → CI green, or red if the witness does not match
human approve (explicit flag or approval file)
    → golden YAML
        → later replay
            → CI red on regression
```

Rule IDs live in code.

| Rule | Meaning |
|---|---|
| `AT-PAY-001` | Payment amount differs from the sealed effect. Checked before payee, so a wrong amount and a wrong payee still name this rule. |
| `AT-PAY-002` | Payee is not the sealed beneficiary. |
| `AT-MAIL-001` | Email recipient is not on the sealed allowlist. |
| `AT-DEL-001` | Delete target is not on the sealed allowlist. |
| `AT-DEP-001` | Deploy target is not on the sealed allowlist. |

CodeGovernor rule IDs are imported as-is. They are not renumbered. `CG-GATE-002` records that a shell call happened, including allowed calls. A summary that contains only that event is `unknown`. It is not a payment allow.

Human approval is an explicit act. The importer CLI exits 2 and writes nothing unless `--approve` is set with a non-empty actor and note, or an approval file says `"approve": true`. Pending and rejected cases stay out of the golden file.

### Package map

| Path | Import | Role |
|---|---|---|
| `packages/evidence/` | `agenttrust.evidence` | Evidence Schema v1. Canonical JSON. Extra keys rejected. |
| `packages/importers/` | `agenttrust.importers` | One-way maps from AgentEval traces, KarmaSakshi fixtures, and CodeGovernor `summary.json`. |
| `packages/gate/` | `agenttrust.gate` | Compares the proposal to the sealed intent. Attaches a real KarmaSakshi seal and witness on allow. |
| `packages/ci/` | `agenttrust.ci` | Exit 0, 1, 2, or 3. |
| `apps/demo/` | script | Offline ₹1500 → Priya story. |
| `apps/report/` | script | One HTML page from one chain. |
| `apps/ui/` | local server | Live Evidence dashboard (demo only, not a second control center). |

Design: [docs/architecture.md](docs/architecture.md). Decisions: [docs/adr/](docs/adr/). Add this gate to a CI job: [docs/adopt.md](docs/adopt.md).

## Install

**Alpha. Simulators only.** The PyPI distribution is `nishanttyagi-agenttrust`. PyPI rejected `agenttrust-stack` as too similar to an existing project. Imports stay `agenttrust`.

The core dependency is PyPI `nishanttyagi-agenteval>=0.5.0,<0.6` ([0.5.0](https://pypi.org/project/nishanttyagi-agenteval/0.5.0/), provenance SHA `99fa7a5f4edafd44acb6c68d23cb871eb539b7d7`). Exit 3 calls `compare_runs` from that package. See [docs/adr/0007-pypi.md](docs/adr/0007-pypi.md).

| Command | Unlocks |
|---|---|
| `pip install nishanttyagi-agenttrust` | Evidence, gate, CI, and the demo/report entrypoints. Exit 3 calls `compare_runs` when AgentEval imports. |
| `pip install "nishanttyagi-agenttrust[karmasakshi]"` | The row above, plus KarmaSakshi seal and witness on the payment and email simulators. |
| `pip install "nishanttyagi-agenttrust[dev,karmasakshi]"` | The row above, plus pytest. |

There is no `[agenteval]` extra. AgentEval is a direct PyPI dependency, not an optional one.

Supported command now, from a clone, bash and PowerShell:

```bash
python -m pip install -e ".[dev,karmasakshi]"
```

## Proof you can run

Python 3.12. KarmaSakshi 0.2.0 installs on `>=3.10,<3.14`.

Primary, bash and PowerShell, from a clone:

```bash
python -m pip install -e ".[dev,karmasakshi]"
python -m pytest -q
python -m agenttrust.demo
python -m agenttrust.report evidence-pack/chain.json evidence-pack/report.html
```

That install is what Actions ran. Demo stdout from run `37513293615` at `2026-10-06T18:42:12Z`, Python 3.12.14:

```text
red_exit=1
green_exit=0
regression_exit=3
held_exit=0
rule_id=AT-PAY-001
witness_matched=True
adapter_id=payment.simulator
target_resource=payment:beneficiary/Priya
manifest_hash=sha256:e1d380c3105cd715bcd4e37c835f7cdcf6c900f7edb69e7ca9329fa101867372
```

Green-path excerpt from the uploaded `evidence-pack/chain.json` of that same run (ids omitted; hash matches the stdout):

```json
{
  "schema_version": "1.0",
  "chain_id": "demo-right",
  "decision": {
    "outcome": "allow",
    "rule_id": null,
    "reason": "matches sealed payment"
  },
  "effect_ref": {
    "effect_type": "payment.transfer",
    "adapter_id": "payment.simulator",
    "target_resource": "payment:beneficiary/Priya",
    "manifest_hash": "sha256:e1d380c3105cd715bcd4e37c835f7cdcf6c900f7edb69e7ca9329fa101867372"
  },
  "witness": {
    "matched_expected": true,
    "detail": "provider status: settled"
  }
}
```

The 2026-10-06 impact table above is an earlier local run (43 passed, hash `sha256:7c7d7bf38d6ffe3aeabab396a392b27bad6150fbe28765a044809e77f3cdd449`). Hashes move because KarmaSakshi `prepare` draws a nonce. Exit codes matched.

Full notes: [docs/demo.md](docs/demo.md). Workflow: [`.github/workflows/agenttrust.yml`](.github/workflows/agenttrust.yml). Layout: [docs/adr/0004-install-and-evidence-artifact.md](docs/adr/0004-install-and-evidence-artifact.md).



### Local Live Evidence UI

Demo-only dashboard. Not a second control center.

```bash
python -m pip install -e ".[dev,karmasakshi]"
python apps/ui/server.py
```

Open http://127.0.0.1:8765/ and click **Run live demo**. It runs a real `python -m agenttrust.demo` subprocess and shows policy / seal / witness / regression cards.

## Vision

AgentTrust Stack becomes the release gate for any agent that can move money, send mail, delete data, or ship a release.

The durable product is the chain, not another score. Every consequential attempt produces the same document: who proposed it, which rule decided it, which sealed manifest was authorized, what the witness observed, and which approved case will catch the failure next time. Policy engines, eval suites, and effect protocols stay replaceable behind importers. The chain stays the contract a customer, an auditor, and a CI job all read.

v1 proves that contract offline, on a payment simulator, with a human approval that cannot be implied.

## Roadmap

Shipped in this repository:

1. Evidence Schema v1 and round-trip tests.
2. Importers for AgentEval traces, KarmaSakshi regression fixtures, and CodeGovernor `policyEvents`.
3. Human approval before any golden YAML write.
4. Consequential gate with stable rule IDs.
5. KarmaSakshi seal and witness on the payment allow path. A deny does not call commit.
6. One local CI check with exits 1, 2, and 3.
7. Offline wrong-payment demo, red then green.
8. One JSON chain and one HTML page.

Next, in order:

1. Depend on PyPI `nishanttyagi-agenteval>=0.5.0,<0.6` (0.5.0, provenance SHA `99fa7a5f4edafd44acb6c68d23cb871eb539b7d7`). Done. Exit 3 calls `compare_runs`. The `agenteval compare` CLI was not invoked. This package is still not uploaded.
2. Keep the local text check only when that import fails. Stderr names the fallback.
3. `email.send` is sealed on `email.sandbox`. `data.delete` and `deploy.release` stay rule-only until upstream ships those effect types ([ADR 0006](docs/adr/0006-multi-action-seals.md)).
4. Publish a sample evidence pack from a real GitHub Actions run of this workflow, so the README can cite a remote CI URL as well as the local 43-pass run.
5. Keep PromptGate and VisionEval off the v1 path. A later product decision can attach them as siblings. They are not scheduled as forks.

Out of this product on purpose: a second approval inbox, a hosted trace platform, an LLM gateway, and a production bank or mail connector. KarmaSakshi ships reference simulators. This repo uses those simulators.

## Limits, stated so a buyer can price them

- v1 witnesses simulated payments (`payment.simulator`) and sandbox email (`email.sandbox`). `data.delete` and `deploy.release` are deny rules only. KarmaSakshi 0.2.0 has no adapter for those effect types. `sqlite.row.delete` is not relabeled as `data.delete`. See [docs/adr/0006-multi-action-seals.md](docs/adr/0006-multi-action-seals.md).
- A missing CodeGovernor policy event imports as `unknown` and fails CI. It does not become an allow.
- KarmaSakshi requires Python `>=3.10,<3.14`. On 3.14 the attach tests skip.
- Manifest hashes are not golden constants. `prepare` draws a nonce.
- Exit 3 calls `agenteval.core.compare.compare_runs` from `nishanttyagi-agenteval` 0.5.0 (provenance SHA `99fa7a5f4edafd44acb6c68d23cb871eb539b7d7`, the function `agenteval compare` uses). It is not a claim that the `agenteval compare` CLI was invoked. If that package is missing, stderr says `agenteval compare unavailable; local ground_truth check`.
- The PyPI name is `nishanttyagi-agenttrust` 0.1.0. PyPI rejected `agenttrust-stack` as too similar. Imports stay `agenttrust`. AgentEval 0.5.0 is the direct dependency. Publish is GitHub Trusted Publisher on tag `v*`, with no token in this repo.
- Nothing in the importer auto-approves a case.

Research behind the scope: [docs/research/top20-comparison.md](docs/research/top20-comparison.md), [docs/research/gap-matrix.md](docs/research/gap-matrix.md). Status: [docs/progress.md](docs/progress.md).

## License

MIT. Copyright 2026 Nishant Tyagi.
