"""Policy rule IDs and KarmaSakshi attach."""

from __future__ import annotations

import pytest

from agenttrust.evidence import DecisionOutcome, EffectType
from agenttrust.gate import (
    AT_DEL_001,
    AT_DEP_001,
    AT_MAIL_001,
    AT_PAY_001,
    AT_PAY_002,
    Intent,
    attach_payment,
    chain_for_decision,
    decide,
)

APPROVED = Intent(EffectType.payment_transfer, "Priya", 150000)


def test_wrong_amount_is_at_pay_001() -> None:
    outcome, rule_id, _reason = decide(APPROVED, Intent(EffectType.payment_transfer, "Priya", 150100))
    assert outcome == DecisionOutcome.deny
    assert rule_id == AT_PAY_001
    chain = chain_for_decision(
        APPROVED,
        Intent(EffectType.payment_transfer, "Priya", 150100),
        chain_id="wrong-amount",
    )
    assert chain.effect_ref is None
    assert chain.witness is None
    assert chain.eval_case is not None
    assert chain.eval_case.approval.state.value == "pending"


def test_wrong_payee_is_at_pay_002() -> None:
    outcome, rule_id, _reason = decide(APPROVED, Intent(EffectType.payment_transfer, "Ravi", 150000))
    assert outcome == DecisionOutcome.deny
    assert rule_id == AT_PAY_002


def test_amount_rule_wins_when_both_differ() -> None:
    _outcome, rule_id, _reason = decide(APPROVED, Intent(EffectType.payment_transfer, "Ravi", 150100))
    assert rule_id == AT_PAY_001


def test_email_delete_deploy_rule_ids() -> None:
    email = Intent(EffectType.email_send, "priya@example.com")
    assert decide(email, Intent(EffectType.email_send, "other@example.com"))[1] == AT_MAIL_001
    delete = Intent(EffectType.data_delete, "table:refunds")
    assert decide(delete, Intent(EffectType.data_delete, "table:users"))[1] == AT_DEL_001
    deploy = Intent(EffectType.deploy_release, "prod")
    assert decide(deploy, Intent(EffectType.deploy_release, "staging"))[1] == AT_DEP_001


def test_matching_payment_is_allow() -> None:
    outcome, rule_id, _reason = decide(APPROVED, APPROVED)
    assert outcome == DecisionOutcome.allow
    assert rule_id is None


def test_attach_seals_matching_payment_with_karmasakshi() -> None:
    pytest.importorskip("karmasakshi")
    chain = attach_payment(APPROVED, APPROVED, chain_id="priya-ok")
    assert chain.decision.outcome == DecisionOutcome.allow
    assert chain.effect_ref is not None
    assert chain.effect_ref.adapter_id == "payment.simulator"
    assert chain.effect_ref.manifest_hash
    assert "Priya" in chain.effect_ref.target_resource
    assert chain.witness is not None
    assert chain.witness.matched_expected is True


def test_attach_does_not_commit_a_wrong_amount() -> None:
    pytest.importorskip("karmasakshi")
    chain = attach_payment(
        APPROVED,
        Intent(EffectType.payment_transfer, "Priya", 150100),
        chain_id="priya-bad",
    )
    assert chain.decision.rule_id == AT_PAY_001
    assert chain.effect_ref is None
    assert chain.witness is None
