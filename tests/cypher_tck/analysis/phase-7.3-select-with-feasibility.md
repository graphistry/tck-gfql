# Phase 7.3 SELECT/WITH Feasibility Matrix

## Scope
Investigation of `select/with` strict-pure fallback drivers with emphasis on vector-safe lowering compatible with WHERE/disjunction work.

## Evidence Snapshot
- Probe: `PYTHONPATH=. pytest -q graphistry/tests/compute/gfql/test_row_pipeline_ops.py -k "select or with_"`
  - Result: `16 passed`
- Probe: `PYTHONPATH=/home/lmeyerov/Work/pygraphistry:/home/lmeyerov/Work/tck-gfql pytest -q tests/cypher_tck/test_tck_runner.py -k "return or with"`
  - Result: `162 passed, 305 xfailed`
- Strict-pure fallback inventory (all executable plan scenarios):
  - `select_local_projection`: `580`
  - `with_local_projection`: `167`

## Matrix

### Easy / High Predictability (do first)
1. Constant expression folding for 0/1-row frames (already partially in place; continue expanding expression forms).
2. Function-string lowering for row-expression-safe subset (`toBoolean`, `toString`, `coalesce`, arithmetic/comparison literals).
3. Alias/property rewrite stabilization where source columns are present and unambiguous.

### Medium (stage behind focused tests)
1. Mixed aggregate + scalar projection rewrites (`age + count(...)`) where implicit grouping occurs.
2. `WITH` carry-forward alias rewrites across multiple stages.
3. Map/list index projection when base/value types are stable.

### Defer (high risk / broad semantics)
1. Percentile aggregates and advanced aggregation functions not represented in pygraphistry row primitives.
2. Path/map projection flows requiring entity-level serialization parity.
3. Multi-clause optional/comma-MATCH coupled projection semantics.

## Recommendation
Prioritize a narrow `select/with` lift aligned with existing pygraphistry row-expression support and avoid broad aggregate-expression rewrites until WHERE/null tri-valued semantics are locked.
