# Phase 7.8 Post-Wave Gap Inventory

Date: 2026-05-11
Branch: `main`
Source: `python3 -m tests.cypher_tck.report`

## Current checkpoint
- Scenarios represented: `3627`
- GFQL translated: `2938` (`81.0%`)
- Status counts: `2837 supported`, `790 xfail`, `0 skip`
- Purity split: `supported_semantic=2837`, `supported_pure=2837`, `supported_impure=0`
- Direct Cypher total snapshot: `2820 / 3627` (`77.8%`)
- Direct Cypher non-validation debt: `38`

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
| Expression long tail | 147 | P3 | big-swath | #51 |
| Other read-only gaps | 84 | P3 | big-swath | #52 |
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

Current split remains `34 success_wrong_rows` and
`4 unexpected_success_expected_error`. The focused details suggest the debt is
not one uniform class:

| likely class | keys | note |
|---|---:|---|
| Numeric/string/display normalization | 18 | Float exponent and integer/float rendering, string escaping, quote rendering, map key order, label order. Examples: `expr-aggregation3-1`, `expr-literals5-5`, `expr-literals6-5`, `expr-literals7-18`, `expr-typeconversion4-2`, `match3-7`. These are plausible repo-side oracle normalization candidates before pygraphistry semantics work. |
| Row-shape or post-aggregation alias mismatch | 3 | `expr-list12-3`, `return2-10`, `return2-9`. These need careful oracle-vs-runtime inspection; at least two involve `__cypher_postagg__` leaking instead of expected aliases. |
| Pattern/string/match semantic mismatch | 13 | Duplicate or missing rows for pattern predicates, string trim/newline cases, relationship expansion, and WITH join. Examples: `expr-pattern1-13`, `expr-string10-5`, `match5-25`, `with2-1`. Treat as likely pygraphistry-side until proven otherwise. |
| Expected-error contract drift | 4 | `expr-list1-6-4`, `expr-typeconversion4-10-1`, `expr-typeconversion4-10-2`, `match-where1-10`. One case now passes expected oracle; these need a promotion/error-contract audit. |

High-return repo-only follow-up:
- First inspect the normalization bucket and update row normalization only if
  the TCK oracle contract supports canonical equivalence. This could retire a
  subset of wrong-row debt without pygraphistry changes.
- Do not promote pattern/string/match mismatch cases based only on display
  similarity; they include missing/duplicate rows and should stay semantic
  until a targeted proof says otherwise.
- Audit `match-where1-10` separately because the focused command reports
  `passes expected oracle` while the contract bucket still says
  `unexpected_success_expected_error`.

## Next useful work
- Keep dependency/preflight failures explicit so contributors do not debug stale
  pygraphistry installs as TCK failures.
- Next low-risk slice is direct-Cypher normalization audit on the likely
  display-only cases, especially float exponent formatting and string/label
  canonicalization.
- Prefer small P1 slices in row-pipeline read forms or grouped aggregates after
  the editable pygraphistry environment is available.
- Treat write clauses, CALL/procedures, and broad expression-tail work as lower
  ROI unless product needs change.
