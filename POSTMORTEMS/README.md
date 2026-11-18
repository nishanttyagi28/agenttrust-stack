# Postmortems

A postmortem is written after something that shipped was wrong, and it is
written by the person who shipped it. The point is not to perform accountability
— it is to record the **friction**: what was believed, how reality disagreed, and
what was changed so the same belief cannot survive again.

Generated code never produces these, because generation has no memory of being
wrong. That is why they live in the repo next to the tests.

## Template

```markdown
# NNNN: <one line, the wrong thing, stated plainly>

**Severity:** high | medium | low
**Affected:** <versions / files>
**Introduced:** <date>  **Found:** <date>  **Fixed:** <date> (<time to fix>)
**Time it existed undetected:** <duration>

## What we believed
The claim, in the words it was actually shipped in.

## What was true
The gap, stated without softening.

## How it was found
The specific action that exposed it. Not "review" — the command, the test, the
user report.

## Why it survived review / CI
The honest reason. If the answer is "the test suite checked the wrong thing",
say that.

## What changed
Commit + ADR links. Tests added, by name.

## What we did not fix
Remaining exposure, so the next reader is not misled by this document.

## What we would do differently
One or two sentences. If a process change, it goes in GOVERNANCE.md.
```

## Index

| # | Title | Severity | Existed for |
|---|---|---|---|
| [0001](0001-unsigned-evidence-chain.md) | The evidence chain was not tamper-evident | high | 44 days |
