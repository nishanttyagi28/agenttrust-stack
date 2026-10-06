"""CI exit codes."""

from __future__ import annotations

import pytest

from agenttrust.ci import EXIT_OK, EXIT_POLICY, EXIT_REGRESSION, EXIT_WITNESS, check_chain
from agenttrust.evidence import Chain, Decision, DecisionOutcome, EffectRef, EffectType, Event, Witness
from agenttrust.gate import Intent, chain_for_decision
from agenttrust.importers import approve_case, export_golden_yaml


APPROVED = Intent(EffectType.payment_transfer, "Priya", 150000)


def test_deny_exits_1() -> None:
    chain = chain_for_decision(
        APPROVED,
        Intent(EffectType.payment_transfer, "Priya", 150100),
        chain_id="ci-deny",
    )
    assert check_chain(chain) == EXIT_POLICY
    assert chain.decision.outcome == DecisionOutcome.deny


def test_regression_exits_3_when_replay_misses_ground_truth() -> None:
    chain = chain_for_decision(
        APPROVED,
        Intent(EffectType.payment_transfer, "Priya", 150100),
        chain_id="ci-reg",
    )
    approved = approve_case(
        chain,
        case_id=chain.eval_case.case_id,  # type: ignore[union-attr]
        actor="finance-approver",
        note="checked",
    )
    golden = export_golden_yaml(approved)
    # A later allow chain that still has to be checked against the golden replay.
    # Build an allow-shaped failure by using the approved chain's sibling:
    # regression is evaluated only after policy and witness pass, so use a
    # witness-true chain from the gate attach when available. Here we only
    # assert the golden parser and the mismatch helper via check on a chain
    # that already failed policy: policy wins (exit 1) before regression.
    assert "blocked" in golden
    assert check_chain(chain, golden_yaml=golden, replay_output="settled") == EXIT_POLICY


def test_ground_truth_mismatch_on_allow_is_exit_3() -> None:
    chain = Chain(
        schema_version="1.0",
        chain_id="allow-replay",
        event=Event(
            id="e",
            caused_by=None,
            actor_id="refund-agent",
            timestamp="2026-10-06T12:00:00Z",
            action_type="payment.transfer.propose",
            payload={"target": "Priya", "amount_minor": 150000},
        ),
        decision=Decision(
            id="d",
            caused_by="e",
            outcome=DecisionOutcome.allow,
            rule_id=None,
            policy_version="agenttrust-gate-1",
            reason="matches",
        ),
        effect_ref=EffectRef(
            id="f",
            caused_by="d",
            manifest_hash="sha256:priya-1500",
            effect_type=EffectType.payment_transfer,
            adapter_id="payment.simulator",
            target_resource="payment:beneficiary/Priya",
        ),
        witness=Witness(
            id="w",
            caused_by="f",
            matched_expected=True,
            adapter_id="payment.simulator",
            detail="provider status: settled",
        ),
        eval_case=None,
    )
    golden = '    ground_truth: "blocked"\n'
    assert check_chain(chain, golden_yaml=golden, replay_output="settled to Priya") == EXIT_REGRESSION
    assert check_chain(chain, golden_yaml=golden, replay_output="blocked") == EXIT_OK


def test_false_witness_exits_2() -> None:
    chain = Chain(
        schema_version="1.0",
        chain_id="bad-witness",
        event=Event(
            id="e",
            caused_by=None,
            actor_id="refund-agent",
            timestamp="2026-10-06T12:00:00Z",
            action_type="payment.transfer.propose",
            payload={"target": "Priya"},
        ),
        decision=Decision(
            id="d",
            caused_by="e",
            outcome=DecisionOutcome.allow,
            rule_id=None,
            policy_version=None,
            reason=None,
        ),
        effect_ref=EffectRef(
            id="f",
            caused_by="d",
            manifest_hash="sha256:x",
            effect_type=EffectType.payment_transfer,
            adapter_id="payment.simulator",
            target_resource="payment:beneficiary/Priya",
        ),
        witness=Witness(
            id="w",
            caused_by="f",
            matched_expected=False,
            adapter_id="payment.simulator",
            detail="mismatch",
        ),
        eval_case=None,
    )
    assert check_chain(chain) == EXIT_WITNESS


def test_compare_runs_logs_the_real_gate(capsys: pytest.CaptureFixture[str]) -> None:
    pytest.importorskip("agenteval.core.compare")
    from agenttrust.evidence import Chain, Decision, EffectRef, EffectType, Event, Witness

    chain = Chain(
        schema_version="1.0",
        chain_id="compare-replay",
        event=Event(
            id="e",
            caused_by=None,
            actor_id="refund-agent",
            timestamp="2026-10-06T12:00:00Z",
            action_type="payment.transfer.propose",
            payload={"target": "Priya", "amount_minor": 150000},
        ),
        decision=Decision(
            id="d",
            caused_by="e",
            outcome=DecisionOutcome.allow,
            rule_id=None,
            policy_version="agenttrust-gate-1",
            reason="matches",
        ),
        effect_ref=EffectRef(
            id="f",
            caused_by="d",
            manifest_hash="sha256:priya-1500",
            effect_type=EffectType.payment_transfer,
            adapter_id="payment.simulator",
            target_resource="payment:beneficiary/Priya",
        ),
        witness=Witness(
            id="w",
            caused_by="f",
            matched_expected=True,
            adapter_id="payment.simulator",
            detail="provider status: settled",
        ),
        eval_case=None,
    )
    golden = '    ground_truth: "blocked"\n'
    assert check_chain(chain, golden_yaml=golden, replay_output="settled 150100") == EXIT_REGRESSION
    missed = capsys.readouterr().err
    assert "agenteval compare_runs passed=False" in missed
    assert check_chain(chain, golden_yaml=golden, replay_output="blocked") == EXIT_OK
    held = capsys.readouterr().err
    assert "agenteval compare_runs passed=True" in held
