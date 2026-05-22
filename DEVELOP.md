# Development Setup

See also [CONTRIBUTING.md](CONTRIBUTING.md) (if/when added) and the project README.

This repo focuses on the openCypher TCK conformance harness for GFQL and uses
the local `plans/` clone of the TCK repo for reference (not vendored).

## Local Tests

```bash
UV_EXCLUDE_NEWER="6 days" uv pip install --python "$(command -v python)" pytest pandas
./bin/ci.sh
python3 -m pytest tests/cypher_tck -xvs
TEST_CUDF=1 python3 -m pytest tests/cypher_tck -xvs
```

When running from a sibling `pygraphistry` checkout, set:

```bash
PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_PATH=/path/to/pygraphistry ./bin/ci.sh
PYTHONPATH=/path/to/pygraphistry python3 -m tests.cypher_tck.porting_backlog
```

## Environment Variables

- `PYGRAPHISTRY_PATH`: use a local pygraphistry checkout (sibling repo).
- `PYGRAPHISTRY_INSTALL=1`: install pygraphistry (editable if `PYGRAPHISTRY_PATH` set).
- `PYGRAPHISTRY_REPO`: git URL for pygraphistry (CI default is upstream).
- `PYGRAPHISTRY_REF`: branch/tag/sha for pygraphistry (CI default is `master`).
- `UV_EXCLUDE_NEWER`: set to `6 days` for non-graphistry dependency installs.

Notes:
- Use pinned `uv` in CI.
- `graphistry`/`pygraphistry` installs are exempt from the 6-day cooldown (same-day allowed).

## CI

GitHub Actions runs the suite on PRs. See `.github/workflows`.
`nightly.yml` runs on schedule and updates the pygraphistry badge.

`pr-conformance-summary.yml` runs on PRs to generate the unified conformance
summary from the PR checkout against the base `main` checkout. It uploads the
structured JSON and markdown artifacts as `unified-conformance-summary`, then
posts or updates one marker-based PR comment. Local reproduction:

```bash
python -m tests.cypher_tck.pr_conformance_comment \
  --base-dir /path/to/base/tck-gfql \
  --head-dir /path/to/pr/tck-gfql \
  --pygraphistry-path /path/to/pygraphistry
```

## Debugging Tips

- Use `python3 -m tests.cypher_tck.report` to print the conformance summary.
- Use `python3 -m tests.cypher_tck.porting_backlog` for xfail coverage stats.
- Use `PYGRAPHISTRY_PATH=/path/to/pygraphistry python3 -m tests.cypher_tck.coverage_gap_report`
  to run the scenario suite under coverage.py and write the pygraphistry GFQL
  zero-hit range JSON/markdown artifacts under `build/`.
- If `./bin/ci.sh` reports missing `graphistry.compute` row-pipeline symbols,
  point `PYGRAPHISTRY_PATH` at a newer pygraphistry checkout or run with
  `PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_REF=<ref>`.
- If `./bin/ci.sh` reports the GFQL row expression parser backend is unavailable,
  rerun with `PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_PATH=/path/to/pygraphistry` so
  pygraphistry's parser dependency is installed instead of only prepending the
  source checkout to `PYTHONPATH`.

## Publish: Merge, Tag, & Release

1. Update `CHANGELOG.md` in your PR branch
   - Move changes from `## [Development]` into a dated release section (e.g., `## [0.1.0 - YYYY-MM-DD]`).
   - Keep `## [Development]` with empty headings.

2. Merge the PR to `main` (via GitHub UI or `gh pr merge`).

3. Switch to `main` and pull the merged changes:
   ```bash
   git checkout main
   git pull
   ```

4. Tag the repository with the new version number (semantic versioning):
   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   ```

5. Create a GitHub Release with notes from the changelog:
   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z" --notes "See CHANGELOG.md for details."
   ```
