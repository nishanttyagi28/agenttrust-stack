# ADR 0009: Agents have write lanes, enforced by a hook

**Status:** Accepted. `.githooks/pre-commit` runs `tools/check_allowlist.py --staged --any-lane`. Human override is explicit.
**Date:** 2026-11-19

## Context

Most of this repo was written with AI coding agents (stated in the README). The
first version of `tools/check_allowlist.py` defined a lane per agent and could
check the working tree, but nothing ever ran it. A rule that nothing executes is
documentation, not a control — and a reviewer is right to read it that way.

The failure that motivated this is recorded in
[POSTMORTEMS/0001](../POSTMORTEMS/0001-unsigned-evidence-chain.md): the CI check
trusted the same file it was judging. Nothing in the process made that
impossible, so nothing caught it for 44 days.

## Decision

**A staged diff must fit inside at least one agent's lane, and the check runs
before the commit exists.**

- `tools/check_allowlist.py --staged --any-lane` reads `git diff --cached` and
  passes only if a single role's patterns cover every staged path.
- A diff touching `packages/evidence/**` **and** `packages/ci/**` fits no single
  role, so it is rejected. That is correct: it is an orchestrator change.
- `.githooks/pre-commit` calls it. `python scripts/install_hooks.py` enables it
  with `core.hooksPath`, which is a per-clone setting and touches nothing global.
- `AGENTTRUST_SCOPE_OVERRIDE=1` skips the check **and prints that it did**. A
  human can widen the machine's permissions; the machine cannot widen its own,
  and the widening is never silent.

## Why a lane per agent, rather than tests alone

A test written by the same agent that wrote the code is not verification, it is
agreement. The lane is what makes the test worth something: the `evidence` agent
owns the schema and its tests and cannot reach into `packages/ci/`, so the CI
check is a consumer of a contract it did not get to rewrite.

The concrete instance that proves this is worth the friction: the bug in
postmortem 0001 lived in `packages/ci/`, and the fix touched `packages/evidence/`
as well. No single agent could have made that change. A human had to, and did.

## Alternatives considered

- **Document the rule in `AGENTS.md` only.** Rejected. It was already documented
  and it was ignored, by me.
- **Enforce in CI instead of a hook.** Necessary as a backstop but insufficient
  as the primary control: CI rejects the branch after the work is done, which
  invites a follow-up "fix the lint" commit that undoes the lesson. The hook
  stops the wrong shape from becoming a commit at all.
- **Fail CI on any cross-lane diff.** Rejected. Real work is sometimes genuinely
  cross-cutting; that is what the orchestrator role is, and making it impossible
  would produce a queue of override commits, which is the same as no control.
- **Block agents from running `git` at all** (the pattern in
  `aravali-ap-desk/.cursor/hooks/scope_guard.py`). Stronger, but it is a Cursor
  hook and belongs to that repo's tooling, not this one. Porting it here is a
  reasonable follow-up, not this decision.

## Consequences

- A clone without `install_hooks.py` has no guard. `GOVERNANCE.md` says so
  plainly rather than implying coverage it does not have.
- Cross-lane changes now require a visible override, so the count of overrides
  is a usable signal of how often the process is being bypassed.
- The lanes constrain **paths**, not quality. An agent inside its lane can still
  write bad code; tests and review remain the only defence against that.
- The lane map itself is a human judgment recorded in `AGENTS.md`. Nothing
  verifies that `gate` *should* own `packages/ci/**`.
