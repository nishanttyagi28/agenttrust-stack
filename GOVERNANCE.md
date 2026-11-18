# How this repo is built: agents on a leash

Parts of this code were written by AI coding agents. That is stated plainly in
the README because pretending otherwise is a lie that collapses at the first
code review.

What matters is not that agents wrote code. It is **what they were allowed to
touch, what they were forbidden to do, and who signed off.** This file is the
mechanism, not a policy statement. Every claim below points at a file you can
run.

## 1. Every agent has a lane

`tools/check_allowlist.py` maps a role to the only paths that role may write:

| Role | May write |
| --- | --- |
| `architect` | `docs/architecture.md`, `docs/adr/0001–0003`, `docs/progress.md`, `README.md` |
| `evidence` | `packages/evidence/**`, `tests/evidence/**`, `pyproject.toml` |
| `importers` | `packages/importers/**`, `tests/importers/**`, `tests/fixtures/**` |
| `gate` | `packages/gate/**`, `packages/ci/**`, `.github/workflows/agenttrust.yml`, `tests/gate/**`, `tests/ci/**` |
| `demo` | `apps/demo/**`, `apps/report/**`, `docs/demo.md`, `tests/demo/**` |
| `p0`–`p4` | the files for that slice only (**time-boxes, not actors** — excluded from lane matching) |
| `governance` | `GOVERNANCE.md`, `AGENTS.md`, `POSTMORTEMS/**`, `.githooks/**`, `tools/check_allowlist.py`, `scripts/install_hooks.py`, `README.md` |

The evidence agent cannot edit the CI check. The gate agent cannot edit the
schema. That separation is the point: an agent that can write both the thing
and its own test has not been verified, it has been trusted.

The `p0`–`p4` roles are sprint slices and they deliberately span packages. They
are excluded from lane matching, because if a sprint role counted as an actor it
would cover every lane and the guard would always pass. `tests/governance/`
asserts this, so the claim cannot quietly rot.

## 2. The rule is enforced, not documented

A markdown rule does not block a write. `.githooks/pre-commit` does:

```sh
exec python tools/check_allowlist.py --staged --any-lane
```

Enable it once per clone:

```bash
python scripts/install_hooks.py
```

From then on, a staged diff that fits no single role is rejected before the
commit exists. A diff that fits `evidence` is accepted as evidence work. A diff
that touches `packages/evidence/**` **and** `packages/ci/**` fails, because no
agent owns both — that is by construction an orchestrator change.

## 3. A human can always override — visibly

```bash
AGENTTRUST_SCOPE_OVERRIDE=1 git commit -m "..."
```

The hook prints `scope guard: OVERRIDDEN by human` and lets it through. That
line is the whole governance model in one sentence: **the machine cannot widen
its own permissions, and a human who does must say so out loud.**

Silent widening is the failure mode this is designed to prevent. An override
that announces itself is not a loophole; it is an audit record.

## 4. Decisions are not the agent's to make

`docs/adr/` holds the irreversible calls: what the schema means, what is out of
scope, what "thin umbrella" excludes. `AGENTS.md` states the constraint
directly — *"Phase 0 decisions are locked. Do not reopen them."*

An agent can propose a shape inside an approved ADR. It cannot quietly replace
the architecture to make its own task easier. The evidence for that is
[ADR 0001](docs/adr/0001-thin-umbrella.md) rejecting the obvious-but-wrong
design of absorbing the sibling projects.

## 5. When the guard fails, the failure gets written down

`POSTMORTEMS/` records what broke, how it was found, and what changed. It is a
record of friction, which is the one artifact generated code cannot produce.
See [0001](POSTMORTEMS/0001-unsigned-evidence-chain.md), where 0.1.0 claimed
tamper evidence it did not have.

## What this does not do

Be honest about the edges:

- The allowlist constrains **paths**, not **quality**. An agent inside its lane
  can still write bad code. That is what tests and review are for.
- `core.hooksPath` is local configuration. It can be unset, and a fresh clone
  has no hook until `install_hooks.py` runs. CI is the backstop that cannot be
  unset locally.
- The lane boundaries themselves are a human judgment call, recorded in
  `AGENTS.md`. Nothing verifies that `gate` *should* own `packages/ci/**`.
- This is one repo's process, at one scale. It is not a framework.

The same pattern, with a stricter hook that also blocks an agent from running
`git commit`, `push`, `reset`, `checkout`, `rebase`, `clean` and `stash` at all,
lives in [`aravali-ap-desk/.cursor/hooks/scope_guard.py`](https://github.com/nishanttyagi28/aravali-ap-desk/blob/main/.cursor/hooks/scope_guard.py).
