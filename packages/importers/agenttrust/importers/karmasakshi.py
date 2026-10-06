"""KarmaSakshi RegressionFixture → Evidence Schema v1 Chain."""

from __future__ import annotations

from typing import Any

from agenttrust.evidence import Chain, DecisionOutcome

from agenttrust.importers._common import (
    EFFECT_TYPE_MAP,
    VALID_EFFECT_TYPES,
    filter_primitive_inputs,
    make_chain,
    make_decision,
    make_effect_ref,
    make_eval_case,
    make_event,
    make_witness,
    slug,
)


def import_karmasakshi_fixture(data: dict[str, Any]) -> Chain:
    """Map a KarmaSakshi RegressionFixture JSON object into a Chain."""
    schema_version = data.get("schema_version")
    if schema_version != "1.0":
        raise ValueError('schema_version must be exactly "1.0"')

    effect_type = data.get("effect_type")
    if effect_type not in VALID_EFFECT_TYPES:
        raise ValueError(f"unsupported effect_type: {effect_type!r}")

    reproduction = data.get("reproduction_metadata")
    if not isinstance(reproduction, dict):
        raise ValueError("reproduction_metadata.manifest_hash is required")
    manifest_hash = reproduction.get("manifest_hash")
    if not isinstance(manifest_hash, str) or not manifest_hash:
        raise ValueError("reproduction_metadata.manifest_hash is required")

    adapter_id = data.get("adapter_id")
    if not isinstance(adapter_id, str) or not adapter_id:
        raise ValueError("adapter_id is required")

    expected_effect = data.get("expected_effect")
    if not isinstance(expected_effect, dict):
        raise ValueError("expected_effect.target_resource is required")
    target_resource = expected_effect.get("target_resource")
    if not isinstance(target_resource, str) or not target_resource:
        raise ValueError("expected_effect.target_resource is required")

    observed = data.get("observed_outcome")
    if not isinstance(observed, dict):
        raise ValueError("observed_outcome is required")
    matched_expected = observed.get("matched_expected")

    failure_category = data.get("failure_category")
    failure_category_str = (
        failure_category if isinstance(failure_category, str) else ""
    )

    normalized_inputs = data.get("normalized_inputs")
    inputs = normalized_inputs if isinstance(normalized_inputs, dict) else {}

    manifest_slug = slug(manifest_hash)
    chain_id = f"chain-ks-{manifest_slug}"
    event_id = f"evt-ks-{manifest_slug}"
    decision_id = f"dec-ks-{manifest_slug}"
    effect_id = f"eff-ks-{manifest_slug}"
    witness_id = f"wit-ks-{manifest_slug}"
    eval_id = f"eval-ks-{manifest_slug}"
    case_id = f"ks-{manifest_slug}"

    action_type = f"{effect_type}.propose"
    event_payload = filter_primitive_inputs(inputs)
    event_payload["failure_category"] = failure_category_str

    if matched_expected is None:
        event_payload["manifest_hash"] = manifest_hash
        event_payload["effect_type"] = effect_type
        event_payload["adapter_id"] = adapter_id
        event = make_event(
            event_id=event_id,
            actor_id="refund-agent",
            action_type=action_type,
            payload=event_payload,
        )
        decision = make_decision(
            decision_id=decision_id,
            event_id=event_id,
            outcome=DecisionOutcome.unknown,
            rule_id=None,
            reason=failure_category_str or "unwitnessed outcome",
        )
        return make_chain(
            chain_id=chain_id,
            event=event,
            decision=decision,
        )

    event = make_event(
        event_id=event_id,
        actor_id="refund-agent",
        action_type=action_type,
        payload=event_payload,
    )

    effect_ref = make_effect_ref(
        effect_id=effect_id,
        decision_id=decision_id,
        manifest_hash=manifest_hash,
        effect_type=EFFECT_TYPE_MAP[effect_type],
        adapter_id=adapter_id,
        target_resource=target_resource,
    )

    detail = observed.get("detail")
    detail_str = detail if isinstance(detail, str) else None

    witness = make_witness(
        witness_id=witness_id,
        effect_id=effect_id,
        matched_expected=bool(matched_expected),
        adapter_id=adapter_id,
        detail=detail_str,
    )

    decision = make_decision(
        decision_id=decision_id,
        event_id=event_id,
        outcome=DecisionOutcome.allow,
        rule_id=None,
        policy_version=None,
        reason=None,
    )

    eval_case = None
    if matched_expected is False:
        prompt = f"ATTEMPT {effect_type} target={target_resource}"
        eval_case = make_eval_case(
            eval_id=eval_id,
            caused_by=witness_id,
            chain_id=chain_id,
            case_id=case_id,
            prompt=prompt,
            expects={
                "correctness_type": "contains",
                "ground_truth": "blocked",
                "must_not_hallucinate": True,
            },
        )

    return make_chain(
        chain_id=chain_id,
        event=event,
        decision=decision,
        effect_ref=effect_ref,
        witness=witness,
        eval_case=eval_case,
    )
