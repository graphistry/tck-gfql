# Phase 7.4 Quantifier/List Feasibility Matrix

## Scope
Assess ANY/ALL/NONE/SINGLE and list-expression support under strict vectorized pandas+cudf constraints, with WHERE interaction awareness.

## Evidence Snapshot
- Probe: `PYTHONPATH=. pytest -q graphistry/tests/compute/gfql/test_row_pipeline_ops.py -k "unwind or where_rows"`
  - Result: `6 passed, 1 skipped`
- Probe: `PYTHONPATH=/home/lmeyerov/Work/pygraphistry:/home/lmeyerov/Work/tck-gfql pytest -q tests/cypher_tck/test_tck_runner.py -k "quantifier or list"`
  - Result: `420 passed, 369 xfailed`
- Focused executor analysis (`quantifier` + `list` feature paths):
  - strict-pure blockers: `select_local_projection=203`, `with_local_projection=70`
  - semantic top failures: list-comprehension syntax lowering, `range()/sign()` missing in eval path, list slicing semantics, and selected quantifier truth-table mismatches.

## Matrix

### Easy / Can Add Now
1. `range(start, stop[, step])` expression lowering for select/with paths.
2. Basic list slicing (`list[a..b]`, open-ended bounds) in expression lowering.
3. Quantifier forms already mapped to row-expression engine (`ANY/ALL/NONE/SINGLE`) for straightforward scalar predicates.

### Medium (staged)
1. List-comprehension lowering (`[x IN list WHERE ... | ...]`) for constrained subforms.
2. `IN` with transformed list expressions where null semantics remain predictable.
3. Quantifier + null truth table hardening for selected boundary scenarios.

### Defer
1. Full list-comprehension support with nested function/pattern constructs.
2. Complex path/list projection forms (`nodes(path)` in comprehensions).
3. Cases requiring write-clause interaction (`SET`) or unsupported plan steps.

## Risk Notes
- Current semantic failures include Python-eval parse errors for Cypher list-comprehension syntax.
- Some quantifier failures are semantic (truth-table) not just parser/lowering gaps.
- `range`/slice lifts are low-risk/high-reward and should precede comprehension generalization.
