# Top-20 comparison

Phase 0 research for AgentTrust Stack. No product code in this pass.

Snapshot date: **2026-10-06**. Stars and `pushed_at` come from the GitHub REST API (`gh api repos/<owner>/<repo>`). Several historical names redirect; the table uses the canonical `full_name` the API returned. Licenses were read from each repo’s `LICENSE` file unless noted. Feature bullets are taken from the README (or, for my repos, README plus the docs named below). A feature that is not in those files is not claimed.

I did **not** re-run test suites or audit implementations of the public repos. Test counts for my repos are the numbers their READMEs state, not a fresh pytest/vitest run on 2026-10-06.

## What my five projects already own

Do not rebuild these.

### AgentEval — [nishanttyagi28/agenteval](https://github.com/nishanttyagi28/agenteval)

| | |
|---|---|
| Stars / last push | 4 / 2026-10-02 |
| License / language | MIT / Python 3.10+ |
| Package | `nishanttyagi-agenteval`. README: `main` is **0.5.0**; latest **published** PyPI is **0.3.0**. Classifier: Alpha. |
| README test claim | 1152 passed, 3 skipped (Docker, FastAPI, KarmaSakshi extras absent); Failure Memory suite 59 passed |

Owns:

1. **CI regression gate.** YAML golden suites, scored runs, git-trackable baseline, non-zero exit on regression. Composite GitHub Action (`action.yml`). CLI: `agenteval run` / `compare`.
2. **Deterministic evidence, not one score.** Exact / contains / numeric correctness, hallucination vs ground truth, tool precision/recall/F1, latency/cost, trajectory (LCS F1), optional flakiness repeats. LLM judge is optional; `AGENTEVAL_JUDGE_PROVIDER=offline` scores open-ended cases with no key.
3. **Failure Memory.** TraceEnvelope schema v1 → redact before disk → deterministic taxonomy and fingerprint → clustering → replay → minimize → **human approve** → golden YAML → `agenteval run --production-cases`. SQLite under `.agenteval/`. Schema version on main is 5. No auto-approval.
4. **Adapters.** CrewAI, AutoGen, OpenAI Agents SDK, LangGraph, custom, plus an optional KarmaSakshi bridge (`adapters/karmasakshi.py`). Templates: coding-agent, customer-support, rag-assistant, indic-agent.
5. **Narrow safety and desk tools.** `agenteval sql` structural/policy scanner (exit 2 on block). Local Release Desk (`agenteval gate --local`) ingests an incident and writes `.agenteval/production-regressions.yaml`. Optional RAG checks. Redaction is best-effort, not a DLP product.

Explicit non-goals in `docs/failure-memory.md` and `docs/v1-readiness.md`: not multi-tenant, not an OpenTelemetry collector, not a hosted control plane, not v1-stable. `docs/v1-readiness.md` still lists schema versioning and public-API inventory as blockers.

KarmaSakshi bridge (`docs/karmasakshi-bridge.md`): offline demo, approved effect **₹1500 → Priya**. ₹1501 or payee Ravi is blocked (`ManifestTamperedError`) and scored as an AgentEval failure. This is a demo adapter, not a shared schema used by CodeGovernor or PromptGate.

### KarmaSakshi Protocol — [nishanttyagi28/karmasakshi-protocol](https://github.com/nishanttyagi28/karmasakshi-protocol)

| | |
|---|---|
| Stars / last push | 2 / 2026-09-26 |
| License / language | MIT / Python |
| Package | `karmasakshi-protocol` **0.2.0**, experimental |
| README test claim | 1077 passed, 8 skipped (Redis). 85 security invariants. 15 demo scenarios. 3 reference adapters. |

Owns the question the permission tools do not answer: **did the exact effect a non-agent approved become the outcome that actually happened?**

1. **Exact-effect seal.** `EffectManifest.canonical_hash()` binds target, amount, parameters, and preconditions. A later edit is a different object.
2. **Grant bound to that hash.** Human or service key issues the grant. The agent cannot approve itself. Single-use by default. Scoped, expiring, revocable.
3. **Commit-time checks.** Preconditions re-validated inside `commit` (`StaleManifestError`). Atomic reserve so concurrent retries get one success. `recover_ambiguous_commit()` for the crash between external success and local record.
4. **Independent witness.** `adapter.verify()` re-reads the adapter’s system of record. `OutcomeProof.matched_expected` records intent-vs-outcome mismatch. Action Passport and offline-verifiable Evidence Pack (`evidence_pack.v1`, `karmasakshi.portable`).
5. **Reference adapters and audit.** Payment simulator, email sandbox, SQLite rows. Hash-chained audit journal. Control Center UI. LangGraph handoff that only narrows a grant.

