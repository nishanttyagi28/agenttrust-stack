"""Tests for offline importers into Evidence Schema v1."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agenttrust.evidence import ApprovalState, DecisionOutcome, parse_chain
from agenttrust.importers import (
    approve_case,
    export_golden_yaml,
    import_agenteval_trace,
    import_codegovernor_summary,
    import_karmasakshi_fixture,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
CLI_TMP = Path(__file__).resolve().parent / "_cli_tmp"
PYTHONPATH = os.pathsep.join(
    [str(REPO_ROOT / "packages" / "evidence"), str(REPO_ROOT / "packages" / "importers")]
)


def _cli_workspace() -> Path:
    CLI_TMP.mkdir(exist_ok=True)
    return CLI_TMP


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = PYTHONPATH
    return subprocess.run(
        [sys.executable, "-m", "agenttrust.importers", *args],
        capture_output=True,
        text=True,
        env=env,
    )


def _load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_ks_mismatch_parses_with_witness_false_and_pending_case() -> None:
    chain = import_karmasakshi_fixture(_load_json("ks_mismatch.json"))
    parsed = parse_chain(json.dumps(chain.model_dump(mode="json")))

    assert parsed.decision.outcome == DecisionOutcome.allow
    assert parsed.effect_ref is not None
    assert parsed.effect_ref.manifest_hash == "sha256:priya-1500"
    assert parsed.witness is not None
    assert parsed.witness.matched_expected is False
    assert parsed.eval_case is not None
    assert parsed.eval_case.caused_by == parsed.witness.id
    assert parsed.eval_case.approval.state == ApprovalState.pending
    assert parsed.eval_case.expects["ground_truth"] == "blocked"


def test_ks_unwitnessed_is_unknown_without_effect_ref() -> None:
    chain = import_karmasakshi_fixture(_load_json("ks_unwitnessed.json"))

    assert chain.decision.outcome == DecisionOutcome.unknown
    assert chain.effect_ref is None
    assert chain.witness is None
    assert chain.eval_case is None


def test_cg_deny_is_deny_without_effect_ref_and_pending_case() -> None:
    chain = import_codegovernor_summary(_load_json("cg_deny.json"))

    assert chain.decision.outcome == DecisionOutcome.deny
    assert chain.decision.rule_id == "CG-SHELL-001"
    assert chain.effect_ref is None
    assert chain.eval_case is not None
    assert chain.eval_case.caused_by == chain.decision.id
    assert chain.eval_case.expects["ground_truth"] == "blocked"


def test_cg_shell_only_is_unknown_not_allow() -> None:
    chain = import_codegovernor_summary(_load_json("cg_shell_only.json"))

    assert chain.decision.outcome == DecisionOutcome.unknown
    assert chain.effect_ref is None
    assert chain.witness is None
    assert "CG-GATE-002" in (chain.decision.reason or "")


def test_cg_missing_is_unknown() -> None:
    chain = import_codegovernor_summary(_load_json("cg_missing.json"))

    assert chain.decision.outcome == DecisionOutcome.unknown
    assert chain.decision.reason == "policyEvents missing"


def test_ae_nocapture_has_no_eval_case() -> None:
    chain = import_agenteval_trace(_load_json("ae_nocapture.json"))

    assert chain.decision.outcome == DecisionOutcome.unknown
    assert chain.eval_case is None


def test_ae_failed_trace_has_pending_case_with_prompt() -> None:
    chain = import_agenteval_trace(_load_json("ae_failed_trace.json"))

    assert chain.eval_case is not None
    assert chain.eval_case.prompt == "Refund order 4821"
    assert chain.eval_case.caused_by == chain.decision.id
    assert chain.eval_case.expects["ground_truth"] == "failed"
    assert chain.eval_case.approval.state == ApprovalState.pending


def test_export_golden_yaml_raises_on_pending() -> None:
    chain = import_karmasakshi_fixture(_load_json("ks_mismatch.json"))

    with pytest.raises(ValueError, match="not approved"):
        export_golden_yaml(chain)


def test_approve_case_then_export_contains_case_fields() -> None:
    chain = import_karmasakshi_fixture(_load_json("ks_mismatch.json"))
    assert chain.eval_case is not None

    approved = approve_case(
        chain,
        case_id=chain.eval_case.case_id,
        actor="finance-approver",
        note="checked mismatch",
    )
    yaml_text = export_golden_yaml(approved)

    assert "id:" in yaml_text
    assert "ground_truth" in yaml_text
    assert chain.eval_case.case_id in yaml_text
    assert "blocked" in yaml_text
    assert "approval:" not in yaml_text
    assert "approved" not in yaml_text.lower().split()


def test_cli_without_approve_exits_2_and_does_not_write() -> None:
    workspace = _cli_workspace()
    chain = import_agenteval_trace(_load_json("ae_failed_trace.json"))
    chain_path = workspace / "chain-no-approve.json"
    out_path = workspace / "cases-no-approve.yaml"
    chain_path.write_text(json.dumps(chain.model_dump(mode="json")), encoding="utf-8")

    result = _run_cli(str(chain_path), "--out", str(out_path))

    assert result.returncode == 2
    assert not out_path.exists()


def test_cli_with_approve_writes_file() -> None:
    workspace = _cli_workspace()
    chain = import_agenteval_trace(_load_json("ae_failed_trace.json"))
    chain_path = workspace / "chain-approve.json"
    out_path = workspace / "cases-approve.yaml"
    chain_path.write_text(json.dumps(chain.model_dump(mode="json")), encoding="utf-8")

    result = _run_cli(
        str(chain_path),
        "--out",
        str(out_path),
        "--approve",
        "--actor",
        "finance-approver",
        "--note",
        "checked",
    )

    assert result.returncode == 0
    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "Refund order 4821" in content
    assert "ground_truth" in content


def test_cli_approval_file_approve_false_exits_2() -> None:
    workspace = _cli_workspace()
    chain = import_agenteval_trace(_load_json("ae_failed_trace.json"))
    chain_path = workspace / "chain-approval-file.json"
    out_path = workspace / "cases-approval-file.yaml"
    approval_path = workspace / "approval-false.json"
    chain_path.write_text(json.dumps(chain.model_dump(mode="json")), encoding="utf-8")
    approval_path.write_text(
        json.dumps(
            {
                "approve": False,
                "case_id": chain.eval_case.case_id if chain.eval_case else "x",
                "actor": "finance-approver",
                "note": "checked",
            }
        ),
        encoding="utf-8",
    )

    result = _run_cli(
        str(chain_path),
        "--out",
        str(out_path),
        "--approval-file",
        str(approval_path),
    )

    assert result.returncode == 2
    assert not out_path.exists()


def test_importers_never_return_approved_cases() -> None:
    ks_mismatch = import_karmasakshi_fixture(_load_json("ks_mismatch.json"))
    ks_unwitnessed = import_karmasakshi_fixture(_load_json("ks_unwitnessed.json"))
    cg_deny = import_codegovernor_summary(_load_json("cg_deny.json"))
    cg_shell = import_codegovernor_summary(_load_json("cg_shell_only.json"))
    cg_missing = import_codegovernor_summary(_load_json("cg_missing.json"))
    ae_failed = import_agenteval_trace(_load_json("ae_failed_trace.json"))
    ae_nocapture = import_agenteval_trace(_load_json("ae_nocapture.json"))

    for chain in (
        ks_mismatch,
        ks_unwitnessed,
        cg_deny,
        cg_shell,
        cg_missing,
        ae_failed,
        ae_nocapture,
    ):
        if chain.eval_case is not None:
            assert chain.eval_case.approval.state == ApprovalState.pending
            assert chain.eval_case.approval.actor is None
            assert chain.eval_case.approval.note is None
