"""Ed25519 signing for evidence chains.

A bare chain is a self-report. Anyone who can write the JSON can change
``event.payload.amount_minor``, point ``effect_ref.manifest_hash`` at zeros, or
flip ``witness.matched_expected``, and the CI check still exits 0 because it
reads those fields as facts.

Signing closes that: the signature covers the canonical JSON of the whole
chain, so any edit invalidates it. Verification is separate from the trust
anchor, so a signed file also needs a public key you already trust. Without an
anchor a signature only proves the file is self-consistent, not that it came
from the gate.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from pydantic import ValidationError

from agenttrust.evidence.codec import canonical_json, parse_chain
from agenttrust.evidence.models import Chain

ALG = "ed25519"

# Published seed for the demo key only. Reproducible on purpose: anyone who
# clones the repo can regenerate the same keypair and verify the checked-in
# demo pack. This is not a trust anchor for real deployments.
DEMO_SEED = b"agenttrust-demo-seed-v1"

ENVELOPE_CHAIN = "chain"
ENVELOPE_SIGNATURE = "signature"


class IntegrityError(Exception):
    """The chain could not be verified as unmodified and signed."""


@dataclass(frozen=True)
class VerifyResult:
    """Outcome of verifying one evidence document."""

    ok: bool
    reason: str
    signed: bool

    def __bool__(self) -> bool:
        return self.ok


def _raw_public_bytes(key: Ed25519PublicKey) -> bytes:
    return key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def key_id(key: Ed25519PublicKey) -> str:
    """Stable short identifier for a public key."""
    return hashlib.sha256(_raw_public_bytes(key)).hexdigest()[:16]


def demo_private_key() -> Ed25519PrivateKey:
    """Deterministic demo key. Never use this to sign anything real."""
    return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(DEMO_SEED).digest())


def demo_public_key() -> Ed25519PublicKey:
    return demo_private_key().public_key()


def public_key_pem(key: Ed25519PublicKey) -> str:
    return key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")


def demo_public_key_pem() -> str:
    return public_key_pem(demo_public_key())


def load_public_key_pem(text: str) -> Ed25519PublicKey:
    """Parse a PEM public key, rejecting any other key type."""
    try:
        key = serialization.load_pem_public_key(text.encode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - any parse failure is an integrity failure
        raise IntegrityError(f"public key is not readable PEM: {exc}") from exc
    if not isinstance(key, Ed25519PublicKey):
        raise IntegrityError(f"public key is {type(key).__name__}, expected Ed25519")
    return key


def signing_payload(chain: Chain) -> bytes:
    """Bytes that get signed: canonical JSON, independent of file formatting."""
    return canonical_json(chain).encode("utf-8")


def sign_chain(chain: Chain, private_key: Ed25519PrivateKey) -> dict[str, Any]:
    """Return a signed envelope for *chain*."""
    signature = private_key.sign(signing_payload(chain))
    return {
        ENVELOPE_CHAIN: chain.model_dump(mode="json"),
        ENVELOPE_SIGNATURE: {
            "alg": ALG,
            "key_id": key_id(private_key.public_key()),
            "sig": base64.b64encode(signature).decode("ascii"),
        },
    }


def sign_chain_text(chain: Chain, private_key: Ed25519PrivateKey) -> str:
    """Canonical JSON text of a signed envelope, newline terminated."""
    return json.dumps(sign_chain(chain, private_key), sort_keys=True) + "\n"


def is_envelope(document: Any) -> bool:
    return (
        isinstance(document, dict)
        and isinstance(document.get(ENVELOPE_SIGNATURE), dict)
        and isinstance(document.get(ENVELOPE_CHAIN), dict)
    )


def _decode_signature(meta: dict[str, Any]) -> bytes:
    if meta.get("alg") != ALG:
        raise IntegrityError(f"signature alg must be {ALG!r}, got {meta.get('alg')!r}")
    raw = meta.get("sig")
    if not isinstance(raw, str):
        raise IntegrityError("signature sig must be a base64 string")
    try:
        return base64.b64decode(raw, validate=True)
    except Exception as exc:  # noqa: BLE001
        raise IntegrityError(f"signature sig is not valid base64: {exc}") from exc


def verify_document(
    document: Any,
    *,
    trusted_public_key: Ed25519PublicKey | None = None,
    allow_unsigned: bool = False,
) -> tuple[Chain | None, VerifyResult]:
    """Validate and verify one evidence document.

    Returns the parsed chain plus a result. Raises nothing: an unusable
    document yields ``ok=False`` with a reason.
    """
    if is_envelope(document):
        meta = document[ENVELOPE_SIGNATURE]
        try:
            chain = parse_chain(json.dumps(document[ENVELOPE_CHAIN]))
        except ValidationError as exc:
            return _fail(f"chain does not validate: {exc.error_count()} error(s)")

        if trusted_public_key is None:
            return _fail(
                "signed chain, but no trust anchor supplied "
                "(a signature alone only proves self-consistency)"
            )

        try:
            signature = _decode_signature(meta)
        except IntegrityError as exc:
            return _fail(str(exc))

        if meta.get("key_id") != key_id(trusted_public_key):
            return _fail(
                f"signature key_id {meta.get('key_id')!r} does not match "
                f"trusted key {key_id(trusted_public_key)!r}"
            )

        try:
            trusted_public_key.verify(signature, signing_payload(chain))
        except InvalidSignature:
            return _fail("signature does not match the chain contents (chain was edited)")
        return chain, VerifyResult(True, "signature verified", signed=True)

    try:
        chain = parse_chain(json.dumps(document))
    except ValidationError as exc:
        return _fail(f"chain does not validate: {exc.error_count()} error(s)")

    if allow_unsigned:
        return chain, VerifyResult(True, "unsigned chain accepted by request", signed=False)
    return _fail("unsigned chain: no signature, so edits cannot be detected")


def verify_text(
    text: str,
    *,
    trusted_public_key: Ed25519PublicKey | None = None,
    allow_unsigned: bool = False,
) -> tuple[Chain | None, VerifyResult]:
    """Parse JSON text, then verify it."""
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, VerifyResult(False, f"not valid JSON: {exc}", signed=False)
    chain, result = verify_document(
        document,
        trusted_public_key=trusted_public_key,
        allow_unsigned=allow_unsigned,
    )
    return (chain if result.ok else None), result


def _fail(reason: str) -> tuple[None, VerifyResult]:
    # The chain is unavailable when verification fails; callers must not use it.
    return None, VerifyResult(False, reason, signed=False)
