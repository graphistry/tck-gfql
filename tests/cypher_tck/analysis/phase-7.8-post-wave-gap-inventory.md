# Phase 7.8 Post-Wave Gap Inventory

Date: 2026-03-03
Branch: `feat/return-pipeline-exec`

## Current checkpoint
- `supported_semantic`: `1343`
- `supported_pure`: `1333`
- `supported_impure`: `10`
- `pytest -q tests/cypher_tck/test_tck_runner.py`: `1343 passed, 2284 xfailed`

## Remaining supported-but-impure keys (10)
- `expr-aggregation8-2` (`match,select`)
- `return-orderby4-1` (`with,unwind,unwind,with,select,order_by`)
- `return-orderby6-1` (`match,rows,select,order_by`)
- `return-orderby6-2` (`match,rows,select,order_by`)
- `return-orderby6-3` (`match,rows,select,order_by`)
- `return-skip-limit2-5` (`match,rows,select,order_by,limit`)
- `return4-7` (`match,select`)
- `return6-18` (`match,with,select`)
- `return6-19` (`match,select`)
- `return6-6` (`match,select`)

## Strict-pure failure reason histogram (top)
- `select_local_projection`: `574`
- `with_local_projection`: `175`
- `order_by_local_eval`: `45`
- `comma-separated MATCH patterns are only supported for a single linear connected path`: `19`
- `unsupported plan step: create`: `19`
- `unwind_local_row_loop`: `6`
- `unbounded variable-length relationship patterns are not supported`: `4`

## Delta from start of Phase 7 wave
- Start (locked in plan): `1334 / 1302 / 32`
- Current: `1343 / 1333 / 10`
- Net: `+9 semantic`, `+31 pure`, `-22 impure`

## Notes on what moved in this wave
- Computed ORDER BY normalization (`ASCENDING`/`DESCENDING` suffix handling) unlocked additional `with-orderby*` scenarios.
- String constant-folding in strict-pure projection was adjusted to preserve literal semantics without regressing temporal function cases.
- Bounded variable-length MATCH compilation was added, but current conformance uplift from it is still limited by downstream projection/path semantics.
