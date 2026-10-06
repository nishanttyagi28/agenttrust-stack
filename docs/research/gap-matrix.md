# Gap matrix

Phase 0. Status labels describe what was **read** on 2026-10-06, not a full audit of every public codebase.

| Label | Meaning |
|---|---|
| **Have** | Present in that repo’s README or, for my repos, in the docs and package layout reviewed in [top20-comparison.md](top20-comparison.md). |
| **Partial** | A related mechanism exists and does not satisfy the row. |
| **Missing** | Not found in the reviewed surface. For public repos this means “not stated in the README reviewed,” which is not a proof of absence. For my repos the tree and docs were read, so Missing is stronger. |
| **Out of scope** | Explicitly disclaimed, or a different product layer that the umbrella should not absorb. |

Short names: **AE** AgentEval, **KS** KarmaSakshi, **PG** PromptGate, **CG** CodeGovernor, **VE** VisionEval.

## 1. My five projects

### Eval and regression

| Capability | AE | KS | PG | CG | VE |
|---|---|---|---|---|---|
| Declarative golden cases | Have | Missing | Have (JSON contains/exact/regex) | Missing | Have |
| Baseline compare, CI non-zero exit | Have | Missing | Partial (CLI exit 1, no baseline file) | Partial (pipeline FAIL, not an eval suite) | Have |
| Deterministic scorers, no LLM required | Have | Out of scope | Have | Partial (pytest + review gate) | Have |
| Optional LLM-as-judge | Have | Out of scope | Missing | Missing | Missing |
| RAG retrieval metrics | Partial | Out of scope | Missing | Out of scope | Out of scope |
| Red-team case generation (human must promote) | Have | Missing | Missing | Missing | Missing |
| Tool-call / trajectory match | Have | Missing | Missing | Partial (tool log, not a golden trajectory) | Out of scope |
| SQL or other structured safety scan | Have (`agenteval sql`) | Missing | Missing | Missing | Out of scope |
| Framework adapters (CrewAI, AutoGen, LangGraph, OpenAI Agents) | Have | Partial (LangGraph handoff only) | Missing | Out of scope | Out of scope |
| Failure capture, redact, fingerprint, cluster | Have | Partial (exact-signature JSONL, no cluster, advisory) | Missing | Missing | Partial (vision traps, not agent traces) |
| Replay and minimize a failure | Have | Missing | Missing | Partial (offline replay of a recorded coding run) | Missing |
| Human approve before a case can fail CI | Have | Partial (human grant before **execution**, not before a golden export) | Missing | Partial (`--interactive` y/n on budget/retry) | Missing |
| Production incident → golden file | Have (Failure Memory + Release Desk) | Partial (neutral `RegressionFixture`, not AE YAML) | Missing | Missing | Partial (trap harvest) |

### Runtime control and effect proof

| Capability | AE | KS | PG | CG | VE |
|---|---|---|---|---|---|
| Policy enforced in code/hooks, not only markdown | Partial (SQL scanner; eval does not block a live tool) | Partial (grants and policy bundles; intelligence recommendations are advisory) | Missing | Have | Out of scope |
| Stable rule IDs on deny | Missing | Missing | Missing | Have (coding tools; live SDK deny not yet observed, ADR 0005) | Out of scope |
| Exact-effect seal (hash of target, amount, params, preconditions) | Missing | Have | Missing | Missing | Out of scope |
| Human grant bound to that hash, agent cannot self-approve | Missing | Have | Missing | Missing | Out of scope |
| Exactly-once reservation and stale-state recheck | Missing | Have | Missing | Missing | Out of scope |
| Independent witness of external state | Missing | Have (reference adapters) | Missing | Missing | Out of scope |
| Portable verifiable pack for one effect | Missing | Have (`evidence_pack.v1`) | Missing | Missing | Out of scope |
| Coding-agent budgets, checkpoints, role tool allowlists | Partial (coding-agent **template** only) | Out of scope | Missing | Have | Out of scope |
| `AGENTS.md` as guidance | Missing | Missing | Missing | Have (and ADRs say it is not enforcement) | Missing |

