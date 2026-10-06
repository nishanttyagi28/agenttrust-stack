# ADR 0002: Evidence Schema v1

**Status:** Accepted  
**Date:** 2026-10-06

## Context

Every later slice (importers, gate, CI, demo, report) needs one versioned contract linking Event → Decision → EffectRef → Witness → EvalCase. Langfuse traces, KarmaSakshi Evidence Packs, and CodeGovernor `policyEvents` are each real and each incomplete for the joint claim. A second chain format in any package would make CI checks unverifiable.

## Decision

Adopt **Evidence Schema v1** with `schema_version` string **`"1.0"`**. All packages read and write this shape only. **Extra JSON keys are rejected** at parse time (Pydantic `model_config = ConfigDict(extra="forbid")` or equivalent).

### Encoding

- UTF-8 JSON.
- Canonical form for tests and golden fixtures: `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`.

### Allowed dependencies

| Package | Version | Use |
|---|---|---|
| `pydantic` | `>=2.0,<3` | Typed models, validation, JSON Schema export |
| `pytest` | `>=8,<9` | Round-trip and rejection tests |

No other runtime or dev dependencies without a new ADR.

---

### Chain (document root)

The serialized artifact is one `Chain` object.

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema_version` | string | yes | Must be exactly `"1.0"`. |
| `chain_id` | string | yes | Stable id for this chain instance (UUID or slug). |
| `event` | Event | yes | First record. |
| `decision` | Decision | yes | Policy outcome for the proposed action. |
| `effect_ref` | EffectRef \| null | yes | Present only when `decision.outcome == "allow"`. Must be **null** when outcome is `deny` or `unknown`. |
| `witness` | Witness \| null | yes | Present only when `effect_ref` is non-null. May be non-null with `matched_expected: null` while witness is pending. |
| `eval_case` | EvalCase \| null | yes | Optional regression candidate or approved golden case. |

**Linking:** Each nested record carries `id` (string, unique within the chain) and optional `caused_by` (string \| null, references another record's `id`).

**Outcome rules (schema 1.0):**

When `decision.outcome` is **`deny`** or **`unknown`**:

- `effect_ref` **MUST** be null.
- `witness` **MUST** be null.
- `eval_case` **MAY** be present (Gap 3 regression candidate).
- If `eval_case` is present, `eval_case.caused_by` **MUST** equal `decision.id`.

When `decision.outcome` is **`allow`**:

- `effect_ref` **required** (non-null).
- `witness` **required** (non-null; `matched_expected` may be `null` while pending — that fails CI #2).
- `eval_case` optional; if present, `eval_case.caused_by` **MUST** equal `witness.id`.

Expected causal order:

```
Event (caused_by: null)
  → Decision (caused_by: event.id)
    → EffectRef (caused_by: decision.id)          [allow only]
      → Witness (caused_by: effect_ref.id)        [allow only]
        → EvalCase (caused_by: witness.id)        [allow path, optional]
    → EvalCase (caused_by: decision.id)           [deny/unknown path, optional]
