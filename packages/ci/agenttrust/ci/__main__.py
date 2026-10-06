"""CLI: python -m agenttrust.ci chain.json [--golden cases.yaml --replay text]."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agenttrust.evidence import parse_chain

from agenttrust.ci.check import check_chain


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AgentTrust CI check")
    parser.add_argument("chain", type=Path)
    parser.add_argument("--golden", type=Path, default=None)
    parser.add_argument("--replay", type=str, default=None)
    args = parser.parse_args(argv)
    chain = parse_chain(args.chain.read_text(encoding="utf-8"))
    golden = args.golden.read_text(encoding="utf-8") if args.golden else None
    code = check_chain(chain, golden_yaml=golden, replay_output=args.replay)
    print(f"exit={code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
