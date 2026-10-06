# Offline demo

Python 3.12. KarmaSakshi 0.2.0 requires `>=3.10,<3.14`.

Primary command, bash and PowerShell, from the repo root:

```bash
python -m pip install -e ".[dev,karmasakshi]"
python apps/demo/run_demo.py
```

On 2026-10-07 `pip install -e ".[dev,karmasakshi]"` fails before the script runs. setuptools reports `package directory 'packages\ci\agenttrust\evidence' does not exist`. Until that discovery bug is fixed, a local run still needs the package roots on `PYTHONPATH`:

```powershell
$env:PYTHONPATH = "packages/evidence;packages/importers;packages/gate;packages/ci"
python apps/demo/run_demo.py
```

```bash
PYTHONPATH=packages/evidence:packages/importers:packages/gate:packages/ci python apps/demo/run_demo.py
```

## Fresh local stdout (2026-10-07)

Same lines `apps/demo/run_demo.py` prints. Captured in one process with the green-path excerpt in the README, so the hash matches that excerpt.

```text
red_exit=1
green_exit=0
regression_exit=3
held_exit=0
rule_id=AT-PAY-001
witness_matched=True
adapter_id=payment.simulator
target_resource=payment:beneficiary/Priya
manifest_hash=sha256:264730d09ab2a10978af0b9b95249efeefd3693b32271be71d7d4fc0bcd6cd27
```

| Check | Result |
|---|---|
| Proposed ₹1501 (150100 minor units) to Priya | `red_exit=1`, rule `AT-PAY-001`, no effect, no witness |
| Sealed ₹1500 (150000) to Priya | `green_exit=0`, `witness_matched=True` |
| Adapter | `payment.simulator` |
| Target | `payment:beneficiary/Priya` |
| Replay `settled 150100` against approved golden `blocked` | `regression_exit=3` |
| Replay containing `blocked` | `held_exit=0` |

## Earlier run (2026-10-06)

Impact numbers in the README table are from that date: pytest **43 passed**, and manifest hash `sha256:7c7d7bf38d6ffe3aeabab396a392b27bad6150fbe28765a044809e77f3cdd449`. Exit codes matched the 2026-10-07 run. The hash did not. KarmaSakshi `prepare` draws a nonce.

Regression exit 3 is a local check that the golden YAML `ground_truth` appears in the replay text. It is the offline stand-in for `agenteval compare` for the one YAML shape this repo emits. AgentEval itself was not executed.

Actions run that is green today, tests only: https://github.com/nishanttyagi28/agenttrust-stack/actions/runs/37510342515