```

---

### Event

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | |
| `caused_by` | string \| null | yes | Null for the chain entrypoint. |
| `actor_id` | string | yes | Agent or service that proposed the action. |
| `timestamp` | string | yes | ISO 8601 UTC (e.g. `2026-10-06T12:00:00Z`). |
| `action_type` | string | yes | Dot-separated intent, e.g. `payment.transfer.propose`. |
| `payload` | object | yes | Redacted proposal parameters. Keys and values are JSON primitives or nested objects of primitives. No secrets. |

---

### Decision

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | |
| `caused_by` | string | yes | Must equal `event.id`. |
| `outcome` | enum | yes | `"allow"` \| `"deny"` \| `"unknown"`. |
| `rule_id` | string \| null | yes | When `outcome == "deny"`, must match `^[A-Z][A-Z0-9]*(-[A-Z0-9]+)+$`. When `outcome == "unknown"`, typically null. When `outcome == "allow"`, null or an informational rule id. |
| `policy_version` | string \| null | yes | Source policy bundle or hook version, if known. |
| `reason` | string \| null | yes | Human-readable deny or unknown explanation. |

**CI semantics (fail #1 — immediate):**

| `outcome` | CI fail #1 | Notes |
|---|---|---|
| `deny` | **Fail immediately** | Whether or not an `eval_case` is present |
| `unknown` | **Fail immediately** | Same; missing `policyEvents` is never allow |
| `allow` | Pass (policy clause only) | Clauses #2 and #3 still apply |

**Missing CodeGovernor `policyEvents` for a required check → `outcome: "unknown"`, never `"allow"`.**

**CI fail #3 (eval regression):** Only after a human sets `eval_case.approval.state` to **`approved`**, that case is written into the AgentEval golden file, and a **later run** still fails it. A **`pending`** `eval_case` is **not** fail #3 and **must not** be written into the golden file.

---

### EffectRef

Points at a KarmaSakshi sealed manifest. Does **not** embed the signing key or the full manifest.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | |
| `caused_by` | string | yes | Must equal `decision.id`. |
| `manifest_hash` | string | yes | `EffectManifest.canonical_hash()` from KarmaSakshi. |
| `effect_type` | enum | yes | One of v1 consequential types (below). |
| `adapter_id` | string | yes | e.g. `payment.simulator.v1`. |
| `target_resource` | string | yes | Payee account, mailbox, table, deploy target, etc. |

**Consequential `effect_type` values in v1:**

| Value | Demo |
|---|---|
| `payment.transfer` | **Yes** (₹1500 → Priya) |
| `email.send` | Reserved |
| `data.delete` | Reserved |
| `deploy.release` | Reserved |

---

### Witness

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | |
| `caused_by` | string | yes | Must equal `effect_ref.id`. |
| `matched_expected` | true \| false \| null | yes | `null` = not yet witnessed. |
| `adapter_id` | string | yes | Witness adapter that performed `verify()`. |
| `detail` | string \| null | yes | Redacted mismatch or success note. |

**CI semantics:** For a consequential `effect_ref`, `matched_expected` must be **`true`**. **`false` or `null` → fail** (unwitnessed or mismatched effect).

---

### EvalCase

Golden fields compatible with AgentEval case loading, plus chain linkage.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | |
| `caused_by` | string | yes | Must equal `decision.id` when `decision.outcome` is `deny` or `unknown`; must equal `witness.id` when `decision.outcome` is `allow`. |
| `chain_id` | string | yes | Copy of parent `Chain.chain_id`. |
| `case_id` | string | yes | Stable case id for AgentEval YAML. |
| `prompt` | string | yes | Adapter prompt or scenario label. |
| `expects` | object | yes | AgentEval expectation object (exact / contains / numeric correctness, etc.). |
| `approval` | object | yes | See below. |

**`approval` object:**

| Field | Type | Required |
|---|---|---|
| `state` | `"pending"` \| `"approved"` \| `"rejected"` | yes |
| `actor` | string \| null | yes |
| `note` | string \| null | yes |

**Rules:** A case with `approval.state` of **`pending` or `rejected` MUST NOT** be written into the CI golden file. There is **no auto-approve** path.

---

### Gate rule IDs (reserved for v1 implementation)

Enforcement lives in `packages/gate` later. This ADR only reserves stable IDs matching `^[A-Z][A-Z0-9]*(-[A-Z0-9]+)+$`:

| Rule ID | Meaning |
|---|---|
| `AT-PAY-001` | Payment amount differs from sealed effect |
| `AT-PAY-002` | Payee not on the sealed allowlist |
| `AT-MAIL-001` | Email recipient not on allowlist |
| `AT-DEL-001` | Delete target not on allowlist |
| `AT-DEP-001` | Deploy target not on allowlist |

CodeGovernor rule IDs (e.g. `CG-SHELL-001`) are imported as-is from `policyEvents`; they are not renumbered.

---

## Alternatives considered

- **Embed full KarmaSakshi SealedManifest in Chain.** Rejected. Duplicates seal crypto and bloats fixtures; `manifest_hash` + upstream pack is enough.
- **Binary `outcome` (allow/deny only).** Rejected. CodeGovernor missing events require an explicit `unknown` that fails closed.
- **Permissive extra keys.** Rejected. Silent field drift breaks importers and CI comparators.

## Consequences

- Agent B (Evidence package) can implement models and round-trip tests without further schema questions.
- Deny/unknown stops before seal — no `EffectRef` or `Witness`, but an optional `EvalCase` may capture the failure for human approval (Gap 3).
- Schema 1.1 can add fields later by bumping `schema_version`; 1.0 parsers reject unknown keys today.
- Demo and report apps consume the same JSON the CI package validates.
