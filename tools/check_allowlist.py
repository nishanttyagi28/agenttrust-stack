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
    "governance": (
        "GOVERNANCE.md",
        "AGENTS.md",
        "POSTMORTEMS/**",
        ".githooks/**",
        "tools/check_allowlist.py",
        "scripts/install_hooks.py",
        "docs/adr/0009-agent-lane-governance.md",
        "README.md",
        "docs/progress.md",
        "tests/governance/**",
    ),
}


# Sprint roles (p0..p4) are time-boxed slices, not actors. They intentionally
# span packages, so they are excluded from --any-lane matching; otherwise a
# single sprint role would cover every lane and the guard would always pass.
NON_ACTOR_ROLES = frozenset({"p0", "p1", "p2", "p3", "p4"})

ACTOR_ROLES = tuple(name for name in AGENTS if name not in NON_ACTOR_ROLES)


def changed_files(staged: bool = False, against: str | None = None) -> list[str]:
    """Paths to check: the working tree by default, or a specific diff."""
    if staged:
        cmd = ["git", "diff", "--cached", "--name-only", "-z"]
    elif against is not None:
        cmd = ["git", "diff", "--name-only", "-z", f"{against}...HEAD"]
    else:
        cmd = ["git", "status", "--porcelain", "-u", "-z"]
    result = subprocess.run(cmd, check=True, capture_output=True)
    raw = result.stdout.decode("utf-8", "replace")
    entries = [part for part in raw.split("\0") if part]
    files: list[str] = []
    for entry in entries:
        if cmd[1] == "status":
            entry = entry[3:]
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        path = entry.strip().strip('"').replace("\\", "/")
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=sorted(AGENTS), default=None)
    parser.add_argument(
        "--staged",
        action="store_true",
        help="check staged changes (used by the pre-commit hook)",
    )
    parser.add_argument(
        "--against",
        default=None,
        metavar="REF",
        help="check the diff against REF instead of the working tree",
    )
    parser.add_argument(
        "--any-lane",
        action="store_true",
        help="pass if any single role covers the whole diff (still rejects a diff that spans lanes)",
    )
    args = parser.parse_args()
    if args.agent is None and not args.any_lane:
        parser.error("pass --agent <role> or --any-lane")
    root = Path.cwd()
    if not (root / ".git").exists():
        print("not a git checkout", file=sys.stderr)
        return 2

    files = changed_files(staged=args.staged, against=args.against)
    if not files:
        print("allowlist ok: no changed paths")
        return 0

    if args.any_lane:
        fits = [name for name in ACTOR_ROLES if all(allowed(f, AGENTS[name]) for f in files)]
        if fits:
            print(f"allowlist ok: diff fits role(s) {', '.join(sorted(fits))} ({len(files)} paths)")
            return 0
        orphans = [
            f for f in files if not any(allowed(f, AGENTS[name]) for name in ACTOR_ROLES)
        ]
        if orphans:
            print("allowlist reject: paths outside every actor role", file=sys.stderr)
        else:
            print(
                "allowlist reject: the diff spans actor lanes, so no single agent "
                "owns it -> an orchestrator change needs a human",
                file=sys.stderr,
            )
        for path in files:
            owners = [n for n in ACTOR_ROLES if allowed(path, AGENTS[n])]
            sprint = [n for n in NON_ACTOR_ROLES if allowed(path, AGENTS[n])]
            tag = ", ".join(sorted(owners)) or "unowned"
            if sprint:
                tag += f" (sprint: {', '.join(sorted(sprint))})"
            print(f"  {path}  [{tag}]", file=sys.stderr)
        return 1

    patterns = AGENTS[args.agent]
    bad = [path for path in files if not allowed(path, patterns)]
    if bad:
        print(f"allowlist reject for {args.agent}:")
        for path in bad:
            print(f"  {path}")
        return 1
    print(f"allowlist ok for {args.agent} ({len(files)} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
