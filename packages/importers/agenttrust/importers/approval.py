"""Human approval and AgentEval golden YAML export."""

from __future__ import annotations

import json
from typing import Any

from agenttrust.evidence import (
    Approval,
    ApprovalState,
    Chain,
    DecisionOutcome,
    EvalCase,
)


def attach_pending_case(chain: Chain) -> Chain:
    """Attach a pending EvalCase when the chain lacks one but warrants it."""
    if chain.eval_case is not None:
        return chain

    outcome = chain.decision.outcome
    eval_case: EvalCase | None = None

    if outcome in (DecisionOutcome.deny, DecisionOutcome.unknown):
        case_id = f"{chain.chain_id}-blocked"
        eval_case = EvalCase(
            id=f"eval-{case_id}",
            caused_by=chain.decision.id,
            chain_id=chain.chain_id,
            case_id=case_id,
            prompt=chain.event.action_type,
            expects={
                "correctness_type": "contains",
                "ground_truth": "blocked",
                "must_not_hallucinate": True,
            },
            approval=Approval(state=ApprovalState.pending, actor=None, note=None),
        )
    elif (
        outcome == DecisionOutcome.allow
        and chain.witness is not None
        and chain.witness.matched_expected is False
    ):
        case_id = f"{chain.chain_id}-mismatch"
        eval_case = EvalCase(
            id=f"eval-{case_id}",
            caused_by=chain.witness.id,
            chain_id=chain.chain_id,
            case_id=case_id,
            prompt=chain.event.action_type,
            expects={
                "correctness_type": "contains",
                "ground_truth": "mismatch",
                "must_not_hallucinate": True,
            },
            approval=Approval(state=ApprovalState.pending, actor=None, note=None),
        )

    if eval_case is None:
        return chain

    return chain.model_copy(update={"eval_case": eval_case})


def approve_case(
    chain: Chain,
    *,
    case_id: str,
    actor: str,
    note: str,
) -> Chain:
    """Mark an EvalCase approved. This is the only approval path."""
    if not actor or not note:
        raise ValueError("actor and note must be non-empty strings")
    if chain.eval_case is None:
        raise ValueError("chain has no eval_case to approve")
    if chain.eval_case.case_id != case_id:
        raise ValueError("case_id does not match chain eval_case.case_id")

    approved = Approval(state=ApprovalState.approved, actor=actor, note=note)
    updated_case = chain.eval_case.model_copy(update={"approval": approved})
    return chain.model_copy(update={"eval_case": updated_case})


def export_golden_yaml(chain: Chain) -> str:
    """Export an approved EvalCase as AgentEval-compatible golden YAML."""
    if chain.eval_case is None:
        raise ValueError("chain has no eval_case")
    if chain.eval_case.approval.state != ApprovalState.approved:
        raise ValueError("eval_case is not approved")

    case = chain.eval_case
    expects: dict[str, Any] = case.expects
    correctness_type = expects.get("correctness_type", "contains")
    ground_truth = expects.get("ground_truth", "")
    must_not_hallucinate = expects.get("must_not_hallucinate", True)

    lines = [
        f"- id: {case.case_id}",
        f"  prompt: {json.dumps(case.prompt)}",
        "  expects:",
        f"    correctness_type: {correctness_type}",
        f"    ground_truth: {json.dumps(ground_truth)}",
        f"    must_not_hallucinate: {str(must_not_hallucinate).lower()}",
        "    must_call_tools: []",
    ]
    return "\n".join(lines) + "\n"
