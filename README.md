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
- **Demo metrics** (exit codes, file names, pass counts) will be recorded in a later slice after a real offline run; none are stated here.
