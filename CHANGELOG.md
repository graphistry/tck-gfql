# Changelog

All notable changes to the tck-gfql project are documented in this file. The PyGraphistry client and other Graphistry components are tracked in the main [Graphistry major release history documentation](https://graphistry.zendesk.com/hc/en-us/articles/360033184174-Enterprise-Release-List-Downloads).

The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and all breaking changes are explictly noted here.

## [Development]
<!-- Do Not Erase This Section - Used for tracking unreleased changes -->

### Added
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
- **Direct-Cypher xfail contract**: Rebased current sibling-target outcomes for newly executing xfail scenarios: promoted `match-where3-3`, `match3-1`, `match3-5`, `match4-3`, and `expr-pattern1-{12,14,15,16,17}` to `success_matches_expected`; tracked `match3-7`, `with-where3-3`, and `expr-pattern1-{13,18}` as `success_wrong_rows`.
- **Direct-Cypher xfail contract**: Updated sibling-target drift snapshot for `with-where3-3` from `success_wrong_rows` to `success_matches_expected`.

### Changed
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
