# Phase 7.8 Next-Wave Plan

Date: 2026-05-10
Branch: `main`

## Objective
Move from the current `2844 supported / 783 xfail / 0 supported_impure`
checkpoint toward higher conformance without widening the blast radius. The
old `10 -> 0` supported-impure burn-down is complete in the live report; the
next useful slices are dependency hygiene, small P1 xfail promotions, and
direct-Cypher contract debt reduction.

## Ordered priorities

1. Pygraphistry dependency hygiene (done for this wave)
- Target: stale local installs that fail before pytest collection.
- Scope: keep `./bin/ci.sh` using `python3` when `python` is absent, run pytest
  through `python -m pytest`, and fail fast when `graphistry.compute` lacks the
  row-pipeline API or GFQL row expression parser backend required by
  `plan_executor.py`.
- Guardrails: do not mutate global Python or sibling pygraphistry checkouts from
  this repo; prefer explicit install commands such as
  `PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_PATH=/path/to/pygraphistry ./bin/ci.sh`.

2. Direct-Cypher expected-error drift audit
- Target: `4` tracked `unexpected_success_expected_error` direct-Cypher xfails.
- Current direct-Cypher non-validation debt: `31` total
  (`27 success_wrong_rows`, `4 unexpected_success_expected_error`).
- Scope: inspect each expected-error key with the focused detail command and
  promote or reclassify only cases whose current result matches the TCK oracle.

3. Remaining direct-Cypher display normalization
- Target: the remaining display-style subset inside `27 success_wrong_rows`.
- Scope: string escaping, quote rendering, map key order, and label order only
  when the oracle contract supports canonical equivalence. The integer/float
  and exponent-formatting slice was already promoted.

4. Row-pipeline read forms
- Target: `157` primary-family xfails, issue `#43`.
- Scope: tiny tranches only, especially shapes already represented by existing
  row-pipeline helpers (`WITH`, `ORDER BY`, `LIMIT`, `SKIP`, `UNWIND`).
- Guardrails: focused plan-executor tests must pass against an editable
  pygraphistry checkout with parser dependencies installed before broad
  promotion sweeps.

5. Grouped aggregates over expanded MATCH
- Target: `26` read-only relationship aggregate xfails, issue `#45`.
- Scope: small grouped count/rollup cases that avoid OPTIONAL MATCH, path
  materialization, writes, and CALL/procedure semantics.

6. Explicit defer list
- Write clauses (`CREATE`, `MERGE`, `SET`, `DELETE`, `REMOVE`) remain lower ROI
  for the current read-only harness.
- CALL/procedures remain niche and high risk.
- OPTIONAL MATCH/null extension and broad expression-tail work should be staged
  behind narrower read-form wins.

## Validation/quality loop (per slice)
- `python3 -m py_compile ...` on touched Python files.
- `bash -n bin/ci.sh` when shell scripts change.
- `python3 -m pytest -q ...` focused tests first.
- `PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_PATH=/path/to/pygraphistry ./bin/ci.sh`
  for full harness runs when a compatible local pygraphistry checkout is
  available.
- `python3 -m tests.cypher_tck.report` after each slice.
- Conformance and purity counts must be non-regressive unless the plan records
  an intentional contract correction.
