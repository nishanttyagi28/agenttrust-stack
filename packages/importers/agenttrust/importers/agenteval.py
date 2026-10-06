"""AgentEval TraceEnvelope → Evidence Schema v1 Chain."""

from __future__ import annotations

from typing import Any

from agenttrust.evidence import Chain, DecisionOutcome

from agenttrust.importers._common import (
    make_chain,
    make_decision,
    make_eval_case,
    make_event,
    normalize_timestamp,
    slug,
)

NO_CAPTURE_REASON = "content capture off; AgentEval will not export a golden case"


def import_agenteval_trace(data: dict[str, Any]) -> Chain:
    """Map an AgentEval TraceEnvelope JSON object into a Chain."""
    trace_id = data.get("trace_id")
    trace_slug = slug(trace_id if isinstance(trace_id, str) else "trace")
    chain_id = f"chain-ae-{trace_slug}"
    event_id = f"evt-ae-{trace_slug}"
    decision_id = f"dec-ae-{trace_slug}"
    eval_id = f"eval-ae-{trace_slug}"
    case_id = f"ae-{trace_slug}"

    agent_name = data.get("agent_name")
    actor_id = agent_name if isinstance(agent_name, str) and agent_name else "agent"

    occurred_at = data.get("occurred_at")
    timestamp = normalize_timestamp(occurred_at if isinstance(occurred_at, str) else None)

    status = data.get("status")
    status_str = status if isinstance(status, str) else "unknown"

    content_captured = bool(data.get("content_captured"))

    payload: dict[str, Any] = {}
    if isinstance(trace_id, str) and trace_id:
        payload["trace_id"] = trace_id
    payload["status"] = status_str
    payload["content_captured"] = content_captured

    tool_calls = data.get("tool_calls")
    if isinstance(tool_calls, list):
        names: list[str] = []
        for call in tool_calls:
            if isinstance(call, dict):
                name = call.get("name")
                if isinstance(name, str) and name:
                    names.append(name)
        if names:
            payload["tool_names"] = ",".join(names)

    event = make_event(
        event_id=event_id,
        actor_id=actor_id,
        action_type="agent.trace",
        payload=payload,
        timestamp=timestamp,
    )

    if not content_captured:
        decision = make_decision(
            decision_id=decision_id,
            event_id=event_id,
            outcome=DecisionOutcome.unknown,
            rule_id=None,
            reason=NO_CAPTURE_REASON,
        )
        return make_chain(chain_id=chain_id, event=event, decision=decision)

    failure_category = data.get("failure_category")
    reason = (
        failure_category
        if isinstance(failure_category, str) and failure_category
        else status_str
    )

    decision = make_decision(
        decision_id=decision_id,
        event_id=event_id,
        outcome=DecisionOutcome.unknown,
        rule_id=None,
        reason=reason,
    )

    eval_case = None
    prompt = data.get("prompt")
    if status_str == "failed" and isinstance(prompt, str) and prompt:
        eval_case = make_eval_case(
            eval_id=eval_id,
            caused_by=decision_id,
            chain_id=chain_id,
            case_id=case_id,
            prompt=prompt,
            expects={
                "correctness_type": "contains",
                "ground_truth": "failed",
                "must_not_hallucinate": True,
            },
        )

    return make_chain(
        chain_id=chain_id,
        event=event,
        decision=decision,
        eval_case=eval_case,
    )
