# ADR 0005: Pin AgentEval and call compare_runs for exit 3

**Status:** Accepted  
**Date:** 2026-10-07

## Context

ADR 0001 deferred the AgentEval git SHA. `agenteval compare` (CLI, read at `cli.py` `_cmd_compare` on this SHA) loads an agent registry and then calls `agenteval.core.compare.compare_runs` on two persisted run reports. It does not read this repo's golden YAML. A mock baseline report in `examples/mock_agent/baseline.json` is the shape `compare_runs` accepts: `correctness_rate`, `hallucination_rate`, `tool_call_accuracy`, and `case_results`.

Default `GateThresholds.max_correctness_drop` is `0.05`. A current report at correctness `0.0` against a baseline at `1.0` fails. Two reports at `1.0` pass. A case `status` of `failed` alone does not fail the gate.

## Decision

1. Depend on `nishanttyagi-agenteval` at git SHA `99fa7a5f4edafd44acb6c68d23cb871eb539b7d7` (commit date `2026-10-02T15:40:39Z`, message starts "Add the Release Desk and a provider-neutral judge (0.5.0)").
2. Exit 3 builds that report shape from one fact: the golden `ground_truth` string is, or is not, contained in the replay. Both reports share `case_id` `agenttrust-case`. The pass/fail decision is `compare_runs(...).passed`.
3. Stderr on that path is `agenteval compare_runs passed=...`. This is not the `agenteval compare` CLI. The CLI also requires an agent registry and an adapter.
4. If the import fails, stderr is `agenteval compare unavailable; local ground_truth check` and the containment check decides exit 3.

## Alternatives considered

- **Invoke the CLI with a generated `agents.yaml`.** Rejected. The registry points at an adapter module. Shipping a fake adapter to satisfy the CLI would pretend a run happened.
- **Leave exit 3 as a local substring check with no pin.** Rejected. The pin was the open item in ADR 0001, and the gate thresholds belong to AgentEval.

## Consequences

Installing this repo installs AgentEval's runtime dependencies (PyYAML, pandas, streamlit, sqlglot) because the pin is a direct dependency. The containment test is still this repo's definition of "the case held." `compare_runs` is the regression gate on top of that bit.