### The joint claim

| Capability | AE | KS | PG | CG | VE |
|---|---|---|---|---|---|
| One typed chain: Event → Decision → Effect → Witness → EvalCase | Missing | Partial (pack is Effect + grant + audit, no Decision, no EvalCase) | Missing | Partial (`policyEvents` only) | Missing |
| One CI check: policy deny **or** unwitnessed effect **or** eval regression | Missing | Missing | Missing | Missing | Missing |
| Witness mismatch or rule deny becomes an approved AgentEval case without hand-written YAML | Partial (bridge demo records a failure; promotion is still the AE review flow, and KS memory does not write the YAML) | Partial (export fixture; memory does not gate CI) | Missing | Missing | Out of scope |
| Offline demo of a wrong payment that turns CI red, then green | Partial (₹1500 → Priya demo inside AE) | Partial (`demo --all` scenario, separate repo) | Missing | Out of scope | Out of scope |

## 2. Public repos

`.` means not stated in the README reviewed.

### Eval repos

Columns: promptfoo (**pf**), DeepEval (**de**), Ragas (**rg**), Inspect (**in**), Langfuse (**lf**), Phoenix (**px**), AgentEvals (**av**), Autoevals (**au**).

| Capability | pf | de | rg | in | lf | px | av | au |
|---|---|---|---|---|---|---|---|---|
| Golden / dataset evals | Have | Have | Have | Have | Have | Have | Have | Partial |
| CI gate for behavior | Have | Have | . | Partial | Partial | Partial | Partial | . |
| Deterministic checks | Have | Have | Have | Have | Have | . | Have | Have |
| LLM-as-judge | Have | Have | Have | Have | Have | Have | Have | Have |
| RAG metrics | Have | Have | Have | . | Partial | Have | . | Have |
| Red team generation | Have | Partial | Partial | Partial | . | . | . | . |
| Trajectory / tool match | Partial | Have | . | Have | Partial | Partial | Have | . |
| Production trace store | . | Partial (Confident AI is separate) | . | . | Have | Have | . | . |
| Human approve then block CI | . | . | . | . | Partial (manual labels) | . | . | . |
| Exact-effect seal + witness | . | . | . | . | . | . | . | . |

### Gateways and guardrails

Columns: Guardrails AI (**ga**), NeMo Guardrails (**nm**), Portkey gateway (**pk**), LiteLLM (**ll**), PurpleLlama (**pl**), Invariant (**iv**).

| Capability | ga | nm | pk | ll | pl | iv |
|---|---|---|---|---|---|---|
| Input/output text guards | Have | Have | Have | Partial | Have (classifiers) | Have |
| Tool / execution checks | . | Have (execution rails) | Partial (MCP access control) | Partial (MCP gateway) | Partial (Code Shield) | Have (trace rules) |
| Stable application rule IDs | . | Partial (Colang flows) | . | . | . | Partial (rule text, not an ID scheme) |
| LLM routing, keys, spend | . | . | Have | Have | . | . |
| Exact-effect seal | . | . | . | . | . | . |
| Independent outcome witness | . | . | . | . | . | . |
| Failure becomes a golden CI case | . | . | . | . | . | . |

### Approval, harness, sandbox

| Capability | HumanLayer | OpenHands | goose | Codex | AGENTS.md | E2B |
|---|---|---|---|---|---|---|
| Human approval of an action | Not claimed (README says the code is deprecated) | . | . | . | . | . |
| Exact-effect witness | . | . | . | . | . | . |
| Coding-agent runtime | . | Have | Have | Have | Out of scope (a file format) | Partial (runs generated code) |
| Markdown guidance only | . | . | . | . | Have | . |
| Sandbox / isolation | . | Partial (Docker/VM; no-sandbox mode is full filesystem) | . | . | . | Have |
| Policy in hooks with rule IDs | . | . | . | . | Missing by design | . |
| Joint CI of policy + witness + eval | . | . | . | . | . | . |

