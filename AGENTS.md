# AgentTrust Stack — agent allowlists

This file is guidance. Enforcement is `python tools/check_allowlist.py --agent <name>` plus the orchestrator reading the diff. A markdown rule does not block a write.

Phase 0 decisions are locked. Do not reopen them. Do not put PromptGate or VisionEval on the v1 code path. Do not fork AgentEval, KarmaSakshi, or CodeGovernor.

Product claim: a consequential action cannot ship unless policy allowed it, a human sealed the exact effect when required, the outcome was witnessed, and any failure becomes an approved CI regression.

Backlog order: evidence schema, importers, failure-to-YAML, consequential gate, KarmaSakshi attach, CI check, offline demo, evidence report.

Impact sprint (do not reopen locked decisions): P0 product surface, P1 install and CI evidence pack, P2 AgentEval pin and compare, P3 email/delete/deploy seal, P4 adoption kit. Stop after P0 until a human says OK.

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

## P0 — Product surface

Write only:

- `README.md`
- `docs/demo.md`
- `docs/progress.md`

Product README, dated demo numbers, and a GitHub description note inside `docs/progress.md`. No product code. Do not invent a CI run URL.

## P1 — Install and CI evidence pack

Write only:

- `pyproject.toml`
- `packages/evidence/**`
- `packages/importers/**`
- `packages/gate/**`
- `packages/ci/**`
- `apps/demo/**`
- `apps/report/**`
- `.github/workflows/agenttrust.yml`
- `tests/**`
- `docs/adr/0004-install-and-evidence-artifact.md`
- `docs/progress.md`
- `README.md` (badge and artifact links only, after a green Actions run)

Editable install, version `0.1.0`, Alpha classifier, demo/report entrypoints, workflow artifact `evidence-pack/`. No PyPI upload.

## P2 — AgentEval pin and compare

Write only:

- `pyproject.toml`
- `packages/ci/**`
- `packages/importers/**`
- `tests/ci/**`
- `tests/fixtures/**`
- `docs/adr/0005-agenteval-pin.md`
- `docs/progress.md`
- `README.md` (limits line for compare only)

Pin a reviewed AgentEval git SHA. Exit 3 uses `agenteval compare` when that pin is present. Fallback must log that compare did not run.

## P3 — Multi-action seal surface

Write only:

- `packages/gate/**`
- `tests/gate/**`
- `apps/demo/**`
- `docs/demo.md`
- `docs/progress.md`

Seal and witness `email.send`, `data.delete`, and `deploy.release` through KarmaSakshi reference adapters. Read the library. If an adapter is missing, stop and report. Deny never commits.

## P4 — Adoption kit

Write only:

- `docs/adopt.md`
- `examples/ci-drop-in/**`
- `README.md`
- `docs/progress.md`

One page and a copy-paste CI snippet that matches what P1 shipped. No new service.

## Shared rules

- One concern per agent. Stop and report when the allowlist deliverable is done.
- Conventional commit subjects: `feat(evidence):`, `feat(importers):`, `feat(gate):`, `feat(ci):`, `feat(demo):`, `docs(architecture):`.
- No new dependency without an ADR in `docs/adr/`.
- Do not claim a dependency supports a behavior unless that behavior was read in its source or docs.
