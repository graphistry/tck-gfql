# Phase 7.2 WHERE Null/Boolean Feasibility Matrix

## Scope
Investigation for vectorized WHERE/null/boolean/disjunction behavior under strict-pure constraints (pandas + cudf compatibility target).

## Evidence Snapshot
- Probe: `PYTHONPATH=. pytest -q graphistry/tests/compute/gfql/test_row_pipeline_ops.py -k "where_rows"`
  - Result: `2 passed`
- Probe: `PYTHONPATH=/home/lmeyerov/Work/pygraphistry:/home/lmeyerov/Work/tck-gfql pytest -q tests/cypher_tck/test_tck_runner.py -k "where or boolean or null"`
  - Result: `48 passed, 197 xfailed`
- Strict-pure failure sampling shows dominant blockers in this area:
  - three-valued boolean semantics mismatch (`AND/OR/NOT` with `null`)
  - local projection fallback (`select_local_projection` / `with_local_projection`)
  - unsupported/high-risk forms (`XOR`, `IN` null edge cases, comma-match interactions)

## Matrix

### Can Add Now (predictable, vector-safe)
1. `IS NULL` / `IS NOT NULL` for scalar/property tokens in `WHERE` and projected boolean columns.
2. Binary comparison null propagation (`=`, `<>`, `<`, `<=`, `>`, `>=`) when either side is null.
3. Top-level `AND`/`OR` for scalar boolean expressions once three-valued mask handling is corrected.

### Add with Caution (needs staged validation)
1. Nested disjunctions (`(a OR b) AND c`) with null truth-table parity.
2. `NOT` over nullable boolean expressions (currently null collapses to false in several paths).
3. Alias/property resolution mixed with nullable values (`a.prop IS NULL` in chained `WITH ... WHERE ...`).

### Defer (high-risk / broad semantic surface)
1. Full `XOR` truth tables under null semantics.
2. `IN` / `NOT IN` with null-containing lists and parameterized collections.
3. Boolean algebra equivalence families from TCK (`Boolean3/Boolean5`) until tri-valued core is locked.
4. WHERE scenarios coupled to currently unsupported MATCH forms (comma-pattern multi-root / optional interactions).

## Primary Risk Callout
Current row-expression boolean machinery coerces masks using `fillna(False)` in places where Cypher expects null-preserving three-valued logic. This is the main source of false positives in semantic pass checks.

## Recommendation
Implement tri-valued boolean mask handling first (shared helper), then re-run focused boolean/null families before widening to XOR/IN/null-heavy algebraic scenarios.
