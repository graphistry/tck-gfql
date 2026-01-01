[![CI](https://github.com/graphistry/tck-gfql/actions/workflows/ci.yml/badge.svg)](https://github.com/graphistry/tck-gfql/actions/workflows/ci.yml)

# GFQL Cypher TCK Conformance Harness

This repo hosts the Cypher TCK -> GFQL translation harness used by
PyGraphistry. It relies on an installed `pygraphistry` package to execute
GFQL queries and validate results.

## Layout
- `tests/cypher_tck/`: Scenario translations, runner, and gap analysis.
- TCK clone (gitignored): `plans/cypher-tck-conformance/tck`.
- Sync guide: `SYNC.md`.

## Setup
1. Install or editable-link `pygraphistry`:
   ```bash
   pip install -e /path/to/pygraphistry
   ```
2. Clone the openCypher TCK locally (gitignored):
   ```bash
   mkdir -p plans/cypher-tck-conformance
   git clone https://github.com/opencypher/openCypher plans/cypher-tck-conformance/tck
   ```

## Run
```bash
pytest tests/cypher_tck -xvs
TEST_CUDF=1 pytest tests/cypher_tck -xvs
```
