# Changelog

All notable changes to the tck-gfql project are documented in this file. The PyGraphistry client and other Graphistry components are tracked in the main [Graphistry major release history documentation](https://graphistry.zendesk.com/hc/en-us/articles/360033184174-Enterprise-Release-List-Downloads).

The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and all breaking changes are explictly noted here.

## [Development]
<!-- Do Not Erase This Section - Used for tracking unreleased changes -->

### Added
- **Direct-Cypher row promotion (`with2-1` WITH-pipelined join)**: Promoted `with2-1` from `success_wrong_rows` to `success_matches_expected`, emptying the direct-Cypher wrong-row bucket and dropping tracked non-validation debt to 1. The residual was a fixture-modeling artifact, not a pygraphistry join bug: `graph_fixture_from_create` stringified the `a.id` property reference in the ported `CREATE (:Begin {num: a.id})` setup and conflated the Cypher `id` property with the synthetic node-identity column. Replaced the `with2-1` fixture with an explicit `GraphFixture` and moved the key to the promoted-tolerant row-pipeline tranche-3 lane contract (tck-gfql#115).
- **Direct-Cypher error promotions (`range()` invalid arguments)**: Promoted the 26 `expr-list11-4-*` / `expr-list11-5-*` *"Fail on invalid arguments for `range()`"* scenarios from `xfail` to `supported` as expected-error cases — pygraphistry's direct-Cypher path correctly raises for invalid `range()` arguments/types. Added parametrized positive/negative regression coverage in `test_tck_runner.py` and widened the expression-long-tail lane contract to accept direct-Cypher error promotions (tck-gfql#108 cluster 2).
- **Direct-Cypher expected-error rebaseline**: Removed `expr-list1-6-4` from `unexpected_success_expected_error` non-validation debt after pygraphistry #1450 restored scalar-string integer subscript rejection.
- **Direct-Cypher pattern predicate rebaseline correction**: Restored `expr-pattern1-{10,13,18}` to `success_wrong_rows` tracking after current pygraphistry master still returns wrong rows for those pattern predicate residuals.
- **Direct-Cypher row promotions (escaped string literal contract)**: Promoted `expr-literals6-5` from `success_wrong_rows` to `success_matches_expected` after current pygraphistry direct-Cypher string literal parity.
- **Direct-Cypher row promotions (comparison/list/null contract)**: Promoted `expr-list12-3` after pygraphistry #1367 fixed empty optional-match post-aggregate list-comprehension projection.
- **Direct-Cypher row promotions (current pygraphistry compatibility)**: Promoted `return2-10` after current pygraphistry main began returning the expected empty-graph aggregate boolean row.
- **Direct-Cypher row promotions (zero-hop match contract)**: Promoted `match5-8` after pygraphistry #1443 fixed exact zero-hop `*0..0` Cypher relationship semantics for #1369/#1353.
- **Direct-Cypher row promotions (string/typeconversion contract)**: Extended `parse_cypher` string literal handling, promoted `expr-literals6-4`, `expr-string8-{4,5}`, `expr-string9-{4,5}`, `expr-string10-{4,5}` to `success_matches_expected`, and rebaselined the related lane/contract/report assertions (PR #104).
- **Direct-Cypher row promotions (map-key-order)**: Allowlisted map-key-order row-normalization; promoted `expr-literals7-18` and `expr-literals8-18` to `success_matches_expected` (PR #102).
- **Direct-Cypher row promotions (label-order)**: Allowlisted label-order row-normalization for node labels; promoted `match3-7` (PR #101).
- **Direct-Cypher row promotions (nested numeric literals)**: Allowlisted nested numeric container normalization for simple list/map displays; promoted `expr-literals7-7` and `expr-literals8-11` (PR #100).
- **Direct-Cypher row promotions (string keywords)**: Allowlisted `toString(boolean)` string-keyword row normalization (recurses through lists); promoted `expr-typeconversion4-{2,3,4,5}` (PR #99).
- **Direct-Cypher graph-id success oracle**: Added harness support for direct-Cypher success cases whose expected oracle is node/edge ids rather than row dicts; promoted `match-where1-10` (PR #98).
- **Direct-Cypher row promotions (numeric formatting)**: Allowlisted numeric row-equivalence for audited float-format mismatches; promoted `expr-aggregation3-1` and `expr-literals5-{5,6,11,12,25,26}` (PR #97).
- **Direct-Cypher non-validation taxonomy**: Phase 7.8 analysis docs classify remaining non-validation debt into normalization/row-shape/semantic/expected-error buckets (PR #96).
- **Direct-Cypher non-validation detail command**: `python -m tests.cypher_tck.sweep_direct_cypher --show-nonvalidation-debt [--nonvalidation-limit N]` prints expected bucket + current pass/detail for tracked non-validation xfails (PR #95).
- **Full TCK harness module preflight**: `./bin/ci.sh` now fails fast when `graphistry.gfql.ref.enumerator` or `graphistry.tests.test_compute` are missing, with editable-install guidance (PR #94).
- **Parser preflight guard tests**: Static guards in `test_workflow_action_versions.py` pin the row-pipeline + parser-backend + full-harness module preflight in `bin/ci.sh` and `PYGRAPHISTRY_INSTALL=1` editable-install guidance in docs (PR #93).
- **Direct-Cypher CI preflight**: Added `test_direct_cypher_contract_fastfail.py` and wired `./bin/ci.sh` to run it before the full suite so sibling-target non-validation outcome drift fails early with key-level diagnostics (PR #88).
- **CI guardrails**: Added `test_workflow_action_versions.py` to enforce minimum GitHub Action major versions in `ci.yml` and `nightly.yml` (`checkout>=v6`, `setup-python>=v6`, `setup-uv>=v7`).
- **CI observability**: Added a non-blocking `CI observability summary` step to `ci.yml` and `nightly.yml` that runs `python -m tests.cypher_tck.report` on every run (`if: always()`) and appends conformance/lane metrics to GitHub step summaries.
- **TCK contract**: Promoted `match5-21..24` to `success_matches_expected` — multi-hop connected patterns with row bindings now pass (pygraphistry #973).
- **TCK contract**: Added `match5-25/26` as `success_wrong_rows` — multi-hop open-range connected patterns return rows but with wrong values (pygraphistry #973).
- **TCK contract**: Added `match5-16/17/18`, `with-where1-2`, `with-where7-1/3` to `success_matches_expected` — these now pass against updated pygraphistry main.
- **TCK contract**: Promoted `with-orderby1-31-{1..3}`, `with-orderby1-32-{1..2}`, `with-orderby2-7-{1..3}`, and `with-orderby3-2-{1..6}` from `success_wrong_rows` to `success_matches_expected` (issue #36).
- **TCK contract**: Promoted `expr-temporal7-{1..5}-{1,2}` from `success_wrong_rows` to `success_matches_expected` after expected-row placeholder correction (issue #38).
- **Strict-pure regressions**: Added standing-gate tests for `return6-6` and `return6-19` in `test_plan_executor_strict_pure_regressions.py`.
- **Lane trackers**: Added concrete tracker issues for top read-lane families and wired priority metadata to issues `#43`, `#44`, and `#45`.
- **Row-pipeline lane contracts**: Added tranche-1 TCK-only guardrails (`tests/cypher_tck/lane_contracts.py`, `tests/cypher_tck/test_lane_contracts.py`) covering key existence, status/tag contract, family classification, and tracker wiring for issue `#43`.
- **Grouped-aggregate lane contracts**: Added tranche-1 TCK-only guardrails for issue `#45` in lane contract tests (key existence, status/tag contract, family classification, and tracker wiring).
- **Optional/null lane contracts**: Added tranche-1 TCK-only guardrails for issue `#44` in lane contract tests (key existence, status/tag contract, family classification, and tracker wiring).
- **Lane tracker backlog coverage**: Added concrete tracker issues for remaining priority lanes and wired refs in `gap_priority.py`: expression long-tail `#51`, residual read-only gaps `#52`, procedures/CALL `#53`, and write clauses `#54`.
- **Expression long-tail lane contracts**: Added tranche-1 TCK-only guardrails for issue `#51` (List11 + Precedence2 key inventory) in lane contract tests covering key existence, status/tag contract, family classification, and tracker wiring.
- **Expression long-tail lane contracts**: Added tranche-2 TCK-only guardrails for issue `#51` (Temporal4 + Aggregation6 key inventory) in lane contract tests covering key existence, status/tag contract, and family classification.
- **Expression long-tail lane contracts**: Added tranche-3 TCK-only guardrails for issue `#51` (Temporal8 key inventory) in lane contract tests covering key existence, status/tag contract, and family classification.
- **Direct-Cypher contract cleanup**: Promoted 47 prior `success_matches_expected` xfail keys into direct-Cypher row support snapshot and removed them from non-validation xfail debt tracking.
- **Residual read-only lane contracts**: Added tranche-1 TCK-only guardrails for issue `#52` (variable-length + named-path anchor inventory) in lane contract tests covering key existence, status/tag contract, family classification, and tracker wiring.
- **Write-clauses lane contracts**: Added tranche-1 TCK-only guardrails for issue `#54` (cross-clause anchor inventory spanning CREATE/MERGE/SET/DELETE/REMOVE) in lane contract tests covering key existence, status/tag contract, family classification, and tracker wiring.
- **Procedures/CALL lane contracts**: Added tranche-1 TCK-only guardrails for issue `#53` (registry/invocation/YIELD anchors) in lane contract tests covering key existence, status/tag contract, family classification, and tracker wiring.
- **Priority lane tranche expansion**: Added tranche-2 contract guardrails for row-pipeline `#43`, optional/null-extension `#44`, and grouped-aggregate `#45`, plus tranche-4 expression-long-tail guardrails for `#51`.
- **Report drift guardrails**: Added explicit lane-count stability assertions in `test_report.py` for row-pipeline, optional/null-extension, grouped-aggregate, and expression-long-tail families.
- **Priority lane tranche expansion (round 2)**: Added tranche-3 row-pipeline `#43`, tranche-3 optional/null `#44`, tranche-3 grouped-aggregate `#45`, and tranche-5 expression-long-tail `#51` contract guardrails.
- **Contract process guards**: Added tranche disjointness tests per lane family to catch contract overlap/regression drift.
- **Optional/null lane contracts**: Added tranche-4 guardrails for `#44`, completing TCK contract coverage for the optional/null lane key inventory.
- **Expression long-tail lane contracts**: Added tranche-6 TCK-only guardrails for `#51` (Literals5 + Null3 + Precedence3 + TypeConversion4 inventory) in lane contract tests covering key existence, status/tag contract, family classification, and tranche disjointness.
- **Row-pipeline lane contracts**: Added tranche-4 TCK-only guardrails for `#43` (Quantifier11 expression residual cluster) in lane contract tests covering key existence, status/tag contract, family classification, and tranche disjointness.
- **Coverage-floor guards**: Added non-decreasing contract coverage floor tests for open lanes `#43` (row-pipeline floor 59) and `#51` (expression long-tail floor 135).
- **Row-pipeline lane contracts**: Added tranche-5 TCK-only guardrails for `#43` (Quantifier12 expression residual cluster) and raised row-pipeline coverage floor to `74`.
- **Row-pipeline lane contracts**: Added tranche-6 TCK-only guardrails for `#43` (Quantifier9 expression residual cluster) and raised row-pipeline coverage floor to `89`.
- **Row-pipeline lane contracts**: Added tranche-7 TCK-only guardrails for `#43` (Temporal8 expression residual cluster) and raised row-pipeline coverage floor to `104`.
- **Row-pipeline lane contracts**: Added tranche-8 TCK-only guardrails for `#43` (Temporal5 expression residual cluster) and raised row-pipeline coverage floor to `111`.
- **Row-pipeline lane contracts**: Added tranche-9 TCK-only guardrails for `#43` (Map1 expression residual cluster) and raised row-pipeline coverage floor to `117`.
- **Row-pipeline lane contracts**: Added tranche-10 TCK-only guardrails for `#43` (Quantifier10 expression residual cluster) and raised row-pipeline coverage floor to `122`.
- **Row-pipeline lane contracts**: Added tranche-11 TCK-only guardrails for `#43` (Comparison1 expression residual cluster) and raised row-pipeline coverage floor to `126`.
- **Row-pipeline lane contracts**: Added tranche-12 TCK-only guardrails for `#43` (Comparison2 expression residual cluster) and raised row-pipeline coverage floor to `130`.
- **Row-pipeline lane contracts**: Added tranche-13 TCK-only guardrails for `#43` (List1 expression residual cluster) and raised row-pipeline coverage floor to `134`.
- **Row-pipeline lane contracts**: Added tranche-14 TCK-only guardrails for `#43` (final residual sweep, 24 keys) and raised row-pipeline coverage floor to `158` (full row-pipeline lane contract coverage).
- **Expression long-tail lane contracts**: Added tranche-7 TCK-only guardrails for `#51` (Quantifier7 + ExistentialSubquery1/3 + List5/List6 residual bundle, 20 keys) and raised expression coverage floor to `155`.
- **Expression long-tail lane contracts**: Added tranche-8 TCK-only guardrails for `#51` (List12 + Literals6/7/8 + Path2 + String10 residual bundle, 12 keys) and raised expression coverage floor to `167`.
- **Expression long-tail lane contracts**: Added tranche-9 TCK-only guardrails for `#51` (final residual sweep, 9 keys) and raised expression coverage floor to `176`.
- **Direct-Cypher xfail contract**: Rebased current sibling-target outcomes for newly executing xfail scenarios: promoted `match-where3-3`, `match3-1`, `match3-5`, `match4-3`, and `expr-pattern1-{12,14,15,16,17}` to `success_matches_expected`; tracked `match3-7`, `with-where3-3`, and `expr-pattern1-{13,18}` as `success_wrong_rows`.
- **Direct-Cypher xfail contract**: Updated sibling-target drift snapshot for `with-where3-3` from `success_wrong_rows` to `success_matches_expected`.
- **Direct-Cypher xfail contract**: Updated sibling-target drift snapshot for `expr-temporal2-6-5` from `success_wrong_rows` to `success_matches_expected`.
- **Direct-Cypher xfail contract**: Updated sibling-target drift snapshot for `expr-comparison1-6-5` from `success_wrong_rows` to `success_matches_expected`.
- **Direct-Cypher xfail contract**: Updated sibling-target drift snapshot for `expr-comparison1-7-12` from `success_wrong_rows` to `success_matches_expected`.
- **Direct-Cypher xfail contract**: Updated sibling-target drift snapshot for `expr-comparison1-7-{13,14,15,16}` from `success_wrong_rows` to `success_matches_expected`.
- **Direct-Cypher xfail contract**: Updated sibling-target drift snapshot for `expr-list3-7` from `success_wrong_rows` to `success_matches_expected`.
- **Direct-Cypher xfail contract**: Updated sibling-target drift snapshot for `expr-precedence3-6-{1,2}` from `GFQLValidationError` to `success_matches_expected`.
- **Direct-Cypher xfail contract**: Updated sibling-target drift snapshot for `expr-list5-21` from `success_wrong_rows` to `success_matches_expected`.
- **Direct-Cypher xfail contract**: Updated sibling-target drift snapshot for `expr-list5-{29,31,34}` from `success_wrong_rows` to `success_matches_expected`.
- **Direct-Cypher xfail contract**: Updated sibling-target drift snapshot for `expr-null{1,2}-3` from `success_wrong_rows` to `success_matches_expected`.

### Changed
- **Cypher clause splitter**: `scenarios._CLAUSE_RE` now also matches clause keywords mid-line preceded by whitespace, so `ORDER BY c SKIP 1` / `ORDER BY c LIMIT 1` lower into separate `order_by` + `skip`/`limit` steps. Affects `with-skip-limit1-2` and `with-skip-limit2-4` parsed plans (scenarios remain xfail pending row-pipeline match projection / grouped-aggregate semantics on the pygraphistry side).
- **Repo hygiene**: Gitignored `.claude/settings.local.json` (per-user permission allowlist) and `.claude/scheduled_tasks.lock` (per-session state) so local Claude Code use does not leak into `git status` (PR #103).
- **CI workflows**: Centralized shared runtime pins (`PYTHON_VERSION`, `UV_VERSION`, `UV_EXCLUDE_NEWER`) and added inline compatibility notes in `ci.yml` and `nightly.yml` to keep workflow behavior aligned.
- **CI workflows**: Upgraded GitHub Actions versions to Node24-era majors in `ci.yml` and `nightly.yml` (`actions/checkout@v6`, `actions/setup-python@v6`, `astral-sh/setup-uv@v7`) to avoid pending Node20 deprecation breakage.
- **TCK xfail reason**: Updated `unwind1` scenario reason to reflect the multi-alias row-scope limitation that replaced the old parser/lowering block.
- **Scenario parsing**: `parse_cypher` now preserves nested list/map literals in fixture properties instead of stringifying them.
- **Row assertion semantics**: with-orderBy scenarios now honor explicit openCypher `in order` vs `in any order` expectation metadata (fallback heuristic retained for non-annotated scenarios).
- **Temporal7 scenario data**: Fixed outline expansion artifact where expected rows retained literal `<gt>` instead of substituted boolean values in 10 temporal comparison cases.
- **Direct-Cypher promotion contract**: Removed stale `match-where1-10` row-promotion marker so promotion snapshot aligns with status-tagged support.
- **Direct-Cypher parity guard**: Added test coverage that enforces promotion-snapshot/status-tag parity and report-tracker assertion alignment.
- **Report ownership split**: Added an `Ownership split (heuristic)` section to `tests.cypher_tck.report` distinguishing issue-backed lane follow-up from TODO-tracked planning/backlog debt.

## [0.1.1 - 2026-01-03]

### Added
- **Docs**: Expanded `DEVELOP.md` with local run helpers, environment variables, and CI notes.

## [0.1.0 - 2026-01-03]

### Added
- **GFQL plans**: Auto-generate clause + expression plans for target extension xfail scenarios (table ops + expr DSL).
- **GFQL plan DSL**: Added expression AST helpers (`col`, `lit`, `param`, `func`, `binary`, `unary`, `list`, `map`, `index`, `star`) for non-executable plan capture.
- **Docs**: Documented generated xfail plans and plan helpers in `tests/cypher_tck/README.md`.

### Changed
- **GFQL plan generation**: Expanded target expr coverage to include map and type conversion buckets.
