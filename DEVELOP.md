# Development Setup

See also [CONTRIBUTING.md](CONTRIBUTING.md) (if/when added) and the project README.

This repo focuses on the openCypher TCK conformance harness for GFQL and uses
the local `plans/` clone of the TCK repo for reference (not vendored).

## Local Tests

```bash
./bin/ci.sh
pytest tests/cypher_tck -xvs
TEST_CUDF=1 pytest tests/cypher_tck -xvs
```

When running from a sibling `pygraphistry` checkout, set:

```bash
PYTHONPATH=/path/to/pygraphistry python -m tests.cypher_tck.porting_backlog
```

## Environment Variables

- `PYGRAPHISTRY_PATH`: use a local pygraphistry checkout (sibling repo).
- `PYGRAPHISTRY_INSTALL=1`: install pygraphistry (editable if `PYGRAPHISTRY_PATH` set).
- `PYGRAPHISTRY_REPO`: git URL for pygraphistry (CI default is upstream).
- `PYGRAPHISTRY_REF`: branch/tag/sha for pygraphistry (CI default is `master`).

## CI

GitHub Actions runs the suite on PRs. See `.github/workflows`.
`nightly.yml` runs on schedule and updates the pygraphistry badge.

## Debugging Tips

- Use `python -m tests.cypher_tck.report` to print the conformance summary.
- Use `python -m tests.cypher_tck.porting_backlog` for xfail coverage stats.

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
