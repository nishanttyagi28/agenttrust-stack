"""Offline ₹1500 → Priya story. No network."""

from __future__ import annotations

from agenttrust.ci import check_chain
from agenttrust.evidence import EffectType, canonical_json
from agenttrust.gate import Intent, attach_payment
from agenttrust.importers import approve_case, export_golden_yaml

APPROVED = Intent(EffectType.payment_transfer, "Priya", 150000)
WRONG = Intent(EffectType.payment_transfer, "Priya", 150100)


def run_story() -> dict[str, str | int | bool]:
    wrong = attach_payment(APPROVED, WRONG, chain_id="demo-wrong")
    red = check_chain(wrong)
    approved = approve_case(
        wrong,
        case_id=wrong.eval_case.case_id,  # type: ignore[union-attr]
        actor="finance-approver",
        note="wrong amount must stay blocked",
    )
    golden = export_golden_yaml(approved)
    right = attach_payment(APPROVED, APPROVED, chain_id="demo-right")
    green = check_chain(right)
    replay = "blocked AT-PAY-001"
    regression = check_chain(right, golden_yaml=golden, replay_output="settled 150100")
    held = check_chain(right, golden_yaml=golden, replay_output=replay)
    return {
        "red_exit": red,
        "green_exit": green,
        "regression_exit": regression,
        "held_exit": held,
        "rule_id": wrong.decision.rule_id or "",
        "witness_matched": bool(right.witness and right.witness.matched_expected),
        "adapter_id": right.effect_ref.adapter_id if right.effect_ref else "",
        "manifest_hash": right.effect_ref.manifest_hash if right.effect_ref else "",
        "target_resource": right.effect_ref.target_resource if right.effect_ref else "",
        "golden_has_blocked": "blocked" in golden,
        "wrong_chain": canonical_json(wrong),
        "right_chain": canonical_json(right),
    }


def main() -> int:
    story = run_story()
    print(f"red_exit={story['red_exit']}")
    print(f"green_exit={story['green_exit']}")
    print(f"regression_exit={story['regression_exit']}")
    print(f"held_exit={story['held_exit']}")
    print(f"rule_id={story['rule_id']}")
    print(f"witness_matched={story['witness_matched']}")
    print(f"adapter_id={story['adapter_id']}")
    print(f"target_resource={story['target_resource']}")
    print(f"manifest_hash={story['manifest_hash']}")
    return 0 if story["red_exit"] == 1 and story["green_exit"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
