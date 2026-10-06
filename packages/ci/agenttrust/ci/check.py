"""One local check: policy deny, missing witness, or eval regression."""

from __future__ import annotations

import json

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

    Policy and witness are read from the chain. Regression compares
    ``replay_output`` to the ``ground_truth`` string in an AgentEval golden
    YAML file this repo already emits. That is the offline equivalent of
    ``agenteval compare`` for this one case shape.
    """
    if chain.decision.outcome != DecisionOutcome.allow:
        return EXIT_POLICY
    if chain.witness is None or chain.witness.matched_expected is not True:
        return EXIT_WITNESS
    if golden_yaml is not None and replay_output is not None:
        if not replay_matches_golden(golden_yaml, replay_output):
            return EXIT_REGRESSION
    return EXIT_OK


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