`docs/comparison.md` (reviewed by that repo on 2026-07-28) already separates this from IAM, credential brokers, and policy gateways (Grantex, AgentLattice, Xybern, OpenLeash). Those products, in the docs that file reviewed, prove an **authorization decision**. KarmaSakshi’s passport includes the **verified outcome**.

Honest limits that matter for the umbrella (`docs/limitations.md`, `docs/agenteval-integration.md`):

- Not audited, not a real bank/mail/database connector, not production-proven.
- `karmasakshi.integrations.agenteval` exports a **neutral** `RegressionFixture` (`FIXTURE_SCHEMA_VERSION = "1.0"`). The KarmaSakshi doc still says this is **not** AgentEval’s internal schema. AgentEval’s later bridge consumes the engine directly; the two fixture stories are not one typed chain.
- `FailureMemoryStore` in KarmaSakshi is an append-only JSONL keyed by an **exact** signature (`effect_type + adapter_id + failure_category + invariant`). It does not cluster, does not write AgentEval YAML, and **does not affect** `authorize()` or `commit()`. Advisory only.
- Effect Intelligence recommendations are advisory. Signed policy bundles pin which policy was used; they do not by themselves enforce the recommendation.
- Evidence Pack verifies one manifest’s seal, grant, and audit slice. It does not carry a CodeGovernor rule ID or an AgentEval golden case.

### PromptGate — [nishanttyagi28/promptgate](https://github.com/nishanttyagi28/promptgate)

| | |
|---|---|
| Stars / last push | 0 / 2026-08-28 (`master`) |
| License | **No license file** (`licenseInfo` null). Do not treat it as reusable until a license is added. |
| README test claim | 16 passed |

Owns a **text contract checker**, not a runtime gate:

- Rules: `contains` (default), `exact`, `regex`.
- `POST /eval`, `POST /eval/batch`, CLI `python -m app.cli`, exit code 1 if any case fails, JSONL log.
- No model calls. No tool calls. No dashboard. README says it is a prototype and not an AI gateway (and not promptgate.dev).

AgentEval already scores contains/exact/regex-style expectations. PromptGate should not be rebuilt as the policy engine. Its only reusable idea is “freeze the contract, fail the process.”

### CodeGovernor — [nishanttyagi28/codegovernor](https://github.com/nishanttyagi28/codegovernor)

| | |
|---|---|
| Stars / last push | 0 / 2026-10-04 |
| License / language | MIT / TypeScript (Node ≥ 22.13) |
| Runtime | `@cursor/sdk`, local agents only (ADR 0001) |

Owns a **coding-agent control plane**, enforced in hooks and TypeScript, not in `AGENTS.md`:

1. **Rule IDs.** `CG-SHELL-001` … `CG-SHELL-004`, `CG-READ-*`, `CG-GATE-001` (refuse to start a role whose allowlist contains a shell tool unless an orchestrator command allowlist exists), `CG-GATE-002` (every recorded shell call). ADR 0005. Source of truth is the hook scripts and `src/tool-gate.ts`, not the markdown index.
2. **Fail-closed hooks.** `beforeShellExecution` allowlist (`python -m pytest|compileall`). `beforeReadFile` denies paths outside the workspace.
3. **Deterministic review gate.** Failing pytest, a changed file not in the plan, or a coder path outside the workspace forces FAIL even if the reviewer model says PASS.
4. **Budget and checkpoints.** Worst-case run cap checked before the first agent (`maxRuns` default 6). Duplicate-failure abort. Git refs under `refs/codegovernor/` restore the workspace on any non-PASS.
5. **Audit log.** Redacted tool args (200 chars), `policyEvents` in `summary.json`. Offline replay: `npm run demo:replay`.

