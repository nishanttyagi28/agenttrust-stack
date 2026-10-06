"""CodeGovernor summary.json → Evidence Schema v1 Chain."""

from __future__ import annotations

from typing import Any

from agenttrust.evidence import Chain, DecisionOutcome

from agenttrust.importers._common import (
    make_chain,
    make_decision,
    make_eval_case,
    make_event,
    slug,
)

SHELL_RECORDED_RULE = "CG-GATE-002"


def import_codegovernor_summary(data: dict[str, Any]) -> Chain:
    """Map a CodeGovernor summary.json object into a Chain.

    CG-GATE-002-only summaries map to unknown because shell-call recording
    is not a consequential allow without an EffectRef.
    """
    raw_events = data.get("policyEvents")
    events = raw_events if isinstance(raw_events, list) else None

    chain_id = "chain-cg-summary"
    event_id = "evt-cg-summary"
    decision_id = "dec-cg-summary"
    eval_id = "eval-cg-summary"
    case_id = "cg-summary"

    if not events:
        event = make_event(
            event_id=event_id,
            actor_id="coder",
            action_type="coding.tool",
            payload={"reason": "policyEvents missing"},
        )
        decision = make_decision(
            decision_id=decision_id,
            event_id=event_id,
            outcome=DecisionOutcome.unknown,
            rule_id=None,
            reason="policyEvents missing",
        )
        return make_chain(chain_id=chain_id, event=event, decision=decision)

    first = events[0] if isinstance(events[0], dict) else {}
    role = first.get("role")
    actor_id = role if isinstance(role, str) and role else "coder"
    tool = first.get("tool")
    tool_str = tool if isinstance(tool, str) else ""
    label = first.get("label")
    label_str = label if isinstance(label, str) else ""

    payload: dict[str, str] = {}
    if tool_str:
        payload["tool"] = tool_str
    if label_str:
        payload["label"] = label_str

    event = make_event(
        event_id=event_id,
        actor_id=actor_id,
        action_type="coding.tool",
        payload=payload,
    )

    rule_ids: list[str] = []
    deny_event: dict[str, Any] | None = None
    for item in events:
        if not isinstance(item, dict):
            continue
        rule_id = item.get("ruleId")
        if isinstance(rule_id, str) and rule_id:
            rule_ids.append(rule_id)
            if rule_id != SHELL_RECORDED_RULE and deny_event is None:
                deny_event = item

    if deny_event is not None:
        deny_rule = deny_event.get("ruleId")
        if not isinstance(deny_rule, str):
            deny_rule = "CG-UNKNOWN-001"
        detail = deny_event.get("detail")
        reason = detail if isinstance(detail, str) and detail else "policy deny"
        deny_tool = deny_event.get("tool")
        deny_tool_str = deny_tool if isinstance(deny_tool, str) else tool_str
        rule_slug = slug(deny_rule)
        chain_id = f"chain-cg-{rule_slug}"
        event_id = f"evt-cg-{rule_slug}"
        decision_id = f"dec-cg-{rule_slug}"
        eval_id = f"eval-cg-{rule_slug}"
        case_id = f"cg-{rule_slug}"

        event = make_event(
            event_id=event_id,
            actor_id=actor_id,
            action_type="coding.tool",
            payload=payload,
        )
        decision = make_decision(
            decision_id=decision_id,
            event_id=event_id,
            outcome=DecisionOutcome.deny,
            rule_id=deny_rule,
            reason=reason,
        )
        prompt = f"coding-agent {deny_tool_str} {deny_rule}"
        eval_case = make_eval_case(
            eval_id=eval_id,
            caused_by=decision_id,
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
            eval_case=eval_case,
        )

    if rule_ids and all(rule_id == SHELL_RECORDED_RULE for rule_id in rule_ids):
        chain_id = "chain-cg-shell-only"
        event_id = "evt-cg-shell-only"
        decision_id = "dec-cg-shell-only"
        event = make_event(
            event_id=event_id,
            actor_id=actor_id,
            action_type="coding.tool",
            payload=payload,
        )
        decision = make_decision(
            decision_id=decision_id,
            event_id=event_id,
            outcome=DecisionOutcome.unknown,
            rule_id=None,
            reason="shell call recorded (CG-GATE-002) is not a consequential allow",
        )
        return make_chain(chain_id=chain_id, event=event, decision=decision)

    event = make_event(
        event_id=event_id,
        actor_id=actor_id,
        action_type="coding.tool",
        payload=payload,
    )
    decision = make_decision(
        decision_id=decision_id,
        event_id=event_id,
        outcome=DecisionOutcome.unknown,
        rule_id=None,
        reason="policyEvents missing",
    )
    return make_chain(chain_id=chain_id, event=event, decision=decision)
