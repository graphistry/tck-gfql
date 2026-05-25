[![CI](https://github.com/graphistry/tck-gfql/actions/workflows/ci.yml/badge.svg)](https://github.com/graphistry/tck-gfql/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![pygraphistry](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/graphistry/tck-gfql/main/badges/pygraphistry-version.json)](https://github.com/graphistry/pygraphistry)

# GFQL Cypher TCK Conformance Harness

This repo hosts the Cypher TCK -> GFQL translation harness used by
PyGraphistry. It relies on an installed `pygraphistry` package to execute
GFQL queries and validate results.

## Layout
- [`tests/cypher_tck/`](tests/cypher_tck/): Scenario translations, runner, and gap analysis.
- [`docs/conformance-ownership-map.md`](docs/conformance-ownership-map.md): Ownership boundary with PyGraphistry and shared conformance artifact contracts.
- [`docs/capability-debt-manifest-schema.md`](docs/capability-debt-manifest-schema.md): Public schema for scenario-level capability/debt metadata and validation drift checks.
- [`docs/conformance-profile-handoff-template.md`](docs/conformance-profile-handoff-template.md): Coordinator-facing template for cross-repo conformance lanes.
- TCK clone (gitignored): `plans/cypher-tck-conformance/tck`.
- Cross-repo coordination guide: [SYNC.md](SYNC.md).

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
   uv pip install --python "$(command -v python)" -e /path/to/pygraphistry
   ```
2. Clone the openCypher TCK locally (gitignored):
   ```bash
   mkdir -p plans/cypher-tck-conformance
   git clone https://github.com/opencypher/openCypher plans/cypher-tck-conformance/tck
   ```

## Run
```bash
./bin/ci.sh
python3 -m pytest tests/cypher_tck -xvs
TEST_CUDF=1 python3 -m pytest tests/cypher_tck -xvs
```

`./bin/ci.sh` checks that the imported `graphistry.compute` package exposes the
GFQL row-pipeline API and row expression parser backend required by this harness
before pytest collection starts.

## Local pygraphistry override
Use a sibling checkout and install its dependencies in editable mode:
```bash
PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_PATH=../pygraphistry ./bin/ci.sh
```

`PYGRAPHISTRY_PATH` without `PYGRAPHISTRY_INSTALL=1` only prepends source to
`PYTHONPATH`; that is useful for quick import checks, but strict GFQL row
expression tests also need pygraphistry's parser dependency installed.

Install a specific ref from GitHub:
```bash
PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_REF=master ./bin/ci.sh
```

Dependency freshness policy:
- Non-graphistry dependencies should use a 6-day cooldown (`UV_EXCLUDE_NEWER="6 days"`).
- `graphistry`/`pygraphistry` is first-party and may be installed same-day.

## License
This repository is licensed under the Apache License 2.0. See [LICENSE](LICENSE)
and [NOTICE](NOTICE) for details and upstream attribution.