Two recorded runs are in the README (477,882 tokens / about $0.19 list-price estimate, and 727,269 tokens / about $0.29). Those runs predate the current hooks. ADR 0005 says rule IDs on hook denials are **unit-tested only**; no real SDK run has produced a `policyEvent`, and the SDK may not surface hook denies in a way `policyEvents` can parse. The umbrella must not claim live hook denial is proven.

CodeGovernor does not seal a payment, witness a ledger, or emit an AgentEval case. It is Cursor-SDK-specific.

### VisionEval — [nishanttyagi28/VisionEval](https://github.com/nishanttyagi28/VisionEval)

| | |
|---|---|
| Stars / last push | 2 / 2026-09-02 (`master`) |
| License | Apache-2.0 |
| README test claim | 109 tests. Version 0.1.0. |

Owns the same **regression-memory pattern** for vision models: golden suite, baseline, failure “traps” that stay until the model passes twice, failure maps, budgeted re-test, CPU claim-check (`supported` / `contradicted` / `insufficient`) without a paid API.

Useful as a sibling story. Out of scope for the agent evidence chain. Do not merge it into the umbrella v1.

## How the five fit the thesis today

Thesis: a consequential action cannot ship unless (a) policy allowed it, (b) a human sealed the exact effect when required, (c) the outcome was witnessed, and (d) any failure becomes an approved CI regression.

| Clause | Where it exists | What is still separate |
|---|---|---|
| (a) policy allow | CodeGovernor hooks + tool gate, for **coding** tools. AgentEval SQL scanner, for **SQL text**. KarmaSakshi grants, as a supporting control on an already-resolved effect. | No shared Decision record. PromptGate does not gate actions. |
| (b) human seals the exact effect | KarmaSakshi seal + grant. | Not referenced by CodeGovernor or PromptGate. |
| (c) outcome witnessed | KarmaSakshi `verify` / Evidence Pack. | AgentEval scores the bridge demo; it does not store the pack. |
| (d) failure → approved CI case | AgentEval Failure Memory and Release Desk. | KarmaSakshi’s JSONL memory is advisory and does not write that YAML. CodeGovernor `policyEvents` are not cases. |

The expensive gap is the **missing joint artifact and the missing joint CI check**, not another metric library.

## Public set (20)

Selection rule: public repos that teams actually adopt for eval, runtime policy, human approval, or agent/sandbox control. Highest-star coding IDEs are included only so the matrix shows they are a different product. Braintrust’s hosted product is not open source; `autoevals` is the OSS slice the brief asked for.

Redirects observed on 2026-10-06:

- `explodinggradients/ragas` → `vibrantlabsai/ragas`
- `All-Hands-AI/OpenHands` → `OpenHands/OpenHands`
- `block/goose` → `aaif-goose/goose`
- `NVIDIA/NeMo-Guardrails` → `NVIDIA-NeMo/Guardrails`
- `openai/agents.md` → `agentsmd/agents.md`

### Also considered, not in the 20

| Repo | Why it is not a column |
|---|---|
| `openai/evals` | 19,561 stars, last push 2026-04-14, license SPDX `NOASSERTION`. Historical registry of model evals, not an agent evidence chain. Stale relative to promptfoo / DeepEval / Inspect. |
| `protectai/llm-guard` | 3,215 stars, **archived**, last push 2026-07-08. |
| `microsoft/autogen` | 61,275 stars, last push 2026-04-15, license CC-BY-4.0. An agent framework. AgentEval already has an adapter. Not a gate or an effect witness. |
| `cline/cline` | 69,943 stars, Apache-2.0, active. Another coding IDE. Same bucket as Codex / OpenHands; one column of that bucket is enough. |
| `Aider-AI/aider` | 49,397 stars, Apache-2.0, last push 2026-05-22. Coding agent, not effect verification. |
| `traceloop/openllmetry` | 7,470 stars, Apache-2.0, active. OTel instrumentation library. Langfuse and Phoenix already cover the trace-platform column. |
| `anthropics/claude-code` | 149,608 stars, last push 2026-10-06, **no SPDX license** on the API payload (`license: null`). Not treated as an OSI dependency. |
| `huggingface/lighteval` | 2,553 stars, MIT, active. Model-benchmark harness, not agent governance. |

## Bucket A — eval, golden suites, CI

