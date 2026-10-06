# Progress

## Phase 0

**Status:** Accepted (2026-10-06)

- Thin umbrella repo over PyPI/git dependencies — locked.
- Importers only from AgentEval, KarmaSakshi neutral fixtures, CodeGovernor `policyEvents` — locked.
- PromptGate and VisionEval out of v1 code path — locked.
- Backlog order fixed — locked.

## Phase 1 — Architect slice

**Status:** Done (2026-10-06)

Architecture note and ADRs written. No product code.

### Files written

- `docs/architecture.md`
- `docs/adr/0001-thin-umbrella.md`
- `docs/adr/0002-evidence-schema.md`
- `docs/adr/0003-importers-not-forks.md`
- `docs/progress.md`
- `README.md` (outline only)

### Top 8 gaps — checklist

| # | Gap | Status |
|---|---|---|
| 1 | Evidence Schema v1 | **Done** — `agenttrust.evidence`, 17 round-trip tests |
| 2 | Importers from existing repos | **Done** — KS fixture, CG policyEvents, AE trace |
| 3 | Deny / witness-mismatch → candidate → human approve → YAML | **Done** — `approve_case` only; CLI exits 2 without `--approve` |
| 4 | Consequential-action Decision records (gate) | [ ] |
| 5 | Attach KarmaSakshi seal and witness | [ ] |
| 6 | One local CI check (three fail reasons) | [ ] |
| 7 | Wrong-payment demo acceptance test | [ ] |
| 8 | One evidence report (JSON + HTML) | [ ] |

### Resolved (orchestrator correction)

**Deny/unknown + EvalCase:** ADR 0002 initially required `eval_case` null on deny; red paths and Gap 3 require an optional pending `EvalCase` with `caused_by: decision.id`. Locked in ADR 0002: deny/unknown forces `effect_ref` and `witness` null; `eval_case` may be present. Fail #1 is immediate on deny/unknown; fail #3 only after human approval, golden write, and a later regression.

### Open questions

None. AgentEval git SHA pin deferred to first importer PR per ADR 0001.

## Importers slice

**Status:** Done (2026-10-06). Orchestrator re-ran `pytest tests/importers tests/evidence`: 30 passed.

`agenttrust` is a namespace package so evidence and importers can share one import name. `CG-GATE-002` alone maps to `unknown`, not allow. Golden YAML is written only after `approve_case`.

### Next agent

**Gate and CI** — rule IDs in code, KarmaSakshi attach, three CI fail reasons. Not started.
