"""Offline ₹1500 → Priya story. No network."""

from __future__ import annotations

from pathlib import Path

from agenttrust.ci import check_chain
from agenttrust.evidence import EffectType, canonical_json
from agenttrust.gate import Intent, attach_email, attach_payment, chain_for_decision
from agenttrust.importers import approve_case, export_golden_yaml

APPROVED = Intent(EffectType.payment_transfer, "Priya", 150000)
WRONG = Intent(EffectType.payment_transfer, "Priya", 150100)
MAIL = Intent(EffectType.email_send, "priya@example.com")
MAIL_WRONG = Intent(EffectType.email_send, "ravi@example.com")
DELETE = Intent(EffectType.data_delete, "table:refunds")
DELETE_WRONG = Intent(EffectType.data_delete, "table:users")
DEPLOY = Intent(EffectType.deploy_release, "prod")
DEPLOY_WRONG = Intent(EffectType.deploy_release, "staging")


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
    mail_wrong = attach_email(MAIL, MAIL_WRONG, chain_id="demo-mail-wrong")
    mail_right = attach_email(MAIL, MAIL, chain_id="demo-mail-right")
    delete_wrong = chain_for_decision(DELETE, DELETE_WRONG, chain_id="demo-delete")
    deploy_wrong = chain_for_decision(DEPLOY, DEPLOY_WRONG, chain_id="demo-deploy")
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
        "email_red_exit": check_chain(mail_wrong),
        "email_green_exit": check_chain(mail_right),
        "email_rule_id": mail_wrong.decision.rule_id or "",
        "email_adapter_id": mail_right.effect_ref.adapter_id if mail_right.effect_ref else "",
        "email_witness_matched": bool(mail_right.witness and mail_right.witness.matched_expected),
        "email_target_resource": (
            mail_right.effect_ref.target_resource if mail_right.effect_ref else ""
        ),
        "delete_red_exit": check_chain(delete_wrong),
        "delete_rule_id": delete_wrong.decision.rule_id or "",
        "delete_seal": "blocked",
        "deploy_red_exit": check_chain(deploy_wrong),
        "deploy_rule_id": deploy_wrong.decision.rule_id or "",
        "deploy_seal": "blocked",
    }


def write_green_chain(story: dict[str, str | int | bool], directory: Path) -> Path:
    """Write the allow-path chain. Layout is locked in ADR 0004."""
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "chain.json"
    text = str(story["right_chain"])
    if not text.endswith("\n"):
        text += "\n"
    target.write_text(text, encoding="utf-8")
    return target


def main() -> int:
    story = run_story()
    write_green_chain(story, Path("evidence-pack"))
    print(f"red_exit={story['red_exit']}")
    print(f"green_exit={story['green_exit']}")
    print(f"regression_exit={story['regression_exit']}")
    print(f"held_exit={story['held_exit']}")
    print(f"rule_id={story['rule_id']}")
    print(f"witness_matched={story['witness_matched']}")
    print(f"adapter_id={story['adapter_id']}")
    print(f"target_resource={story['target_resource']}")
    print(f"manifest_hash={story['manifest_hash']}")
    print(f"email_red_exit={story['email_red_exit']}")
    print(f"email_green_exit={story['email_green_exit']}")
    print(f"email_rule_id={story['email_rule_id']}")
    print(f"email_adapter_id={story['email_adapter_id']}")
    print(f"email_witness_matched={story['email_witness_matched']}")
    print(f"email_target_resource={story['email_target_resource']}")
    print(f"delete_red_exit={story['delete_red_exit']}")
    print(f"delete_rule_id={story['delete_rule_id']}")
    print(f"delete_seal={story['delete_seal']}")
    print(f"deploy_red_exit={story['deploy_red_exit']}")
    print(f"deploy_rule_id={story['deploy_rule_id']}")
    print(f"deploy_seal={story['deploy_seal']}")
    ok = (
        story["red_exit"] == 1
        and story["green_exit"] == 0
        and story["email_red_exit"] == 1
        and story["email_green_exit"] == 0
        and story["delete_red_exit"] == 1
        and story["deploy_red_exit"] == 1
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
