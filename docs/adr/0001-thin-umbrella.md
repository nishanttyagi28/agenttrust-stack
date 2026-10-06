# ADR 0001: Thin umbrella repo instead of merging into AgentEval

**Status:** Accepted  
**Date:** 2026-10-06

## Context

Phase 0 research ([gap-matrix.md](../research/gap-matrix.md), [top20-comparison.md](../research/top20-comparison.md)) found the joint claim — policy allow, human seal, witnessed outcome, approved CI regression — is missing as one typed chain and one CI check. AgentEval, KarmaSakshi, and CodeGovernor each own part of the story in separate repos with incompatible shapes.

AgentEval `main` is version **0.5.0** (README, last push 2026-10-02). PyPI still publishes **0.3.0**. KarmaSakshi ships `karmasakshi-protocol` **0.2.0**. CodeGovernor is TypeScript and emits `summary.json` `policyEvents` only for coding tools.

PromptGate has no license file. VisionEval is a sibling product. Neither belongs on the v1 code path.

## Decision

Create **agenttrust-stack** as a thin Python umbrella that:

1. **Depends on upstream packages; does not merge git histories or fork them.**
2. **Defines Evidence Schema v1** (ADR 0002) as the single chain format every package uses.
3. **Imports** from three upstream shapes via one-way mappers (ADR 0003):
   - AgentEval reports / TraceEnvelope / production YAML
   - KarmaSakshi `RegressionFixture` 1.0 and `evidence_pack.v1`
   - CodeGovernor `summary.json` `policyEvents`
4. **Calls** `karmasakshi-protocol` for seal, grant, witness, and portable pack verification. Does not reimplement that cryptography.
5. **Calls** `nishanttyagi-agenteval` for baseline compare and golden-case loading. Does not reimplement Failure Memory clustering.

### Dependency pins

| Package | Pin | Rationale |
|---|---|---|
| `karmasakshi-protocol` | `>=0.2,<0.3` | Matches AgentEval's `[karmasakshi]` extra in its `pyproject.toml`. |
| `nishanttyagi-agenteval` | Git pin of [nishanttyagi28/agenteval](https://github.com/nishanttyagi28/agenteval) **`main` as of 2026-10-02** (README version 0.5.0) | PyPI 0.3.0 lacks bridge and Failure Memory APIs the importers need. **Pin the reviewed main commit SHA in the first importer PR** — do not assume PyPI 0.3.0 API compatibility. |

Schema-only dependencies (ADR 0002): `pydantic>=2.0,<3`, `pytest>=8,<9` for tests. No other runtime or dev dependencies without a new ADR.

## Alternatives considered

- **Merge into AgentEval.** Rejected. AgentEval's v1-readiness doc lists schema versioning as a blocker; mixing a cross-repo contract into an alpha library couples unrelated release trains.
- **Monorepo merge of AE + KS + CG.** Rejected. Different languages (Python + TypeScript), different test counts (1152 + 1077 + Node), and no shared history. The mapper layer is the product, not a git merge.
- **PyPI AgentEval 0.3.0 without git pin.** Rejected. Bridge and 0.5.0 APIs are on `main` only; inventing compatibility shims would lie about behavior.

## Consequences

- Three version pins to maintain until AgentEval 0.5.0 ships on PyPI.
- Importers and CI shell out to or import upstream CLIs; this repo stays small and reviewable.
- Evidence Schema v1 can later move into AgentEval as an optional extra without rewriting gate logic — the ADR shape is reversible via `schema_version`.
- CodeGovernor remains a read-only JSON source; no TypeScript code in this repo.
