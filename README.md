[![CI](https://github.com/graphistry/tck-gfql/actions/workflows/ci.yml/badge.svg)](https://github.com/graphistry/tck-gfql/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

# GFQL Cypher TCK Conformance Harness

This repo hosts the Cypher TCK -> GFQL translation harness used by
PyGraphistry. It relies on an installed `pygraphistry` package to execute
GFQL queries and validate results.

## Layout
- [`tests/cypher_tck/`](tests/cypher_tck/): Scenario translations, runner, and gap analysis.
- TCK clone (gitignored): `plans/cypher-tck-conformance/tck`.
- Sync guide: [SYNC.md](SYNC.md).

## Links
- PyGraphistry repo: [graphistry/pygraphistry](https://github.com/graphistry/pygraphistry)
- GFQL docs: [pygraphistry.readthedocs.io](https://pygraphistry.readthedocs.io/en/latest/gfql/index.html)
- openCypher TCK: [opencypher/openCypher](https://github.com/opencypher/openCypher/tree/main/tck)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Code of Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Security: [SECURITY.md](SECURITY.md)

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

## Local pygraphistry override
Use a sibling checkout without installing by setting `PYGRAPHISTRY_PATH`:
```bash
PYGRAPHISTRY_PATH=../pygraphistry2 ./bin/ci.sh
```

Install a specific ref from GitHub:
```bash
PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_REF=master ./bin/ci.sh
```

## License
This repository is licensed under the Apache License 2.0. See [LICENSE](LICENSE)
and [NOTICE](NOTICE) for details and upstream attribution.
