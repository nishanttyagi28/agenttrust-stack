"""Shared helpers for importers."""

from __future__ import annotations

import re
from typing import Any

from agenttrust.evidence import (
    Approval,
    ApprovalState,
    Chain,
    Decision,
    DecisionOutcome,
    EffectRef,
    EffectType,
    EvalCase,
    Event,
    Witness,
)

FIXED_TIMESTAMP = "2026-10-06T12:00:00Z"
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

VALID_EFFECT_TYPES = {
    "payment.transfer",
    "email.send",
    "data.delete",
    "deploy.release",
}

EFFECT_TYPE_MAP = {
    "payment.transfer": EffectType.payment_transfer,
    "email.send": EffectType.email_send,
    "data.delete": EffectType.data_delete,
    "deploy.release": EffectType.deploy_release,
}


def slug(value: str) -> str:
    """Turn an upstream id into a stable slug for chain record ids."""
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip())
    return cleaned.strip("-") or "unknown"


def normalize_timestamp(value: str | None) -> str:
    if value and TIMESTAMP_RE.match(value):
        return value
    return FIXED_TIMESTAMP


def filter_primitive_inputs(data: dict[str, Any]) -> dict[str, Any]:
    """Keep only JSON primitives allowed in Event.payload."""
    payload: dict[str, Any] = {}
    for key, item in data.items():
        if not isinstance(key, str):
            continue
        if item is None or isinstance(item, (str, int, bool)):
            payload[key] = item
    return payload


def pending_approval() -> Approval:
    return Approval(state=ApprovalState.pending, actor=None, note=None)


def make_event(
    *,
    event_id: str,
    actor_id: str,
    action_type: str,
    payload: dict[str, Any],
    timestamp: str = FIXED_TIMESTAMP,
) -> Event:
    return Event(
        id=event_id,
        caused_by=None,
        actor_id=actor_id,
        timestamp=timestamp,
        action_type=action_type,
        payload=payload,
    )


def make_decision(
    *,
    decision_id: str,
    event_id: str,
    outcome: DecisionOutcome,
    rule_id: str | None = None,
    policy_version: str | None = None,
    reason: str | None = None,
) -> Decision:
    return Decision(
        id=decision_id,
        caused_by=event_id,
        outcome=outcome,
        rule_id=rule_id,
        policy_version=policy_version,
        reason=reason,
    )


def make_effect_ref(
    *,
    effect_id: str,
    decision_id: str,
    manifest_hash: str,
    effect_type: EffectType,
    adapter_id: str,
    target_resource: str,
) -> EffectRef:
    return EffectRef(
        id=effect_id,
        caused_by=decision_id,
        manifest_hash=manifest_hash,
        effect_type=effect_type,
        adapter_id=adapter_id,
        target_resource=target_resource,
    )


def make_witness(
    *,
    witness_id: str,
    effect_id: str,
    matched_expected: bool | None,
    adapter_id: str,
    detail: str | None,
) -> Witness:
    return Witness(
        id=witness_id,
        caused_by=effect_id,
        matched_expected=matched_expected,
        adapter_id=adapter_id,
        detail=detail,
    )


def make_eval_case(
    *,
    eval_id: str,
    caused_by: str,
    chain_id: str,
    case_id: str,
    prompt: str,
    expects: dict[str, Any],
) -> EvalCase:
    return EvalCase(
        id=eval_id,
        caused_by=caused_by,
        chain_id=chain_id,
        case_id=case_id,
        prompt=prompt,
        expects=expects,
        approval=pending_approval(),
    )


def make_chain(
    *,
    chain_id: str,
    event: Event,
    decision: Decision,
    effect_ref: EffectRef | None = None,
    witness: Witness | None = None,
    eval_case: EvalCase | None = None,
) -> Chain:
    return Chain(
        schema_version="1.0",
        chain_id=chain_id,
        event=event,
        decision=decision,
        effect_ref=effect_ref,
        witness=witness,
        eval_case=eval_case,
    )
