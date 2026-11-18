"""CLI: python -m agenttrust.ci chain.json [--golden cases.yaml --replay text].

Verification is secure by default: a bare (unsigned) chain exits 4, and a
signed chain needs a trust anchor via --public-key or --demo-key. Pass
--allow-unsigned to keep the pre-signing behaviour.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from agenttrust.ci.check import EXIT_INTEGRITY, check_evidence_result
from agenttrust.evidence import IntegrityError, demo_public_key, load_public_key_pem


def _trust_anchor(args: argparse.Namespace) -> Ed25519PublicKey | None:
    if args.public_key is not None:
        return load_public_key_pem(args.public_key.read_text(encoding="utf-8"))
    if args.demo_key:
        return demo_public_key()
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AgentTrust CI check")
    parser.add_argument("chain", type=Path)
    parser.add_argument("--golden", type=Path, default=None)
    parser.add_argument("--replay", type=str, default=None)
    parser.add_argument(
        "--public-key",
        type=Path,
        default=None,
        help="PEM Ed25519 public key to verify the signature against",
    )
    parser.add_argument(
        "--demo-key",
        action="store_true",
        help="verify against the published demo key (see agenttrust.evidence.signing)",
    )
    parser.add_argument(
        "--allow-unsigned",
        action="store_true",
        help="accept a chain with no signature (edits cannot be detected)",
    )
    args = parser.parse_args(argv)

    try:
        anchor = _trust_anchor(args)
    except IntegrityError as exc:
        print(f"exit={EXIT_INTEGRITY}", file=sys.stdout)
        print(f"integrity: {exc}", file=sys.stderr)
        return EXIT_INTEGRITY

    golden = args.golden.read_text(encoding="utf-8") if args.golden else None
    result = check_evidence_result(
        args.chain.read_text(encoding="utf-8"),
        golden_yaml=golden,
        replay_output=args.replay,
        trusted_public_key=anchor,
        allow_unsigned=args.allow_unsigned,
    )
    print(f"exit={result.code}")
    if result.reason is not None:
        print(f"integrity: {result.reason}", file=sys.stderr)
    return result.code


if __name__ == "__main__":
    sys.exit(main())
