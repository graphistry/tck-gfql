# Phase 7.8 Next-Wave Plan

Date: 2026-05-10
Branch: `main`

## Objective
Move from the current `2811 supported / 816 xfail / 0 supported_impure`
checkpoint toward higher conformance without widening the blast radius. The
old `10 -> 0` supported-impure burn-down is complete in the live report; the
next useful slices are dependency hygiene, small P1 xfail promotions, and
direct-Cypher contract debt reduction.

## Ordered priorities

1. Pygraphistry dependency hygiene (done for this wave)
- Target: stale local installs that fail before pytest collection.
- Scope: keep `./bin/ci.sh` using `python3` when `python` is absent, run pytest
  through `python -m pytest`, and fail fast when `graphistry.compute` lacks the
  row-pipeline API required by `plan_executor.py`.
- Guardrails: do not mutate global Python or sibling pygraphistry checkouts from
  this repo; prefer `PYGRAPHISTRY_PATH` or explicit install commands.

2. Direct-Cypher non-validation debt
- Target: `64` tracked non-validation xfails in the live report.
- Current split: `26 success_matches_expected`, `34 success_wrong_rows`,
  `4 unexpected_success_expected_error`.
- Scope: start with `success_matches_expected` because those are the safest
  candidates for metadata/status cleanup; do not promote wrong-row cases without
  row-diff analysis.

3. Row-pipeline read forms
- Target: `158` primary-family xfails, issue `#43`.
- Scope: tiny tranches only, especially shapes already represented by existing
  row-pipeline helpers (`WITH`, `ORDER BY`, `LIMIT`, `SKIP`, `UNWIND`).
- Guardrails: focused plan-executor tests must pass against a compatible
  pygraphistry checkout before broad promotion sweeps.

4. Grouped aggregates over expanded MATCH
- Target: `26` read-only relationship aggregate xfails, issue `#45`.
- Scope: small grouped count/rollup cases that avoid OPTIONAL MATCH, path
  materialization, writes, and CALL/procedure semantics.

5. Explicit defer list
- Write clauses (`CREATE`, `MERGE`, `SET`, `DELETE`, `REMOVE`) remain lower ROI
  for the current read-only harness.
- CALL/procedures remain niche and high risk.
- OPTIONAL MATCH/null extension and broad expression-tail work should be staged
  behind narrower read-form wins.

## Validation/quality loop (per slice)
- `python3 -m py_compile ...` on touched Python files.
- `bash -n bin/ci.sh` when shell scripts change.
- `python3 -m pytest -q ...` focused tests first.
- `PYGRAPHISTRY_PATH=/path/to/pygraphistry ./bin/ci.sh` for full harness runs
  when a compatible local pygraphistry checkout is available.
- `python3 -m tests.cypher_tck.report` after each slice.
- Conformance and purity counts must be non-regressive unless the plan records
  an intentional contract correction.
