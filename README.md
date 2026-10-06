# AgentTrust Stack

## Problem

Agent teams can score LLM behavior and can seal individual effects, but no single offline artifact proves all four clauses together: policy allowed the action, a human sealed the exact effect, an independent witness confirmed the outcome, and any recurrence is an approved CI regression. Traces, eval suites, and permission tools each tell part of the story.

## Claim

A consequential action cannot ship unless:

1. policy allowed it,
2. a human sealed the exact effect when required,
3. the outcome was witnessed, and
4. any failure becomes an approved CI regression.

## Package map

| Path | Import | Purpose |
|---|---|---|
| `packages/evidence/` | `agenttrust.evidence` | Evidence Schema v1 models |
| `packages/importers/` | `agenttrust.importers` | Map AgentEval, KarmaSakshi, CodeGovernor inputs → Chain |
| `packages/gate/` | `agenttrust.gate` | Consequential-action gate and `Decision` records |
| `packages/ci/` | `agenttrust.ci` | Local CI: deny, unwitnessed effect, eval regression |
| `apps/demo/` | script | Offline ₹1500 → Priya demo |
| `apps/report/` | script | Chain JSON + static HTML report |

Details: [docs/architecture.md](docs/architecture.md)

## Research

Phase 0 comparison and gap analysis:

- [docs/research/top20-comparison.md](docs/research/top20-comparison.md)
- [docs/research/gap-matrix.md](docs/research/gap-matrix.md)

ADRs: [docs/adr/](docs/adr/)

## Honest limits

- **Simulators only** — KarmaSakshi reference adapters, not production payment or mail connectors.
- **Upstream libs not v1-stable** — AgentEval is Alpha; pin git `main` until 0.5.0 reaches PyPI (see ADR 0001).
- **CodeGovernor policy events may be incomplete** — missing hook denials import as `unknown`, not allow.
- **PromptGate and VisionEval are out of path** — not dependencies for v1.
- **No production payment connector** in this repo.
- **Demo metrics** from one offline run on 2026-10-06, Python 3.12, `karmasakshi-protocol` 0.2.0, `python -m pytest -q` → **43 passed**. Wrong payment ₹1501 (150100 minor units) to Priya: CI exit **1**, rule `AT-PAY-001`, no effect and no witness. Sealed ₹1500 (150000) to Priya: CI exit **0**, witness `matched_expected=True`, adapter `payment.simulator`, target `payment:beneficiary/Priya`. Replay text `settled 150100` against the human-approved golden (`ground_truth` `blocked`): CI exit **3**. Replay text that contains `blocked`: exit **0**.
- **Manifest hashes are not stable.** KarmaSakshi `prepare` draws a nonce. That run's hash was `sha256:7c7d7bf38d6ffe3aeabab396a392b27bad6150fbe28765a044809e77f3cdd449`.
- **CI exit 3 is local.** It checks that the golden YAML `ground_truth` appears in the replay text. `agenteval compare` was not executed. AgentEval on PyPI is still 0.3.0; the git pin of main is not a SHA yet.
- **KarmaSakshi requires Python >=3.10,<3.14.** Gate attach tests skip when the package is missing.
- **No auto-approve.** Pending eval cases are not golden YAML. Only `approve_case` sets `approved`.
- **`CG-GATE-002` alone is `unknown`.** It records a shell call, including allowed ones. It is not a payment allow.