### 1. promptfoo/promptfoo

25,752 stars. Pushed 2026-10-06. MIT. TypeScript. README: now part of OpenAI; remains MIT.

1. Declarative evals of prompts, agents, and RAGs (`promptfoo eval`).
2. Red teaming and vulnerability scanning.
3. Side-by-side model comparison across many providers.
4. CI/CD checks; local-by-default (README: prompts need not leave the machine).
5. PR code scanning for LLM security and compliance issues.

Does not claim an exact-effect seal or an independent ledger witness.

### 2. confident-ai/deepeval

18,659 stars. Pushed 2026-10-05. Apache-2.0. Python. Pytest-style.

1. Large metric catalog: G-Eval, DAG, task completion, tool correctness, argument correctness, plan adherence, step efficiency.
2. RAG metrics (relevancy, faithfulness, contextual precision/recall) and multi-turn chat metrics.
3. MCP use / task-completion metrics.
4. Synthetic single- and multi-turn datasets; CI integration.
5. Component-level and end-to-end eval; custom metrics. Confident AI is the separate hosted product.

Does not seal or witness a real-world side effect. Overlaps AgentEval’s tool and RAG checks; AgentEval’s advantage is Failure Memory plus the KarmaSakshi demo, not metric count.

### 3. vibrantlabsai/ragas

15,948 stars. Pushed **2026-02-24** (about seven months before this snapshot). Apache-2.0. Python.

1. Objective RAG / LLM-app metrics (LLM-based and traditional).
2. Test-data generation when no dataset exists.
3. LangChain and observability integrations.
4. Production-data feedback loops (README claim).
5. Project templates (`ragas` quickstart clones an eval project).

Stale commit history. Wrong layer for payments and deploys. AgentEval’s optional RAG mode does not need to become Ragas.

### 4. UKGovernmentBEIS/inspect_ai

2,947 stars. Pushed 2026-10-06. MIT. Python. UK AI Security Institute.

1. Eval framework for tool use, multi-turn dialog, and model-graded scoring.
2. Extensions via other Python packages.
3. **200+ pre-built evaluations** (README).
4. Docs published for coding agents (`llms.txt` / `llms-full.txt`).
5. Reproducible dev install (`uv sync --extra dev`, `make test`).

This is the serious agent-eval harness. It is a research/safety runner, not a production failure-memory loop and not an effect witness. Do not reimplement Inspect.

### 5. langfuse/langfuse

35,439 stars. Pushed 2026-10-06. **MIT for everything outside `ee/`**; enterprise directories need the `ee` license (LICENSE text, copyright 2023–2026 ClickHouse, Inc.). README: part of ClickHouse since January 2026.

1. Trace observability for LLM calls, retrieval, and agent actions.
2. Prompt management with caching.
3. Evals: LLM-as-a-judge, code evaluators, human labels, user feedback.
4. Datasets and experiments.
5. Self-host (Docker Compose, Helm) plus a cloud product. API and typed SDKs.

Owns traces and scores. Does not, in the README, bind a human-approved effect hash to a re-read ledger.

### 6. Arize-ai/phoenix

11,732 stars. Pushed 2026-10-06. **Elastic License 2.0** (source-available, not OSI). Hosted-service restriction is in the license text.

1. OpenTelemetry / OpenInference tracing.
2. LLM evals for response and retrieval.
3. Versioned datasets and experiments.
4. Playground and prompt management.
5. Remote MCP endpoint for coding agents to query traces. Arize AX is the separate managed product.

Same layer as Langfuse. License makes it a poor thing to vendor.

### 7. langchain-ai/agentevals

740 stars. Pushed **2026-07-14**. MIT. Python and TypeScript.

1. Trajectory match against a reference: strict, unordered, subset, superset.
2. Tool-argument equality modes and per-tool overrides.
3. Optional LLM judge of a trajectory.
4. Messages as OpenAI dicts or LangChain messages.
5. Aimed at LangSmith’s pytest eval flow (README points at LangSmith docs).

Closest small OSS analog to AgentEval’s trajectory checker. Lower level than Failure Memory. LangSmith itself is not this repo.

### 8. braintrustdata/autoevals

1,044 stars. Pushed 2026-10-02. MIT. Python and TypeScript.

