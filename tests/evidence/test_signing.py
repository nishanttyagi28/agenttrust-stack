"""Signing and tamper detection for evidence chains.

These are the tests that would have caught the hole in 0.1.0: before signing,
editing the amount or the manifest hash in the JSON still exited 0.
"""

from __future__ import annotations

import copy
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from agenttrust.ci import (
    EXIT_INTEGRITY,
    EXIT_OK,
    EXIT_POLICY,
    EXIT_WITNESS,
    check_evidence,
)
from agenttrust.evidence import (
    Chain,
    Decision,
    DecisionOutcome,
    EffectRef,
    EffectType,
    Event,
    Witness,
    demo_private_key,
    demo_public_key,
    demo_public_key_pem,
    is_envelope,
    key_id,
    load_public_key_pem,
    parse_chain,
    public_key_pem,
    sign_chain,
    signing_payload,
    verify_document,
    verify_text,
)


def _chain(amount_minor: int = 150_000) -> Chain:
    return Chain(
        schema_version="1.0",
        chain_id="sig-allow",
        event=Event(
            id="e",
            caused_by=None,
            actor_id="refund-agent",
            timestamp="2026-10-06T12:00:00Z",
            action_type="payment.transfer.propose",
            payload={"target": "Priya", "amount_minor": amount_minor},
        ),
        decision=Decision(
            id="d",
            caused_by="e",
            outcome=DecisionOutcome.allow,
            rule_id=None,
            policy_version="agenttrust-gate-1",
            reason="matches sealed payment",
        ),
        effect_ref=EffectRef(
            id="f",
            caused_by="d",
            manifest_hash="sha256:429740e1d1b21c77cd33b2ec143765553c2eccb1fa6fec1ed056b9f6d266cdd9",
            effect_type=EffectType.payment_transfer,
            adapter_id="payment.simulator",
            target_resource="payment:beneficiary/Priya",
        ),
        witness=Witness(
            id="w",
            caused_by="f",
            matched_expected=True,
            adapter_id="payment.simulator",
            detail="provider status: settled",
        ),
        eval_case=None,
    )


def _signed(chain: Chain | None = None) -> dict:
    return sign_chain(chain or _chain(), demo_private_key())


# --- happy path -------------------------------------------------------------


def test_signed_chain_round_trips_and_verifies() -> None:
    envelope = _signed()
    assert is_envelope(envelope)
    chain, result = verify_document(envelope, trusted_public_key=demo_public_key())
    assert result.ok, result.reason
    assert chain is not None
    assert chain.chain_id == "sig-allow"


def test_reformatting_the_file_does_not_break_the_signature() -> None:
    """Signing covers canonical JSON, so indentation and key order are free."""
    envelope = _signed()
    shuffled = json.dumps(envelope, indent=4, sort_keys=False)
    chain, result = verify_text(shuffled, trusted_public_key=demo_public_key())
    assert result.ok, result.reason
    assert chain is not None


def test_key_id_is_stable_and_matches_exported_pem() -> None:
    pem = demo_public_key_pem()
    reloaded = load_public_key_pem(pem)
    assert key_id(reloaded) == key_id(demo_public_key())
    assert public_key_pem(reloaded) == pem


