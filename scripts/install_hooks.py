"""Enable the pre-commit scope guard in this clone.

    python scripts/install_hooks.py

Sets core.hooksPath to .githooks so .githooks/pre-commit runs before every
commit. Nothing global is touched, and the setting can be removed with:

    git config --unset core.hooksPath

Stdlib only.
"""

from __future__ import annotations

import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".githooks"
HOOK = HOOKS / "pre-commit"


def main() -> int:
    if not (ROOT / ".git").exists():
        print("not a git checkout; nothing to install", file=sys.stderr)
        return 2
    if not HOOK.exists():
        print(f"missing {HOOK}", file=sys.stderr)
        return 2

    mode = HOOK.stat().st_mode
    HOOK.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    subprocess.run(
        ["git", "config", "core.hooksPath", ".githooks"], cwd=ROOT, check=True
    )
    print(f"scope guard enabled: core.hooksPath -> .githooks")
    print(f"hook: {HOOK.relative_to(ROOT)}")
    print("a diff that fits no single agent lane will be rejected before it commits")
    print("human override: AGENTTRUST_SCOPE_OVERRIDE=1 git commit ...")

    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True
    )
    if dirty.stdout.strip():
        print()
        print("note: the working tree has changes; stage them and run")
        print("      python tools/check_allowlist.py --staged --any-lane")
        print("      to preview what the hook will decide.")

    shell = shutil.which("sh")
    if shell is None:
        print()
        print(
            "warning: no `sh` on PATH. Git for Windows ships one and git uses it "
            "for hooks, so this is usually fine, but verify with a test commit.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
