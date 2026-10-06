# ADR 0004: Editable install and the CI evidence artifact

**Status:** Accepted  
**Date:** 2026-10-07

## Context

Four package roots each contain a slice of the `agenttrust` namespace (`evidence`, `importers`, `gate`, `ci`). setuptools `packages.find` with all four `where` directories resolved `agenttrust.evidence` under `packages/ci` and failed editable install with `package directory 'packages/ci/agenttrust/evidence' does not exist`.

Buyers also need one command and one downloadable proof. The green Actions run `37510342515` ran pytest and did not upload a chain.

## Decision

1. **Explicit package map.** `pyproject.toml` lists each import package and its directory. The `agenttrust` parent stays a namespace (no `agenttrust/__init__.py`).
2. **Entrypoints.** `python -m agenttrust.demo` and `agenttrust-demo` run the offline story and write the green chain. `python -m agenttrust.report CHAIN.json REPORT.html` and `agenttrust-report` render one HTML page.
3. **Artifact layout**, uploaded on every green `agenttrust` workflow run:
   - `evidence-pack/chain.json` — canonical green-path chain, trailing newline added for the file
   - `evidence-pack/report.html` — `render_html` of that same chain
4. **Version `0.1.0`**, classifier `Development Status :: 3 - Alpha`. The `Private :: Do Not Upload` classifier is removed. This ADR does not publish to PyPI.
5. **Install command:** `python -m pip install -e ".[dev,karmasakshi]"` on Python 3.12. KarmaSakshi stays `>=0.2,<0.3` and still requires Python `<3.14`.

## Alternatives considered

- **One merged `src/agenttrust` tree.** Rejected. Agent allowlists are per directory; merging them couples every slice.
- **Keep PYTHONPATH as the supported entry.** Rejected. It is how the 2026-10-06 demo was run, and it is not a buyer install.
- **Upload the deny chain as a second required file.** Rejected for this layout. Stdout still prints `red_exit`. The artifact is the shippable allow chain plus its page. Adding a second required filename later needs a new ADR.

## Consequences

CI fails if either artifact file is missing or empty. Local `evidence-pack/` is gitignored. Manifest hashes inside `chain.json` still change per run because KarmaSakshi `prepare` draws a nonce.
