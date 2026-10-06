# ADR 0006: Seal only the reference adapters KarmaSakshi 0.2.0 ships

**Status:** Accepted  
**Date:** 2026-10-07

## Context

`karmasakshi.adapters.registry.reference_adapter_capabilities` in `karmasakshi-protocol` 0.2.0 lists three adapters:

| adapter_id | effect types |
|---|---|
| `payment.simulator` | `payment.transfer` |
| `email.sandbox` | `email.send` |
| `sqlite.row` | `sqlite.row.insert`, `sqlite.row.update`, `sqlite.row.delete` |

`karmasakshi.cli.adapter_factory` documents the same three CLI choices: `payment`, `email`, `sqlite`. There is no `deploy.release` adapter and no `data.delete` effect type.

Evidence Schema v1 `EffectType` is `payment.transfer`, `email.send`, `data.delete`, `deploy.release`. Recording a SQLite row delete as `data.delete` would name an effect the seal did not authorize.

## Decision

1. `attach_email` seals `email.send` with `EmailSandboxAdapter` (`adapter_id` `email.sandbox`) through `prepare`, `seal`, `authorize`, `commit`, and `verify`. A recipient mismatch is `AT-MAIL-001` and does not call `commit`.
2. `data.delete` stays a gate rule (`AT-DEL-001`) only. `sqlite.row.delete` is a different effect type and is not aliased.
3. `deploy.release` stays a gate rule (`AT-DEP-001`) only. No reference adapter exists. No simulator wrapper is added.

## Alternatives considered

- **Map `sqlite.row.delete` onto `data.delete`.** Rejected. The manifest effect type would be `sqlite.row.delete` while the chain would say `data.delete`.
- **Add a local deploy simulator.** Rejected. That would be cryptography and effect execution this repo does not own.

## Consequences

The offline demo prints a red-then-green email path and a red-only delete and deploy path with `delete_seal=blocked` and `deploy_seal=blocked`. Rule IDs stay in code.
