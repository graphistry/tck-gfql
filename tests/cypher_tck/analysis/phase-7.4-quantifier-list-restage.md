# Phase 7.4 Quantifier/List Restage Plan

## Goal
Expand quantifier/list coverage in vector-safe slices while preserving strict-pure failfast behavior.

## Restaged Steps

### 7.4.A - Range + slice fundamentals
- Add constrained lowering/evaluation support for `range()` and list slicing forms.
- Validate with list feature families (`List11`, `List2` subsets).

### 7.4.B - Quantifier truth-table stabilization
- Align null semantics for quantifier outcomes in selected failing scenarios.
- Add focused regression tests for `quantifier6/7/8` edge cases.

### 7.4.C - Constrained list-comprehension lowering pilot
- Implement a narrow `[x IN list WHERE pred | proj]` subset.
- Preserve failfast for nested/unsupported subexpressions.

## Exit Conditions
1. Quantifier/list semantic pass count increases without impure growth.
2. strict-pure `select_local_projection/with_local_projection` counts decline for quantifier/list feature paths.
3. No regressions in pygraphistry `unwind/where_rows/group_by` tests.