1. LLM-as-a-judge scorers (factuality, closed QA, moderation, security, summarization, SQL, translation).
2. RAG scorers (context precision/recall/relevancy, faithfulness, answer correctness).
3. Heuristic and embedding scorers; composite scores.
4. Custom classifier prompts.
5. Optional Braintrust logging. The hosted Braintrust product is not this library.

This is the OSS “Braintrust” slice. It is a scorer library. AgentEval already has its own scorers.

## Bucket B — runtime policy, gateways, guardrails

### 9. guardrails-ai/guardrails

7,492 stars. Pushed 2026-10-06. Apache-2.0. Python.

1. Input and output guards that detect and mitigate classes of risk.
2. Structured generation from LLMs.
3. Guardrails Hub of validators (README, 2026-07-06: validators moving to normal PyPI packages; hosted remote inference planned to end 2026-08-25).
4. Guardrails Server, usable from the OpenAI SDK.
5. Guardrails Index benchmark of validators (README points at index.guardrailsai.com).

Validates **text and structure**. It is not an exact-effect commit protocol.

### 10. NVIDIA-NeMo/Guardrails

7,248 stars. Pushed 2026-10-06. README badge says **Apache-2.0**. The raw `LICENSE` file did not download in this pass (API error), so the badge is the source, not a byte-checked LICENSE.

1. Programmable rails for conversational apps (Colang).
2. Five rail types: input, dialog, retrieval, **execution** (tool input/output), output.
3. Configuration folder (`config.yml` plus rails) that can refuse or rewrite a turn.
4. Multiple LLM backends.
5. Library plus docs at docs.nvidia.com/nemo/guardrails. Latest release named in the README: 0.24.1.

Execution rails are the nearest “tool guard” in this bucket. They steer a dialog configuration. They do not hash a sealed refund or write an AgentEval case.

### 11. Portkey-AI/gateway

13,133 stars. Pushed **2026-05-25**. MIT. TypeScript.

1. OpenAI-compatible local gateway.
2. Fallbacks, retries, load balancing, timeouts.
3. Guardrail checks on inputs and outputs (README: 40+ pre-built checks, bring-your-own).
4. Virtual keys, RBAC, caching, usage analytics.
5. MCP gateway: auth, tool access control, tool-call logs, identity forwarding.

A routing and compliance proxy. Last commit is four months before this snapshot. Do not fork it to get a payment witness.

### 12. BerriAI/litellm

60,237 stars. Pushed 2026-10-06. **MIT outside `enterprise/`**; `enterprise/` has its own license.

1. One Python SDK over many chat/embedding/audio/image endpoints.
2. AI Gateway proxy: virtual keys, spend, and routing.
3. MCP bridge and MCP gateway (README sections).
4. Agents and A2A endpoints (README sections).
5. Drop-in use from existing OpenAI-style clients, including Cursor (README).

The default OSS gateway. Policy here is key, spend, and route. It is not “seal ₹1500 to Priya, then re-read the ledger.”

### 13. meta-llama/PurpleLlama

4,422 stars. Pushed 2026-09-29. **Llama 3.2 Community License** for Llama Guard and Prompt Guard. README table: **Code Shield is MIT**.

1. Llama Guard 3 input/output moderation models (MLCommons hazard taxonomy, including cyber and code-interpreter abuse in the README).
2. Prompt Guard classifier for prompt injection and jailbreaks.
3. Code Shield inference-time filter for insecure code suggestions.
4. CyberSec Eval benchmarks (README section).
5. System-level safeguard **models**, not an application policy engine.

Classifiers are a different control from deterministic rule IDs. Out of scope for a CPU, offline, no-new-model demo.

### 14. invariantlabs-ai/invariant

467 stars. Pushed **2026-01-12**. Apache-2.0. Python.

1. Rule language over agent traces (Python-like `raise ... if`).
2. Flow rules across tool calls (example: `get_inbox` then `send_email` to an outside domain).
3. Gateway mode in front of MCP or an LLM (points at `invariantlabs-ai/invariant-gateway`).
4. In-process `invariant-ai` evaluation on a local trace.
5. Rules can match message content or tool arguments.

Small, stale, and the closest public analog to “policy over a tool sequence.” It does not witness external state after the call. Worth citing. Not worth vendoring a dormant rule VM into the umbrella.

