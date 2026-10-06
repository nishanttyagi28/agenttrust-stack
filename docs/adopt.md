# Add AgentTrust to an agent CI job

One pull request. No new service. The job installs this repo, runs the tests, runs the offline demo, renders the evidence page, and uploads `evidence-pack/`. A non-zero demo or pytest exit fails the job.

Exits from `python -m agenttrust.ci`:

| Exit | Meaning |
|---|---|
| 0 | Policy allow, witness matched, and any supplied golden replay still holds |
| 1 | `decision.outcome` is `deny` or `unknown` |
| 2 | Allow path with a missing witness or `matched_expected` not true |
| 3 | `compare_runs` says the replay regressed against the approved golden |

Copy [examples/ci-drop-in/agenttrust.yml](../examples/ci-drop-in/agenttrust.yml) into `.github/workflows/`. It is the workflow this repository runs on `main`.

Requires Python 3.12. `karmasakshi-protocol` 0.2.0 does not install on 3.14. The PyPI distribution is `nishanttyagi-agenttrust` (`pip install nishanttyagi-agenttrust`). PyPI rejected `agenttrust-stack` as too similar. Imports stay `agenttrust`. The dependency `nishanttyagi-agenteval>=0.5.0,<0.6` is what exit 3 imports as `compare_runs`. A clone of this repo still uses the editable install below.

```bash
python -m pip install -e ".[dev,karmasakshi]"
python -m pytest -q
python -m agenttrust.demo
python -m agenttrust.report evidence-pack/chain.json evidence-pack/report.html
```

`python -m agenttrust.demo` exits 0 only when the payment and email allow paths witness, the payment deny is exit 1, and the delete and deploy denies are exit 1. Delete and deploy are not sealed. [ADR 0006](adr/0006-multi-action-seals.md).

The uploaded files are `evidence-pack/chain.json` (payment allow chain) and `evidence-pack/report.html`. The job fails if either file is missing or empty.

Checked-in proof from before this page: Actions run https://github.com/nishanttyagi28/agenttrust-stack/actions/runs/37513293615 and artifact https://github.com/nishanttyagi28/agenttrust-stack/actions/runs/37513293615/artifacts/11436485460.
