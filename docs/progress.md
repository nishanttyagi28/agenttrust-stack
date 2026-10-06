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
| 4 | Consequential-action Decision records (gate) | **Done** — `AT-PAY-001` before payee, `AT-PAY-002`, mail/delete/deploy IDs |
| 5 | Attach KarmaSakshi seal and witness | **Done** — real `prepare/seal/authorize/commit/verify`; deny never commits |
| 6 | One local CI check (three fail reasons) | **Done** — exits 1, 2, 3 |
| 7 | Wrong-payment demo acceptance test | **Done** — red exit 1 then green exit 0 |
| 8 | One evidence report (JSON + HTML) | **Done** — `apps/report/render.py` |

### Resolved (orchestrator correction)

**Deny/unknown + EvalCase:** ADR 0002 initially required `eval_case` null on deny; red paths and Gap 3 require an optional pending `EvalCase` with `caused_by: decision.id`. Locked in ADR 0002: deny/unknown forces `effect_ref` and `witness` null; `eval_case` may be present. Fail #1 is immediate on deny/unknown; fail #3 only after human approval, golden write, and a later regression.

### Open questions

None. AgentEval git SHA pin deferred to first importer PR per ADR 0001.

## Importers slice

**Status:** Done (2026-10-06). Orchestrator re-ran `pytest tests/importers tests/evidence`: 30 passed.

`agenttrust` is a namespace package so evidence and importers can share one import name. `CG-GATE-002` alone maps to `unknown`, not allow. Golden YAML is written only after `approve_case`.

## Gate, CI, demo

**Status:** Done (2026-10-06). Orchestrator implemented these slices after reading `karmasakshi-protocol` 0.2.0 (adapter id `payment.simulator`). `python3.12 -m pytest -q`: 43 passed. Demo numbers are in `docs/demo.md` and the README. Local regression check is not an AgentEval CLI run.

## Impact sprint

**P0 product surface:** Done locally (2026-10-07). Not pushed. Human OK required before P1.

README has an Alpha status line, the CI badge, and the existing green run https://github.com/nishanttyagi28/agenttrust-stack/actions/runs/37510342515 (commit `97b52f3`, tests only, no `evidence-pack/` artifact). Impact table stays on the 2026-10-06 numbers. Inline stdout and the green-chain excerpt are from one local run on 2026-10-07; hash `sha256:264730d09ab2a10978af0b9b95249efeefd3693b32271be71d7d4fc0bcd6cd27`.

`pip install -e ".[dev,karmasakshi]"` was attempted on Python 3.12 and failed: `package directory 'packages\ci\agenttrust\evidence' does not exist`. The README states that failure. P1 owns the fix.

### GitHub description (human sets this on the repo page)

`Release gate for consequential agent actions: policy, sealed effect, witness, and an approved CI regression.`

### Checklist before P1

| ID | Status |
|---|---|
| A Install without PYTHONPATH | Open. Editable install fails as above. |
| B Product README | Local only. Badge points at run 37510342515. No artifact link yet. |
| C Evidence-pack artifact | Open. Cited run did not upload one. |
| D AgentEval compare | Open. Exit 3 is still the local text check. |
| E Email, delete, deploy seal | Open. Rule IDs exist. Only payment is sealed. |
| F Version 0.1.0 Alpha | Open. Still `0.0.0` / Planning / Private. |
| G ADRs 0004 and 0005, progress | Progress updated. ADRs not written. |
| H Tests green on Actions after push | Last green run is 37510342515. This slice is not pushed. |

## P1 — install and evidence pack

**Status:** Done (2026-10-07). Pushed. Actions run https://github.com/nishanttyagi28/agenttrust-stack/actions/runs/37513293615 succeeded. 45 passed. Artifact https://github.com/nishanttyagi28/agenttrust-stack/actions/runs/37513293615/artifacts/11436485460 (`evidence-pack`, 1022 bytes). Demo log hash `sha256:e1d380c3105cd715bcd4e37c835f7cdcf6c900f7edb69e7ca9329fa101867372`. Not published to PyPI.

`docs/demo.md` still describes the pre-fix install failure. The README is the current command.

## P2 — AgentEval pin

**Status:** Done locally (2026-10-07). SHA `99fa7a5f4edafd44acb6c68d23cb871eb539b7d7` (2026-10-02, package version 0.5.0). `python3.12 tests/demo/_entry_out/show_compare.py` printed:

```text
agenteval compare_runs passed=False reasons=['correctness dropped 100.0pp (allowed 5.0pp)']
agenteval compare_runs passed=True reasons=[]
```

`settled 150100` against golden `blocked` fails. Replay `blocked` passes. `python3.12 -m pytest -q` → 46 passed. The `agenteval compare` CLI was not run. Fallback line remains if the import is missing.

| ID | Status |
|---|---|
| A Install without PYTHONPATH | **Done** locally and on that Actions run. |
| B Product README | **Done** after the artifact run. Badge and links point at `37513293615`. |
| C Evidence-pack artifact | **Done.** `chain.json` + `report.html`. |
| D AgentEval compare | **Done** via `compare_runs` on SHA `99fa7a5`. CLI not invoked. |
| E Email, delete, deploy seal | Open. Only payment is sealed. |
| F Version 0.1.0 Alpha | **Done.** Private classifier removed. No PyPI upload. |
| G ADRs | **0004 and 0005 accepted.** |
| H Tests green on Actions | Green for `37513293615`. This P2 commit is not on Actions until push. |

