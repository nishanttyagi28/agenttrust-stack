"""CLI: approve an EvalCase and export AgentEval golden YAML."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agenttrust.evidence import parse_chain

from agenttrust.importers.approval import approve_case, export_golden_yaml


def _load_approval_file(path: Path) -> tuple[bool, str, str, str] | None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    if not payload.get("approve"):
        return None
    case_id = payload.get("case_id")
    actor = payload.get("actor")
    note = payload.get("note")
    if not isinstance(case_id, str) or not case_id:
        return None
    if not isinstance(actor, str) or not actor:
        return None
    if not isinstance(note, str) or not note:
        return None
    return True, case_id, actor, note


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export an approved EvalCase to AgentEval golden YAML."
    )
    parser.add_argument("chain", type=Path, help="Path to Chain JSON")
    parser.add_argument("--out", type=Path, required=True, help="Output YAML path")
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Approve the chain eval_case before export",
    )
    parser.add_argument("--actor", type=str, default="", help="Approval actor id")
    parser.add_argument("--note", type=str, default="", help="Approval note")
    parser.add_argument(
        "--approval-file",
        type=Path,
        default=None,
        help='JSON file: {"approve": true, "case_id": "...", "actor": "...", "note": "..."}',
    )
    args = parser.parse_args(argv)

    chain_text = args.chain.read_text(encoding="utf-8")
    chain = parse_chain(chain_text)

    approved_chain = None
    if args.approval_file is not None:
        approval = _load_approval_file(args.approval_file)
        if approval is None:
            return 2
        _, case_id, actor, note = approval
        approved_chain = approve_case(chain, case_id=case_id, actor=actor, note=note)
    elif args.approve and args.actor and args.note:
        if chain.eval_case is None:
            return 2
        approved_chain = approve_case(
            chain,
            case_id=chain.eval_case.case_id,
            actor=args.actor,
            note=args.note,
        )
    else:
        return 2

    yaml_text = export_golden_yaml(approved_chain)
    args.out.write_text(yaml_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
