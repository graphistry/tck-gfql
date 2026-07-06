# Phase 7.3 SELECT/WITH Restage Plan

## Goal
Reduce `select_local_projection` / `with_local_projection` blockers without introducing non-vector fallback into strict-pure credit path.

## Restaged Steps

### 7.3.A - Constant + literal expression expansion
- Expand deterministic constant folding and literal conversion in `_select_items_to_gfql`.
- Keep fold scope bounded to 0/1-row frames.
- Validate on expression literal/precedence families.

### 7.3.B - Safe function-string lowering
- Support explicit lowering for currently vector-safe pygraphistry row functions.
- Reject unsupported functions early to preserve failfast.
- Validate on type-conversion and list/map literal scenarios.

### 7.3.C - Aggregation projection pilot (constrained)
- Allow selected `agg + scalar` projections when group keys are explicit and resolvable.
- No broad aggregate expression parser in this slice.
- Validate on targeted `return6-*` / `with6-*` families.

## Exit Conditions
1. `select_local_projection` count decreases materially from 580 baseline.
2. No increase in `supported_impure`.
3. pygraphistry GFQL suites stay green.