def test_signature_payload_is_canonical_json() -> None:
    chain = _chain()
    payload = signing_payload(chain)
    assert payload == json.dumps(
        chain.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


# --- the forgeries that used to pass ---------------------------------------


@pytest.mark.parametrize(
    ("dotted", "value"),
    [
        ("chain.event.payload.amount_minor", 999_999),
        ("chain.effect_ref.manifest_hash", "sha256:" + "0" * 64),
        ("chain.witness.matched_expected", False),
        ("chain.effect_ref.target_resource", "payment:beneficiary/Ravi"),
    ],
)
def test_editing_a_signed_chain_is_caught(dotted: str, value: object) -> None:
    envelope = copy.deepcopy(_signed())
    cursor: dict = envelope
    keys = dotted.split(".")
    for key in keys[:-1]:
        cursor = cursor[key]
    cursor[keys[-1]] = value

    _, result = verify_document(envelope, trusted_public_key=demo_public_key())
    assert not result.ok
    assert "signature does not match" in result.reason


def test_tampered_amount_exits_4_through_the_ci_check() -> None:
    """This exited 0 in 0.1.0. It must not now."""
    envelope = copy.deepcopy(_signed())
    envelope["chain"]["event"]["payload"]["amount_minor"] = 999_999
    code = check_evidence(
        json.dumps(envelope),
        trusted_public_key=demo_public_key(),
    )
    assert code == EXIT_INTEGRITY


def test_untampered_signed_chain_exits_0_through_the_ci_check() -> None:
    code = check_evidence(json.dumps(_signed()), trusted_public_key=demo_public_key())
    assert code == EXIT_OK


# --- missing anchors, missing signatures, wrong keys -----------------------


def test_signature_without_a_trust_anchor_is_rejected() -> None:
    _, result = verify_document(_signed())
    assert not result.ok
    assert "no trust anchor" in result.reason


def test_a_different_key_is_rejected_even_with_a_valid_signature() -> None:
    other = Ed25519PrivateKey.generate()
    envelope = sign_chain(_chain(), other)
    _, result = verify_document(envelope, trusted_public_key=demo_public_key())
    assert not result.ok
    assert "does not match trusted key" in result.reason


def test_unsigned_chain_is_rejected_by_default() -> None:
    text = json.dumps(_chain().model_dump(mode="json"))
    assert check_evidence(text, trusted_public_key=demo_public_key()) == EXIT_INTEGRITY


def test_unsigned_chain_can_be_accepted_explicitly() -> None:
    text = json.dumps(_chain().model_dump(mode="json"))
    assert check_evidence(text, allow_unsigned=True) == EXIT_OK


def test_unknown_algorithm_is_rejected() -> None:
    envelope = copy.deepcopy(_signed())
    envelope["signature"]["alg"] = "hmac-sha256"
    _, result = verify_document(envelope, trusted_public_key=demo_public_key())
    assert not result.ok
    assert "alg" in result.reason


def test_garbage_base64_is_rejected() -> None:
    envelope = copy.deepcopy(_signed())
    envelope["signature"]["sig"] = "not base64!!"
    _, result = verify_document(envelope, trusted_public_key=demo_public_key())
    assert not result.ok


def test_non_json_text_is_rejected() -> None:
    _, result = verify_text("{not json", trusted_public_key=demo_public_key())
    assert not result.ok
    assert "not valid JSON" in result.reason


def test_structurally_invalid_chain_is_rejected_before_signing_checks() -> None:
    envelope = copy.deepcopy(_signed())
    del envelope["chain"]["witness"]  # allow requires a witness
    _, result = verify_document(envelope, trusted_public_key=demo_public_key())
    assert not result.ok
    assert "does not validate" in result.reason


# --- integrity outranks the other exit codes ------------------------------


def test_integrity_exit_code_wins_over_policy_and_witness() -> None:
    envelope = copy.deepcopy(_signed())
    envelope["chain"]["witness"]["matched_expected"] = False
    # Witness would be exit 2 on an unsigned chain; a forged signature is exit 4.
    assert (
        check_evidence(json.dumps(envelope), trusted_public_key=demo_public_key())
        == EXIT_INTEGRITY
    )
    assert check_evidence(
        json.dumps(_chain().model_dump(mode="json")), allow_unsigned=True
    ) == EXIT_OK


def test_deny_chain_still_exits_1_when_correctly_signed() -> None:
    chain = Chain(
        schema_version="1.0",
        chain_id="sig-deny",
        event=Event(
            id="e",
            caused_by=None,
            actor_id="refund-agent",
            timestamp="2026-10-06T12:00:00Z",
            action_type="payment.transfer.propose",
            payload={"target": "Priya", "amount_minor": 150100},
        ),
        decision=Decision(
            id="d",
            caused_by="e",
            outcome=DecisionOutcome.deny,
            rule_id="AT-PAY-001",
            policy_version="agenttrust-gate-1",
            reason="amount differs from the seal",
        ),
        effect_ref=None,
        witness=None,
        eval_case=None,
    )
    code = check_evidence(
        json.dumps(sign_chain(chain, demo_private_key())),
        trusted_public_key=demo_public_key(),
    )
    assert code == EXIT_POLICY


def test_false_witness_on_a_genuinely_signed_chain_exits_2() -> None:
    chain = _chain().model_copy(
        update={
            "witness": Witness(
                id="w",
                caused_by="f",
                matched_expected=False,
                adapter_id="payment.simulator",
                detail="mismatch",
            )
        }
    )
    code = check_evidence(
        json.dumps(sign_chain(chain, demo_private_key())),
        trusted_public_key=demo_public_key(),
    )
    assert code == EXIT_WITNESS


def test_parse_chain_still_accepts_a_bare_chain() -> None:
    chain = parse_chain(json.dumps(_chain().model_dump(mode="json")))
    assert chain.chain_id == "sig-allow"