## Bucket C — human approval and effect verification

### 15. humanlayer/humanlayer

11,664 stars. Pushed 2026-06-19. Apache-2.0.

The current README is one paragraph: the code in the repo is **deprecated**, and the rebuild is at humanlayer.com. This pass did not review the historical tree. **No killer-feature list is claimed**, because the README no longer describes a living implementation.

Finding: the best-known open-source “human in the loop for agents” repo has left GitHub as a product. KarmaSakshi’s grant + witness is not redundant with a healthy OSS effect protocol. It is redundant with **building another approval inbox**. KarmaSakshi already has the Control Center.

## Bucket D — coding harnesses, AGENTS.md, sandboxes

### 16. OpenHands/OpenHands

90,108 stars. Pushed 2026-10-06. MIT. The README’s product name is now **Agent Canvas** (status badge: beta).

1. Self-hosted control center for coding agents and automations.
2. Backends: local, Docker, VM, cloud. README warns the no-sandbox install gives the agent full filesystem access.
3. ACP: OpenHands, Claude Code, Codex, Gemini, or any ACP agent.
4. Automations on a schedule or webhook (Slack, GitHub, Linear named in the README).
5. Bring-your-own model.

A place to **run** coding agents. Not a proof that a refund matched a seal.

### 17. aaif-goose/goose

55,008 stars. Pushed 2026-10-06. Apache-2.0. Rust. Agentic AI Foundation (Linux Foundation). Previously `block/goose`.

1. Local desktop app, CLI, and API.
2. README: 15+ model providers.
3. README: 70+ extensions via MCP.
4. Custom distributions (preconfigured providers and extensions).
5. Runs on the user’s machine, not only as a cloud job.

Same conclusion as OpenHands: an agent runtime, not an evidence chain.

### 18. openai/codex

128,044 stars. Pushed 2026-10-06. Apache-2.0. Rust.

1. Local coding-agent CLI.
2. IDE installs (VS Code, Cursor, Windsurf named).
3. Desktop app (`codex app`).
4. Installers for macOS/Linux and Windows; npm and Homebrew also documented.
5. README separates this CLI from Codex Web (the cloud agent).

The README excerpt reviewed here does not describe an effect witness or a golden-suite CI gate. Do not compete with Codex.

### 19. agentsmd/agents.md

24,791 stars. Pushed 2026-09-10. MIT.

1. A plain-markdown convention: predictable instructions for coding agents.
2. Sample sections for dev environment, tests, and PRs.
3. A website and a small renderer (repo language is TypeScript).
4. Intentionally simple. No runtime.
5. Wide adoption as a **file format**, which is why CodeGovernor’s ADR 0003 exists.

`AGENTS.md` is guidance. CodeGovernor’s recorded run 1 (`pip3 install` despite the prompt) is the local proof that the file does not bind the model. The umbrella should keep treating markdown rules as non-enforcing.

### 20. e2b-dev/E2B

14,200 stars. Pushed 2026-10-06. Apache-2.0.

1. Sandboxes for AI-generated code.
2. JavaScript and Python SDKs.
3. Code interpreter and desktop “computer use” quickstarts.
4. Cloud control path (API key required in the quickstart).
5. A self-hosting section in the README.

Isolation for generated code. It does not decide whether a payment matched an approval. Out of scope for the offline demo (the demo must not need E2B).

## What nobody in this set publishes

Across the READMEs reviewed, no project claims all four of:

1. a deterministic policy decision with a stable rule ID,
2. a human seal of the **exact** effect (not the tool name),
3. an independent re-read of the system of record,
4. that failure, after a human approval, as a CI golden case.

Langfuse and Phoenix come closest to “one place for traces and scores.” Promptfoo, DeepEval, and Inspect come closest to “CI for behavior.” NeMo, Guardrails, Invariant, and Portkey come closest to “stop a bad call.” HumanLayer’s public repo no longer documents approval. Coding harnesses stop at the agent loop.

KarmaSakshi plus AgentEval already cover (2), (3), and a demo of (4). CodeGovernor covers (1) for coding tools only. The umbrella’s job is to make (1)–(4) one artifact. It is not to out-metric DeepEval or out-trace Langfuse.