## 3. Where the public tools already won

Do not spend the 2–4 weeks here.

| Job | Who already does it | Umbrella stance |
|---|---|---|
| Metric catalog and LLM judges | DeepEval, promptfoo, Ragas, Autoevals, Inspect | **Out of scope.** AE already has deterministic scorers and an optional offline judge. |
| RAG scoreboards | Ragas, DeepEval, Phoenix, Autoevals | **Out of scope.** AE’s RAG mode is enough for the story. |
| Trace platforms | Langfuse (MIT core), Phoenix (ELv2) | **Out of scope.** A collector does not prove a ledger moved. |
| LLM proxy, virtual keys, fallbacks | LiteLLM, Portkey | **Out of scope.** Different buyer, large codebases, Portkey’s last push is 2026-05-25. |
| Toxicity / injection classifiers | PurpleLlama, Guardrails Hub | **Out of scope.** Needs model weights. The demo is CPU and offline. |
| Coding IDE or cloud sandbox | Codex, OpenHands, goose, E2B | **Out of scope.** CG is the personal control plane. E2B breaks the offline demo. |
| Another approval inbox | HumanLayer’s public repo is deprecated; KS Control Center exists | **Out of scope** as a UI rewrite. |
| Vision regression | VisionEval | **Out of scope** for v1. Cite the trap pattern only. |
| Reviving PromptGate | AE already has contains/exact checks | **Out of scope.** Also has no license file. |

## 4. Recommended top 8 gaps

These are the missing pieces that make the thesis measurable, fit a fresher AI-engineer portfolio (deterministic, tested, local, no cloud agent), and can land as vertical slices in about 2–4 weeks. Order is the implementation order.

### 1. Evidence Schema v1

**Missing everywhere as a shared contract.**

One versioned model, suggested fields:

- `Event` — who proposed what, when, redacted payload
- `Decision` — allow or deny, **rule id**, policy version
- `EffectRef` — points at a KarmaSakshi manifest hash; does not reimplement the seal
- `Witness` — `matched_expected` plus adapter id; does not reimplement `verify()`
- `EvalCase` — the golden fields AgentEval already loads, plus the id of the chain

Pydantic models, golden JSON fixtures, round-trip tests. Unknown fields fail closed. No LLM.

Why first: every later slice is a liar if this file does not exist. Langfuse traces and KS Evidence Packs are each real and each incomplete for this claim.

### 2. Importers from the existing repos, not forks

**Partial today, three incompatible shapes:**

- AgentEval `TraceEnvelope` / production YAML
- KarmaSakshi `RegressionFixture` 1.0 and `evidence_pack.v1`
- CodeGovernor `summary.json` `policyEvents`

Write one-way mappers and tests against **checked-in fixtures copied from those repos’ public examples**, not against a live rewrite. KarmaSakshi’s own docs say the fixture is not AgentEval’s schema. The mapper is the product.

Do not vendor the 1,152 or 1,077 tests into this repo.

### 3. Deny or witness-mismatch → candidate → human approve → AgentEval YAML

**Partial.** AgentEval can do this for a trace it already stores. KarmaSakshi will not write that YAML, and its memory cannot block a commit. The slice is an offline function:

mismatched witness or `Decision.deny` → Failure Memory candidate (or a thin local stand-in that **calls** AgentEval’s export if installed) → human approve → `cases.yaml` that `agenteval run` already understands.

No automatic approval. That rule already exists in AgentEval and must stay.

### 4. Consequential-action Decision records

**Missing as a shared object. Have inside CodeGovernor for coding tools only.**

