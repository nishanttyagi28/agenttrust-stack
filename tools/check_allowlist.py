"""Reject a diff that touches paths outside one agent's allowlist.

Stdlib only. The orchestrator runs this after every specialized agent.
"""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

AGENTS: dict[str, tuple[str, ...]] = {
    "architect": (
        "docs/architecture.md",
        "docs/adr/0001-thin-umbrella.md",
        "docs/adr/0002-evidence-schema.md",
        "docs/adr/0003-importers-not-forks.md",
        "docs/progress.md",
        "README.md",
    ),
    "evidence": (
        "packages/evidence/**",
        "tests/evidence/**",
        "pyproject.toml",
    ),
    "importers": (
        "packages/importers/**",
        "tests/importers/**",
        "tests/fixtures/**",
    ),
    "gate": (
        "packages/gate/**",
        "packages/ci/**",
        ".github/workflows/agenttrust.yml",
        "tests/gate/**",
        "tests/ci/**",
    ),
    "demo": (
        "apps/demo/**",
        "apps/report/**",
        "docs/demo.md",
        "README.md",
        "tests/demo/**",
    ),
    "p0": (
        "README.md",
        "docs/demo.md",
        "docs/progress.md",
    ),
    "p1": (
        "pyproject.toml",
        "packages/evidence/**",
        "packages/importers/**",
        "packages/gate/**",
        "packages/ci/**",
        "apps/demo/**",
        "apps/report/**",
        ".github/workflows/agenttrust.yml",
        "tests/**",
        "docs/adr/0004-install-and-evidence-artifact.md",
        "docs/progress.md",
        "README.md",
    ),
    "p2": (
        "pyproject.toml",
        "packages/ci/**",
        "packages/importers/**",
        "tests/ci/**",
        "tests/fixtures/**",
        "docs/adr/0005-agenteval-pin.md",
        "docs/progress.md",
        "README.md",
    ),
    "p3": (
        "packages/gate/**",
        "tests/gate/**",
        "apps/demo/**",
        "docs/demo.md",
        "docs/progress.md",
        "docs/adr/0006-multi-action-seals.md",
    ),
    "p4": (
        "docs/adopt.md",
        "examples/ci-drop-in/**",
        "README.md",
        "docs/progress.md",
    ),
}


def changed_files() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "-u"],
        check=True,
        capture_output=True,
        text=True,
    )
    files: list[str] = []
    for line in result.stdout.splitlines():
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip('"').replace("\\", "/")
        if path:
            files.append(path)
    return files


def allowed(path: str, patterns: tuple[str, ...]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern) or path == pattern:
            return True
        if pattern.endswith("/**") and (
            path.startswith(pattern[:-3] + "/") or path == pattern[:-3]
        ):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True, choices=sorted(AGENTS))
    args = parser.parse_args()
    patterns = AGENTS[args.agent]
    root = Path.cwd()
    if not (root / ".git").exists():
        print("not a git checkout", file=sys.stderr)
        return 2
    bad = [path for path in changed_files() if not allowed(path, patterns)]
    if bad:
        print(f"allowlist reject for {args.agent}:")
        for path in bad:
            print(f"  {path}")
        return 1
    print(f"allowlist ok for {args.agent} ({len(changed_files())} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
