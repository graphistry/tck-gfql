# Phase 7.8 Post-Wave Gap Inventory

Date: 2026-05-10
Branch: `main`
Source: `python3 -m tests.cypher_tck.report`

## Current checkpoint
- Scenarios represented: `3627`
- GFQL translated: `2938` (`81.0%`)
- Status counts: `2811 supported`, `816 xfail`, `0 skip`
- Purity split: `supported_semantic=2811`, `supported_pure=2811`, `supported_impure=0`
- Direct Cypher total snapshot: `2794 / 3627` (`77.0%`)
- Direct Cypher non-validation debt: `64`

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
| Expression long tail | 166 | P3 | big-swath | #51 |
| Row-pipeline read forms | 158 | P1 | common-read-form | #43 |
| Other read-only gaps | 88 | P3 | big-swath | #52 |
| OPTIONAL MATCH / collect / null extension | 64 | P2 | common-read-form | #44 |
| Procedures / CALL | 37 | P4 | niche-tck | #53 |
| Grouped aggregates over expanded MATCH | 26 | P1 | common-read-form | #45 |

## Local pygraphistry compatibility note
- Default local import on this machine was `graphistry v0.45.4` from
  `/usr/local/lib/python3.12/dist-packages`, which is too old for this harness.
- `./bin/ci.sh` now preflights the required `graphistry.compute` row-pipeline
  symbols before pytest collection.
- A sibling checkout at `/home/lmeyerov/Work/pygraphistry` exposes the required
  API surface, but focused strict-pure tests still showed local fallback
  failures for `order_by_local_eval`, `unwind_local_row_loop`, and
  `where_local_eval`.

## Next useful work
- Keep dependency/preflight failures explicit so contributors do not debug stale
  pygraphistry installs as TCK failures.
- Prefer small P1 slices in row-pipeline read forms or grouped aggregates.
- Treat write clauses, CALL/procedures, and broad expression-tail work as lower
  ROI unless product needs change.
