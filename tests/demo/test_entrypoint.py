"""Install entrypoints write the ADR 0004 evidence pack."""

from __future__ import annotations

from pathlib import Path

import pytest

from agenttrust.evidence import parse_chain
from apps.demo.run_demo import run_story, write_green_chain
from apps.report.render import main as report_main

OUT = Path("tests/demo/_entry_out")


def test_green_chain_file_and_report() -> None:
    pytest.importorskip("karmasakshi")
    story = run_story()
    chain_path = write_green_chain(story, OUT)
    html_path = OUT / "report.html"
    assert report_main([str(chain_path), str(html_path)]) == 0
    chain = parse_chain(chain_path.read_text(encoding="utf-8"))
    page = html_path.read_text(encoding="utf-8")
    assert chain.decision.outcome.value == "allow"
    assert chain.witness is not None
    assert chain.witness.matched_expected is True
    assert chain.effect_ref is not None
    assert "payment:beneficiary/Priya" in page
    assert "matched_expected=True" in page


def test_report_usage() -> None:
    assert report_main([]) == 2
