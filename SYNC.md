# Sync Guide

This repo mirrors the Cypher TCK conformance harness used in PyGraphistry.
The code lives under `tests/cypher_tck/` and is intended to stay in sync with
`pygraphistry`'s corresponding directory.

## Recommended direction
- **Primary edit here**, then sync into `pygraphistry` for integration tests.
- If you must edit in `pygraphistry`, sync back here immediately to avoid drift.

## Sync commands
Replace paths as needed for your workspace.

```bash
export TCK_GFQL_ROOT=/path/to/tck-gfql
export PYGRAPHISTRY_ROOT=/path/to/pygraphistry
```

### tck-gfql → pygraphistry
```bash
rsync -a --delete --exclude '__pycache__' --exclude '.pytest_cache' \
  "${TCK_GFQL_ROOT}/tests/cypher_tck/" \
  "${PYGRAPHISTRY_ROOT}/tests/cypher_tck/"
```

### pygraphistry → tck-gfql
```bash
rsync -a --delete --exclude '__pycache__' --exclude '.pytest_cache' \
  "${PYGRAPHISTRY_ROOT}/tests/cypher_tck/" \
  "${TCK_GFQL_ROOT}/tests/cypher_tck/"
```

## Notes
- Keep the TCK clone in `plans/cypher-tck-conformance/tck` (gitignored).
- The scenario layout mirrors the TCK file tree under
  `tests/cypher_tck/scenarios/tck/features/`.
