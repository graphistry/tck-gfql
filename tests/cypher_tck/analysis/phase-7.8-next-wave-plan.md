# Phase 7.8 Next-Wave Plan

Date: 2026-03-03
Branch: `feat/return-pipeline-exec`

## Objective
Move from `supported_pure=1333` toward the next plateau by removing projection-driven strict-pure fallbacks and finishing the remaining impure-supported keys.

## Ordered priorities

1. Projection function lowering pack (highest ROI)
- Target: `select_local_projection` / `with_local_projection` dominant buckets.
- Scope: extend `_expr_to_gfql_string()` allowlist for vector-safe scalar functions already supported by pygraphistry row expressions (`toInteger`, `toFloat`, `abs`, `ceil`, `sqrt`, `substring`, `reverse`, selected temporal accessors).
- Guardrails: no local eval in strict-pure path; any non-convertible expression must fail-fast.

2. Remaining supported-impure burn-down (`10 -> 0`)
- Target keys: `expr-aggregation8-2`, `return-orderby4-1`, `return-orderby6-*`, `return-skip-limit2-5`, `return4-7`, `return6-*`.
- Scope: remove fallback triggers by adding constrained lowering for:
  - aggregate-in-projection patterns (`avg`, `count(distinct ...)` in mixed select/order contexts),
  - map projection literal forms used by `return6-6`,
  - expression UNWIND delegation needed by `return-orderby4-1`.

3. ORDER BY residual strict-pure fallback (`45`)
- Scope: computed ORDER BY lowering for remaining expression shapes still hitting `order_by_local_eval`.
- Prioritize simple boolean/list/index sort-key forms seen in `with-orderby2-*`/`with-orderby3-*`.

4. MATCH comma/variable-length follow-up (medium risk)
- Scope: only bounded, deterministic forms beyond current support.
- Keep fail-fast for disconnected comma chains and unbounded `*` forms.

5. Explicit defer list (outside this wave)
- Write clauses (`create`, `set`, `delete`) remain non-goals for pure lift in this cycle.
- High-fidelity temporal ordering edge cases and full path-object semantics remain staged after projection burn-down.

## Validation/quality loop (per slice)
- `python -m py_compile ...`, `ruff`, `mypy` on touched TCK files.
- `pytest -q tests/cypher_tck/test_plan_executor_*.py` focused tests + `test_tck_runner.py` full run.
- `sweep_promotions --write` and `tests.cypher_tck.report` after each slice.
- Purity check must be non-regressive: `supported_pure` must not decrease.
