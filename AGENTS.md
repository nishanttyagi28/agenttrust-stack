# AgentTrust Stack — agent allowlists

This file is guidance. Enforcement is `python tools/check_allowlist.py --agent <name>` plus the orchestrator reading the diff. A markdown rule does not block a write.

Phase 0 decisions are locked. Do not reopen them. Do not put PromptGate or VisionEval on the v1 code path. Do not fork AgentEval, KarmaSakshi, or CodeGovernor.

Product claim: a consequential action cannot ship unless policy allowed it, a human sealed the exact effect when required, the outcome was witnessed, and any failure becomes an approved CI regression.

Backlog order: evidence schema, importers, failure-to-YAML, consequential gate, KarmaSakshi attach, CI check, offline demo, evidence report.

## Architect

Write only:

- `docs/architecture.md`
- `docs/adr/0001-thin-umbrella.md`
- `docs/adr/0002-evidence-schema.md`
- `docs/adr/0003-importers-not-forks.md`
- `docs/progress.md`
- `README.md` (outline only: problem, claim, package map, honest limits, pointers)

Read `docs/research/` first. No Python product code. If a schema field has two irreversible shapes, stop and ask. Otherwise pick the reversible shape and record it in an ADR.

## Evidence

Write only `packages/evidence/**`, `tests/evidence/**`, and `pyproject.toml` when an ADR already allows the dependency. Deterministic models and round-trip tests. No network.

## Importers

Write only `packages/importers/**`, `tests/importers/**`, and `tests/fixtures/**`. Offline fixtures. Human approve is an explicit CLI flag or approval file. Never auto-approve.

## Gate and CI

Write only `packages/gate/**`, `packages/ci/**`, `.github/workflows/agenttrust.yml`, `tests/gate/**`, and `tests/ci/**`. Rule IDs live in code. Do not reimplement KarmaSakshi cryptography.

## Demo and report

Write only `apps/demo/**`, `apps/report/**`, `docs/demo.md`, `README.md`, and `tests/demo/**`. Offline ₹1500→Priya path. One JSON report and one HTML page. Numbers in the README must come from a real run.

## Shared rules

- One concern per agent. Stop and report when the allowlist deliverable is done.
- Conventional commit subjects: `feat(evidence):`, `feat(importers):`, `feat(gate):`, `feat(ci):`, `feat(demo):`, `docs(architecture):`.
- No new dependency without an ADR in `docs/adr/`.
- Do not claim a dependency supports a behavior unless that behavior was read in its source or docs.
