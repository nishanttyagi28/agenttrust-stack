# AgentTrust Stack

Records one consequential agent action (a payment, an email, a delete, a deploy) as a single JSON document: the policy decision, the sealed approval, the observed outcome, and the regression test it turns into. A CI check fails if any of those is missing or wrong.

[![agenttrust](https://github.com/nishanttyagi28/agenttrust-stack/actions/workflows/agenttrust.yml/badge.svg)](https://github.com/nishanttyagi28/agenttrust-stack/actions/workflows/agenttrust.yml)
[![PyPI](https://img.shields.io/pypi/v/nishanttyagi-agenttrust.svg)](https://pypi.org/project/nishanttyagi-agenttrust/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Teams that let agents move money or send mail tend to end up with three separate pieces of evidence: an eval suite that scores behaviour, an approval record for the effect, and a policy hook log. None of them alone answers "did this exact action happen as approved, and will the same failure fail the next build?"

This repo is a thin layer that joins them. It imports evidence from three of my other projects and doesn't fork or reimplement them:

- [AgentEval](https://github.com/nishanttyagi28/agenteval): eval traces and baseline comparison
- [KarmaSakshi](https://github.com/nishanttyagi28/karmasakshi-protocol): sealing the exact effect and checking the real outcome
- [CodeGovernor](https://github.com/nishanttyagi28/codegovernor): policy events from coding-agent hooks

## Install

Python 3.10 or newer. The KarmaSakshi extra needs Python below 3.14.

```bash
pip install "nishanttyagi-agenttrust[karmasakshi]"
```

The PyPI name is `nishanttyagi-agenttrust`. The import name is `agenttrust`. AgentEval is a required dependency. Without the `karmasakshi` extra you get the schema, gate and CI check, but no real seal or outcome check.

From source:

```bash
git clone https://github.com/nishanttyagi28/agenttrust-stack.git
cd agenttrust-stack
pip install -e ".[dev,karmasakshi]"
```

## Quick start

```bash
python -m agenttrust.demo
python -m agenttrust.report evidence-pack/chain.json evidence-pack/report.html
python -m agenttrust.ci evidence-pack/chain.json
```

The demo runs offline against KarmaSakshi's payment and email simulators. Finance approved ₹1,500 to Priya:

- The agent proposes ₹1,501. The gate denies it with rule `AT-PAY-001`, nothing is committed, and the CI check exits 1.
- The agent proposes exactly ₹1,500. KarmaSakshi seals, commits and verifies it, and the check exits 0.
- An approved failure is replayed later. If the replay no longer matches the approved ground truth, the check exits 3.
- The same is shown for an email to the wrong recipient (`AT-MAIL-001`), and for delete and deploy targets that aren't on the allowlist.

The demo writes `evidence-pack/chain.json`, and `agenttrust.report` turns it into one HTML page. With a pip install, the same commands are available as `agenttrust-demo` and `agenttrust-report`.

## How it works

Each action produces a chain with four parts:

1. **Policy.** The decision is `allow`, `deny` or `unknown`. Missing policy evidence counts as `unknown`, and `unknown` fails.
2. **Seal.** On allow, the chain points at the KarmaSakshi manifest hash, adapter and target. On deny there is no effect.
3. **Witness.** After the effect runs, the observed outcome must match what was sealed.
4. **Regression.** A failure becomes a pending eval case. It is written to AgentEval golden YAML only after a person approves it.

`python -m agenttrust.ci` exit codes:

| Exit | Meaning |
| --- | --- |
| 0 | Allowed, outcome matched, and any golden replay still holds |
| 1 | Decision was `deny` or `unknown` |
| 2 | Allowed, but the outcome is missing or doesn't match |
| 3 | Replay regressed against the approved golden case (AgentEval's `compare_runs`) |

Rule IDs are defined in code: `AT-PAY-001` (amount differs from the seal), `AT-PAY-002` (wrong payee), `AT-MAIL-001`, `AT-DEL-001` and `AT-DEP-001` (target not on the sealed allowlist). CodeGovernor rule IDs are imported unchanged.

Approving a case is always explicit. `python -m agenttrust.importers chain.json --out golden.yaml` writes nothing unless you pass `--approve --actor <id> --note <text>` or an approval file containing `"approve": true`.

| Path | Import | Role |
| --- | --- | --- |
| `packages/evidence/` | `agenttrust.evidence` | Chain schema, canonical JSON |
| `packages/importers/` | `agenttrust.importers` | Read AgentEval, KarmaSakshi and CodeGovernor output; export approved cases |
| `packages/gate/` | `agenttrust.gate` | Compare a proposal to the sealed intent; attach the seal and outcome |
| `packages/ci/` | `agenttrust.ci` | The exit-code check |
| `apps/demo/`, `apps/report/` | `agenttrust.demo`, `agenttrust.report` | Offline demo and HTML report |
| `apps/ui/` | (script) | Small local page that runs the demo: `python apps/ui/server.py`, then open http://127.0.0.1:8765/ |

More detail: [docs/architecture.md](docs/architecture.md), [docs/demo.md](docs/demo.md), and the decision records in [docs/adr/](docs/adr/). To add the check to your own CI job, see [docs/adopt.md](docs/adopt.md) and [examples/ci-drop-in/agenttrust.yml](examples/ci-drop-in/agenttrust.yml).

## Limitations

- Alpha (0.1.0). It has only been run offline against simulators, not real payment or mail providers.
- Only payments (`payment.simulator`) and email (`email.sandbox`) are actually sealed and checked. Delete and deploy are deny rules only, because KarmaSakshi has no adapter for those effect types yet ([ADR 0006](docs/adr/0006-multi-action-seals.md)).
- Manifest hashes change on every run because KarmaSakshi adds a nonce, so tests don't pin them.
- If AgentEval can't be imported, exit 3 falls back to a plain text check and says so on stderr.
- There is no approval UI or hosted service. Approval happens through the CLI flag or a file.

Progress notes: [docs/progress.md](docs/progress.md).

## Development

```bash
pip install -e ".[dev,karmasakshi]"
python -m pytest -q
```

CI runs the tests, the demo and the report on every push, and uploads `evidence-pack/` as a build artifact.

## License

MIT. See [LICENSE](LICENSE).
