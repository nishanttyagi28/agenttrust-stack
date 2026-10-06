# ADR 0003: Importers from upstream shapes, not forks

**Status:** Accepted  
**Date:** 2026-10-06

## Context

Three upstream repos already export overlapping but incompatible artifacts:

| Source | Shape | Gap |
|---|---|---|
| AgentEval | `TraceEnvelope` (schema v1), production YAML, Failure Memory export | No Decision, EffectRef, or Witness on one chain |
| KarmaSakshi | `RegressionFixture` 1.0 (`FIXTURE_SCHEMA_VERSION = "1.0"`), `evidence_pack.v1` | Neutral export; not AgentEval's internal schema; no EvalCase |
| CodeGovernor | `runs/*/summary.json` → `policyEvents` | Coding tools only; hook denials may be absent (ADR 0005) |

Forking or vendoring their test suites (1152 + 1077 tests) into this repo would drown the thin umbrella in foreign history.

## Decision

Implement **one-way mappers** in `packages/importers` that translate upstream inputs into **Evidence Schema v1** `Chain` records (ADR 0002). Mappers never write back to upstream formats except where AgentEval already owns golden YAML export after human approval.

### Importer boundaries

1. **AgentEval importer**
   - Inputs: TraceEnvelope, scored run reports, production case YAML fields.
   - Outputs: `EvalCase` (and supporting `Event` when trace metadata exists).
   - Does not reimplement scoring, clustering, or Failure Memory taxonomy.

2. **KarmaSakshi importer**
   - Inputs: `RegressionFixture` JSON (`schema_version`, `effect_type`, `adapter_id`, `normalized_inputs`, `expected_effect`, `observed_outcome`, `reproduction_metadata.manifest_hash`, etc.); `evidence_pack.v1` for seal/grant/audit slice references.
   - Outputs: `EffectRef`, `Witness`, and `Event` payload fields derived from `normalized_inputs`.
   - Calls `karmasakshi-protocol` verify helpers where needed; does not reimplement seal or grant crypto.

3. **CodeGovernor importer**
   - Inputs: `summary.json` `policyEvents` entries (rule id, tool name, status).
   - Outputs: `Decision` with `outcome: "allow"` or `"deny"` when an event is present.
   - **Missing `policyEvents` for a required coding decision → `Decision.outcome: "unknown"`, never `"allow"`.**

### Fixtures and credentials

- Tests use **checked-in fixtures** under `tests/fixtures/`, copied from upstream public examples and **sanitized** (no live credentials, no private keys).
- Fixtures are not fetched from live services in CI.

### Human approval

- Promoting a failure to a CI golden case requires **explicit human approval**:
  - a CLI flag (e.g. `--approve-case`), **or**
  - an approval file the operator writes (e.g. JSON with `case_id`, `actor`, `note`).
- **Never auto-approve.** Matches AgentEval Failure Memory rules.

### KarmaSakshi FailureMemoryStore

- The KS append-only JSONL memory (`effect_type + adapter_id + failure_category + invariant` signature) is **advisory only**.
- It may inform operator messaging; it **does not** gate CI and **does not** write AgentEval YAML.
- CI fail conditions remain the three in ADR 0002 / architecture.md (deny, unwitnessed consequential effect, eval regression).

### Failure → YAML path (later slice)

`Decision.deny` or `Witness.matched_expected == false` → optional candidate `EvalCase` with `caused_by: decision.id` (deny path) or `caused_by: witness.id` (allow-path mismatch), `approval.state: "pending"` → human approves → exporter writes AgentEval-compatible YAML → `agenteval run` / compare on a **later** run. Pending cases are not in the golden file and do not trigger fail #3. Content capture must be **opted in** before golden export (AgentEval refuses otherwise); that is correct, not a bypass.

## Alternatives considered

- **Fork AgentEval or KarmaSakshi.** Rejected per Phase 0 lock.
- **Treat missing CodeGovernor events as allow.** Rejected. Fails open; contradicts CodeGovernor ADR 0005 honest limits.
- **Auto-promote KS FailureMemoryStore entries to YAML.** Rejected. Removes human gate and duplicates AgentEval's existing review flow.

## Consequences

- Importer PR must pin the reviewed AgentEval `main` SHA (ADR 0001) and add fixture round-trip tests only — not full upstream suites.
- Unknown policy state surfaces as CI red until a human or a better hook integration supplies a Decision.
- Each mapper is independently testable with frozen JSON files.
