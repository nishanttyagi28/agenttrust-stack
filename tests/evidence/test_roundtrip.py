"""Round-trip and rejection tests for Evidence Schema v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from agenttrust.evidence import (
    Chain,
    canonical_json,
    json_schema,
    parse_chain,
)

FIXTURES = Path(__file__).parent / "fixtures"
GOLDEN_FIXTURES = [
    "allow_priya.json",
    "deny_amount.json",
    "unknown_policy.json",
]


def _load_fixture(name: str) -> str:
    text = (FIXTURES / name).read_text(encoding="utf-8")
    assert text.endswith("\n"), f"{name} must end with a trailing newline"
    return text.rstrip("\n")


def _canonical_dict(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@pytest.mark.parametrize("fixture_name", GOLDEN_FIXTURES)
def test_golden_fixture_matches_canonical_json(fixture_name: str) -> None:
    raw = _load_fixture(fixture_name)
    chain = parse_chain(raw)
    assert canonical_json(chain) == raw


@pytest.mark.parametrize("fixture_name", GOLDEN_FIXTURES)
def test_roundtrip_is_stable(fixture_name: str) -> None:
    first = parse_chain(_load_fixture(fixture_name))
    encoded = canonical_json(first)
    second = parse_chain(encoded)
    assert canonical_json(second) == encoded


def test_json_schema_matches_checked_in_file() -> None:
    expected = json.loads((FIXTURES / "chain.schema.json").read_text(encoding="utf-8"))
    actual = json_schema()
    assert _canonical_dict(actual) == _canonical_dict(expected)


def test_reject_extra_key_on_chain() -> None:
    payload = json.loads(_load_fixture("allow_priya.json"))
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        Chain.model_validate(payload)


def test_reject_deny_with_non_null_effect_ref() -> None:
    payload = json.loads(_load_fixture("deny_amount.json"))
    payload["effect_ref"] = {
        "id": "eff-bad",
        "caused_by": payload["decision"]["id"],
        "manifest_hash": "sha256:bad",
        "effect_type": "payment.transfer",
        "adapter_id": "payment.simulator.v1",
        "target_resource": "Priya",
    }
    with pytest.raises(ValidationError, match="effect_ref must be null"):
        Chain.model_validate(payload)


def test_reject_allow_without_witness() -> None:
    payload = json.loads(_load_fixture("allow_priya.json"))
    payload["witness"] = None
    with pytest.raises(ValidationError, match="witness is required"):
        Chain.model_validate(payload)


def test_reject_deny_with_null_rule_id() -> None:
    payload = json.loads(_load_fixture("deny_amount.json"))
    payload["decision"]["rule_id"] = None
    with pytest.raises(ValidationError, match="rule_id is required"):
        Chain.model_validate(payload)


def test_reject_invalid_rule_id() -> None:
    payload = json.loads(_load_fixture("deny_amount.json"))
    payload["decision"]["rule_id"] = "nopolicy"
    with pytest.raises(ValidationError, match="rule_id must match"):
        Chain.model_validate(payload)


def test_reject_eval_case_caused_by_event_on_deny_chain() -> None:
    payload = json.loads(_load_fixture("deny_amount.json"))
    payload["eval_case"]["caused_by"] = payload["event"]["id"]
    with pytest.raises(ValidationError, match="eval_case.caused_by must equal decision.id"):
        Chain.model_validate(payload)


def test_reject_schema_version_1_1() -> None:
    payload = json.loads(_load_fixture("allow_priya.json"))
    payload["schema_version"] = "1.1"
    with pytest.raises(ValidationError, match='schema_version must be exactly "1.0"'):
        Chain.model_validate(payload)


def test_reject_duplicate_ids() -> None:
    payload = json.loads(_load_fixture("allow_priya.json"))
    payload["witness"]["id"] = payload["event"]["id"]
    with pytest.raises(ValidationError, match="all record ids in the chain must be unique"):
        Chain.model_validate(payload)


def test_reject_list_inside_payload() -> None:
    payload = json.loads(_load_fixture("allow_priya.json"))
    payload["event"]["payload"]["tags"] = ["bad"]
    with pytest.raises(ValidationError, match="payload must not contain lists"):
        Chain.model_validate(payload)


def test_unicode_beneficiary_survives_canonical_json() -> None:
    for fixture_name in ("allow_priya.json", "deny_amount.json"):
        raw = _load_fixture(fixture_name)
        chain = parse_chain(raw)
        encoded = canonical_json(chain)
        assert "Priya" in encoded
        assert "\\u" not in encoded
        assert chain.event.payload["beneficiary"] == "Priya"
