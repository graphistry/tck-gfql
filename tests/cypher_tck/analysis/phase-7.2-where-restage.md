# Phase 7.2 WHERE Null/Boolean Restage Plan

## Goal
Land null/boolean/disjunction improvements in predictable slices without introducing impurity or pandas/cudf drift.

## Restaged Steps

### 7.2.A - Tri-valued boolean core
- Add null-preserving boolean combiner helpers in pygraphistry row expression path.
- Replace `fillna(False)`-style coercion in logical `AND/OR/NOT` evaluation path where Cypher expects unknown (`null`).
- Validation:
  - `pytest -q graphistry/tests/compute/gfql/test_row_pipeline_ops.py -k "boolean or where_rows"`
  - `pytest -q tests/cypher_tck/test_tck_runner.py -k "boolean1 or boolean2 or null3"`

### 7.2.B - WHERE projection/resolution parity
- Expand alias/property resolution and null comparison behavior in `WITH ... WHERE ...` flows.
- Keep strict failfast on unresolved/mixed unsupported patterns.
- Validation:
  - `pytest -q tests/cypher_tck/test_tck_runner.py -k "with-where"`

### 7.2.C - Disjunction staging
- Enable selected nested disjunction forms after 7.2.A parity is stable.
- Do not enable XOR/IN-null edge families in this slice.
- Validation:
  - `pytest -q tests/cypher_tck/test_tck_runner.py -k "where and or"`

### Explicit Defers
- XOR truth-table family under null.
- IN/NOT IN null-heavy semantics.
- MATCH-shape-coupled WHERE families blocked by compiler scope.

## Gate for Promotion
Promote only when:
1. No new strict-pure impurity reasons in promoted keys.
2. Focused boolean/null scenario failures decrease without semantic regressions in previously passing keys.
3. pygraphistry GFQL suite remains green for row pipeline operations.
