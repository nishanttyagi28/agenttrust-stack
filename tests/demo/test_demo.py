"""Demo and report."""

from __future__ import annotations

import pytest

from apps.demo.run_demo import run_story
from apps.report.render import render_html
from agenttrust.evidence import parse_chain


def test_story_is_red_then_green() -> None:
    pytest.importorskip("karmasakshi")
    story = run_story()
    assert story["red_exit"] == 1
    assert story["green_exit"] == 0
    assert story["regression_exit"] == 3
    assert story["held_exit"] == 0
    assert story["rule_id"] == "AT-PAY-001"
    assert story["witness_matched"] is True
    assert story["adapter_id"] == "payment.simulator"
    assert story["golden_has_blocked"] is True


def test_report_escapes_and_shows_rule() -> None:
    pytest.importorskip("karmasakshi")
    story = run_story()
    chain = parse_chain(str(story["wrong_chain"]))
    page = render_html(chain)
    assert "AT-PAY-001" in page
    assert "<script>" not in page
    assert "null" in page