A small Python gate, rule IDs in code, for a fixed set: payment, email, delete, deploy. Example: `AT-PAY-001` amount above a sealed limit, `AT-PAY-002` payee not in the allowlist. Deny **before** any adapter call. Emit a `Decision`.

This is the PromptGate/CodeGovernor idea applied to side effects. It is not a Portkey fork and not a Colang port. PromptGate’s text matcher stays unused.

### 5. Attach KarmaSakshi seal and witness; do not re-seal

**Have in KS, Missing on the chain.**

The chain stores the manifest hash, grant id, and witness result produced by `karmasakshi-protocol`. If the witness does not match, the chain cannot record an `EvalCase` pass. Tests use the existing payment simulator (₹1500 → Priya is already the documented story in both repos). No Stripe, no real mail.

### 6. One local CI check with three fail reasons

**Missing.**

A single command, suitable for a GitHub Actions workflow later, exits non-zero when any of these is true:

1. a required `Decision` is deny,
2. a consequential effect has no matching witness,
3. AgentEval baseline compare reports a regression.

Offline. No cloud runner. The workflow file can live in this repo and shell out to the installed CLIs.

### 7. Wrong-payment demo as the acceptance test

**Partial in two repos, not one path.**

One offline script: agent attempts the wrong payment → gate or seal blocks it → witness records the mismatch → fixture is written → CI is red → the case is fixed (attempt matches the seal) → CI is green. Print the actual exit codes and file names into the README after the run. Do not invent pass rates.

### 8. One evidence report

**Missing.** Both AE (Streamlit/HTML) and KS (Control Center) have UIs that do not show this chain.

A CLI that prints the five objects as JSON, plus one static HTML page generated from that JSON. That is the “dashboard” for v1. A multi-page app is a later slice.

## 5. Why this set, and why not a monorepo merge yet

A fresher portfolio in this space is easy to drown: another judge metric, another gateway, another coding CLI. Reviewers can already point at promptfoo (25k stars), LiteLLM (60k), and Codex (128k). They cannot point at a tested artifact that ties a rule id, a sealed refund, a witness bit, and a CI case together. That is the expensive production hole (wrong payment, ignored prompt rule, failure rediscovered in prod) and it is small enough to finish.

**Recommended home (decision for your OK, not an ADR yet):** a new thin repo, this one (`agenttrust-stack`), that **depends on** `nishanttyagi-agenteval` and `karmasakshi-protocol` and **reads** CodeGovernor `summary.json`. Do not fold the three git histories together. AgentEval on PyPI is still 0.3.0 while `main` is 0.5.0; the first ADR should pin a commit or a path install. PromptGate is not a package to import (no license, text-only). VisionEval stays a sibling.

Reversible if you prefer otherwise: the schema package can later move into AgentEval as an extra. Starting there now would mix a cross-repo contract into a library whose own v1 readiness doc says schemas are still unstable.

## 6. Risks to accept before coding

- CodeGovernor ADR 0005: `policyEvents` may miss a real hook denial. The importer must treat “no event” as unknown, not as allow.
- KarmaSakshi adapters are simulators. The README numbers (1,077 tests, 15 scenarios) are not a production payment integration.
- AgentEval Failure Memory refuses export when content capture is off. The demo has to opt in to redacted content or the golden step will fail closed. That is correct behavior, not a bug to bypass.
- Adding dependencies (Pydantic is the obvious one) needs an ADR, per your rule. AgentEval today depends on PyYAML, pandas, Streamlit, and sqlglot; the schema package should not drag Streamlit in.
- This Phase 0 pass did not re-run the five repos’ tests. Slice 1 should pin versions and run the importer tests only.

## 7. What I need from you

Approve or correct these three points, then Phase 1 is an architecture note plus ADRs, still before feature code:

1. Thin new repo that imports the existing packages, rather than merging into AgentEval.
2. The top 8 above, in that order, stopping after each slice.
3. PromptGate and VisionEval stay out of the v1 code path.

No product code until that OK.
