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

### Changed
- **TCK xfail reason**: Updated `unwind1` scenario reason to reflect the multi-alias row-scope limitation that replaced the old parser/lowering block.

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
