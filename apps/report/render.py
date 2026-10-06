"""One HTML page for a single evidence chain."""

from __future__ import annotations

import html
from pathlib import Path

from agenttrust.evidence import Chain, parse_chain


def render_html(chain: Chain) -> str:
    rows = [
        ("schema_version", chain.schema_version),
        ("chain_id", chain.chain_id),
        ("event", chain.event.action_type),
        ("decision", f"{chain.decision.outcome.value} {chain.decision.rule_id or ''}"),
        ("reason", chain.decision.reason or ""),
        ("effect_ref", _effect(chain)),
        ("witness", _witness(chain)),
        ("eval_case", _case(chain)),
    ]
    body = "\n".join(
        f"<tr><th>{html.escape(name)}</th><td>{html.escape(value)}</td></tr>"
        for name, value in rows
    )
    return (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        "<title>AgentTrust evidence</title></head><body>"
        "<h1>Evidence chain</h1>"
        f"<table>{body}</table></body></html>\n"
    )


def render_file(chain_path: Path, html_path: Path) -> None:
    chain = parse_chain(chain_path.read_text(encoding="utf-8"))
    html_path.write_text(render_html(chain), encoding="utf-8")


def _effect(chain: Chain) -> str:
    if chain.effect_ref is None:
        return "null"
    ref = chain.effect_ref
    return f"{ref.effect_type.value} {ref.target_resource} {ref.manifest_hash}"


def _witness(chain: Chain) -> str:
    if chain.witness is None:
        return "null"
    return f"matched_expected={chain.witness.matched_expected}"


def _case(chain: Chain) -> str:
    if chain.eval_case is None:
        return "null"
    return f"{chain.eval_case.case_id} {chain.eval_case.approval.state.value}"
