"""One local check: integrity, policy deny, missing witness, or eval regression."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass

from agenttrust.evidence import Chain, DecisionOutcome, verify_text
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

EXIT_OK = 0
EXIT_POLICY = 1
EXIT_WITNESS = 2
EXIT_REGRESSION = 3
EXIT_INTEGRITY = 4


@dataclass
class EvidenceResult:
    """Exit code plus, when integrity failed, why."""

    code: int
    reason: str | None


def check_evidence(
    text: str,
    *,
    golden_yaml: str | None = None,
    replay_output: str | None = None,
    trusted_public_key: Ed25519PublicKey | None = None,
    allow_unsigned: bool = False,
) -> int:
    """Verify a signed evidence document, then apply the usual checks.

    Integrity comes first: a chain whose contents do not match its signature
    says nothing about policy, witness or regression, so it exits 4 rather
    than being partially trusted.
    """
    return check_evidence_result(
        text,
        golden_yaml=golden_yaml,
        replay_output=replay_output,
        trusted_public_key=trusted_public_key,
        allow_unsigned=allow_unsigned,
    ).code


def check_evidence_result(
    text: str,
    *,
    golden_yaml: str | None = None,
    replay_output: str | None = None,
    trusted_public_key: Ed25519PublicKey | None = None,
    allow_unsigned: bool = False,
) -> EvidenceResult:
    """Same as :func:`check_evidence` but also returns the integrity reason."""
    chain, integrity = verify_text(
        text,
        trusted_public_key=trusted_public_key,
        allow_unsigned=allow_unsigned,
    )
    if chain is None or not integrity.ok:
        return EvidenceResult(EXIT_INTEGRITY, integrity.reason)
    return EvidenceResult(
        check_chain(chain, golden_yaml=golden_yaml, replay_output=replay_output),
        None,
    )


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