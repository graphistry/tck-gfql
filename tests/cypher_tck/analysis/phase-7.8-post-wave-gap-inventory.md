# Phase 7.8 Post-Wave Gap Inventory

Date: 2026-05-11
Branch: `main`
Source: `python3 -m tests.cypher_tck.report`

## Current checkpoint
- Scenarios represented: `3627`
- GFQL translated: `2938` (`81.0%`)
- Status counts: `2849 supported`, `778 xfail`, `0 skip`
- Purity split: `supported_semantic=2849`, `supported_pure=2849`, `supported_impure=0`
- Direct Cypher total snapshot: `2832 / 3627` (`78.1%`)
- Direct Cypher non-validation debt: `26`

## Remaining supported-but-impure keys
- None in the live report.

The old Phase 7.8 checkpoint tracked `10` supported-but-impure keys. Those are
now counted as pure by the report, so the next work should not target a generic
impure burn-down. Keep using focused strict-pure regression tests as a guardrail,
because local pygraphistry compatibility can still expose fallback paths.

## Current xfail families
| family | xfail | priority | class | tracker |
|---|---:|---|---|---|
| Write clauses | 277 | P3 | big-swath | #54 |
| Row-pipeline read forms | 157 | P1 | common-read-form | #43 |
| Expression long tail | 136 | P3 | big-swath | #51 |
| Other read-only gaps | 83 | P3 | big-swath | #52 |
| OPTIONAL MATCH / collect / null extension | 62 | P2 | common-read-form | #44 |
| Procedures / CALL | 37 | P4 | niche-tck | #53 |
| Grouped aggregates over expanded MATCH | 26 | P1 | common-read-form | #45 |

## Local pygraphistry compatibility note
- Default local import on this machine was `graphistry v0.45.4` from
  `/usr/local/lib/python3.12/dist-packages`, which is too old for this harness.
- `./bin/ci.sh` now preflights the required `graphistry.compute` row-pipeline
  symbols, full TCK harness modules, and GFQL row expression parser backend
  before pytest collection.
- A sibling checkout at `/home/lmeyerov/Work/pygraphistry` exposes the required
  API surface. Source-only `PYTHONPATH` mode can still fail strict row-expression
  delegation when pygraphistry dependencies such as `lark` are not installed.
- Use `PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_PATH=/path/to/pygraphistry ./bin/ci.sh`
  for sibling-checkout validation so editable pygraphistry dependencies are
  installed.

## Direct Cypher non-validation taxonomy
Source command:
`python -m tests.cypher_tck.sweep_direct_cypher --show-nonvalidation-debt`

Current split is `23 success_wrong_rows` and
`3 unexpected_success_expected_error`. The focused details suggest the debt is
not one uniform class:

| likely class | keys | note |
|---|---:|---|
| Numeric/string/display normalization | 7 | String escaping, map key order, label order, and remaining display-style mismatches. Examples: `expr-literals6-5`, `expr-literals7-18`, `expr-literals7-7`, `match3-7`. Seven integer/float and exponent-formatting cases were promoted by the Step 17 numeric-equivalence slice; four `toString(boolean)` string-keyword rendering cases were promoted by the string-keyword slice. |
| Row-shape or post-aggregation expression mismatch | 3 | `expr-list12-3`, `return2-10`, `return2-9`. Direct inspection showed these are not safe alias-only harness fixes: the runtime returns an unevaluated post-aggregation value/list or a different row cardinality. |
| Pattern/string/match semantic mismatch | 13 | Duplicate or missing rows for pattern predicates, string trim/newline cases, relationship expansion, and WITH join. Examples: `expr-pattern1-13`, `expr-string10-5`, `match5-25`, `with2-1`. Treat as likely pygraphistry-side until proven otherwise. |
| Expected-error contract drift | 3 | `expr-list1-6-4`, `expr-typeconversion4-10-1`, `expr-typeconversion4-10-2`. `match-where1-10` now promotes via the direct-Cypher graph-id oracle after the runner learned to validate node/edge IDs for string-query promotions. |

High-return repo-only follow-up:
- The remaining `unexpected_success_expected_error` cases are runtime-error
  semantic gaps where direct Cypher executes despite an expected runtime error;
  keep them as debt until pygraphistry/runtime-error semantics change.
- Next inspect the remaining normalization bucket and update row normalization
  only if the TCK oracle contract supports canonical equivalence.
- Do not promote pattern/string/match mismatch cases based only on display
  similarity; they include missing/duplicate rows and should stay semantic
  until a targeted proof says otherwise.

## Next useful work
- Keep dependency/preflight failures explicit so contributors do not debug stale
  pygraphistry installs as TCK failures.
- Next low-risk slice is the remaining display-only cases such as string/label
  canonicalization, or the post-aggregation alias/row-shape audit.
- Prefer small P1 slices in row-pipeline read forms or grouped aggregates after
  the editable pygraphistry environment is available.
- Treat write clauses, CALL/procedures, and broad expression-tail work as lower
  ROI unless product needs change.
