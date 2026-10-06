"""One local check: policy deny, missing witness, or eval regression."""

from __future__ import annotations

import json
import sys

from agenttrust.evidence import Chain, DecisionOutcome

EXIT_OK = 0
EXIT_POLICY = 1
EXIT_WITNESS = 2
EXIT_REGRESSION = 3


def check_chain(
    chain: Chain,
    *,
    golden_yaml: str | None = None,
    replay_output: str | None = None,
) -> int:
    """Return 0, or 1 policy, 2 witness, 3 regression.

    Policy and witness are read from the chain. Regression asks
    ``agenteval.core.compare.compare_runs`` (the function behind
    ``agenteval compare``) whether a current report regressed against a
    baseline report. The case passes only when the golden ``ground_truth``
    is contained in ``replay_output``. If that package is not installed,
    the same containment check is used and a stderr line says compare did
    not run.
    """
    if chain.decision.outcome != DecisionOutcome.allow:
        return EXIT_POLICY
    if chain.witness is None or chain.witness.matched_expected is not True:
        return EXIT_WITNESS
    if golden_yaml is not None and replay_output is not None:
        if regression_failed(golden_yaml, replay_output):
            return EXIT_REGRESSION
    return EXIT_OK


def regression_failed(golden_yaml: str, replay_output: str) -> bool:
    held = replay_matches_golden(golden_yaml, replay_output)
    try:
        from agenteval.core.compare import compare_runs
    except ImportError:
        print(
            "agenteval compare unavailable; local ground_truth check",
            file=sys.stderr,
        )
        return not held
    result = compare_runs(_passed_report(), _replay_report(held))
    print(
        f"agenteval compare_runs passed={result.passed} reasons={result.reasons}",
        file=sys.stderr,
    )
    return not result.passed


def _passed_report() -> dict[str, object]:
    return _report(passed=True, run_id="agenttrust-baseline")


def _replay_report(held: bool) -> dict[str, object]:
    return _report(passed=held, run_id="agenttrust-current")


def _report(*, passed: bool, run_id: str) -> dict[str, object]:
    return {
        "run_id": run_id,
        "correctness_rate": 1.0 if passed else 0.0,
        "hallucination_rate": 0.0,
        "tool_call_accuracy": 1.0,
        "case_results": [
            {
                "case_id": "agenttrust-case",
                "status": "passed" if passed else "failed",
            }
        ],
    }


def replay_matches_golden(golden_yaml: str, replay_output: str) -> bool:
    truth = ground_truth(golden_yaml)
    return truth in replay_output


def ground_truth(golden_yaml: str) -> str:
    for line in golden_yaml.splitlines():
        stripped = line.strip()
        prefix = "ground_truth:"
        if stripped.startswith(prefix):
            raw = stripped[len(prefix) :].strip()
            value = json.loads(raw)
            if not isinstance(value, str):
                raise ValueError("ground_truth must be a JSON string")
            return value
    raise ValueError("golden YAML has no ground_truth")
