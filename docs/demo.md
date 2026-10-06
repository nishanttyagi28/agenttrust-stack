# Offline demo

Python 3.12. KarmaSakshi 0.2.0 requires `>=3.10,<3.14`.

From a clone:

```bash
python -m pip install -e ".[dev,karmasakshi]"
python -m agenttrust.demo
python -m agenttrust.report evidence-pack/chain.json evidence-pack/report.html
```

The same two commands work in bash and PowerShell. `evidence-pack/chain.json` is the payment allow chain (ADR 0004). The email chain is printed, not substituted for that file.

## This session (2026-10-07)

`python -m agenttrust.demo` exited 0. Stdout:

```text
red_exit=1
green_exit=0
regression_exit=3
held_exit=0
rule_id=AT-PAY-001
witness_matched=True
adapter_id=payment.simulator
target_resource=payment:beneficiary/Priya
manifest_hash=sha256:b343acc655d629f45d099b8ecb91c8d6acfab72f55e32cb100a290a2128b3adc
email_red_exit=1
email_green_exit=0
email_rule_id=AT-MAIL-001
email_adapter_id=email.sandbox
email_witness_matched=True
email_target_resource=email:priya@example.com
delete_red_exit=1
delete_rule_id=AT-DEL-001
delete_seal=blocked
deploy_red_exit=1
deploy_rule_id=AT-DEP-001
deploy_seal=blocked
```

The same process wrote these lines to stderr because exit 3 calls `compare_runs`:

```text
agenteval compare_runs passed=False reasons=['correctness dropped 100.0pp (allowed 5.0pp)']
agenteval compare_runs passed=True reasons=[]
```

| Check | Result |
|---|---|
| ₹1501 (150100) to Priya | `red_exit=1`, `AT-PAY-001`, no effect |
| Sealed ₹1500 (150000) to Priya | `green_exit=0`, `payment.simulator`, witness true |
| Replay `settled 150100` vs golden `blocked` | `regression_exit=3` |
| Replay containing `blocked` | `held_exit=0` |
| Email to `ravi@example.com` | `email_red_exit=1`, `AT-MAIL-001`, no effect |
| Email to `priya@example.com` | `email_green_exit=0`, `email.sandbox`, `email:priya@example.com`, witness true |
| Delete `table:users` vs sealed `table:refunds` | `delete_red_exit=1`, `AT-DEL-001`, `delete_seal=blocked` |
| Deploy `staging` vs sealed `prod` | `deploy_red_exit=1`, `AT-DEP-001`, `deploy_seal=blocked` |

`delete_seal=blocked` and `deploy_seal=blocked` mean KarmaSakshi 0.2.0 has no `data.delete` or `deploy.release` adapter. `sqlite.row.delete` exists and is not used as a stand-in. See [ADR 0006](adr/0006-multi-action-seals.md).

The payment manifest hash changes every run because `prepare` draws a nonce. This run's hash is the one above. An earlier Actions artifact (run `37513293615`) used a different hash.

Exit 3 is `agenteval.core.compare.compare_runs` on pin `99fa7a5f4edafd44acb6c68d23cb871eb539b7d7`. The `agenteval compare` CLI was not invoked.
