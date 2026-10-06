# Offline demo

Run on Python 3.12 (KarmaSakshi 0.2.0 does not install on 3.14):

```text
$env:PYTHONPATH = "packages/evidence;packages/importers;packages/gate;packages/ci"
python3.12 apps/demo/run_demo.py
```

Observed 2026-10-06:

| Check | Result |
|---|---|
| Proposed ₹1501 (150100 minor units) to Priya | `red_exit=1`, rule `AT-PAY-001`, no effect, no witness |
| Sealed ₹1500 (150000) to Priya | `green_exit=0`, `witness_matched=True` |
| Adapter | `payment.simulator` |
| Target | `payment:beneficiary/Priya` |
| Replay `settled 150100` against approved golden `blocked` | `regression_exit=3` |
| Replay containing `blocked` | `held_exit=0` |

The manifest hash on that run was `sha256:7c7d7bf38d6ffe3aeabab396a392b27bad6150fbe28765a044809e77f3cdd449`. KarmaSakshi `prepare` draws a nonce, so a later run gets a different hash. The demo asserts a non-empty hash and `matched_expected=True`.

Regression exit 3 is a local check that the golden YAML `ground_truth` appears in the replay text. It is the offline stand-in for `agenteval compare` for the one YAML shape this repo emits. AgentEval itself was not executed.
