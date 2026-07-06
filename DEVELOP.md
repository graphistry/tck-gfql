# Development Setup

See also [CONTRIBUTING.md](CONTRIBUTING.md) (if/when added) and the project README.

This repo focuses on the openCypher TCK conformance harness for GFQL and uses
the local `plans/` clone of the TCK repo for reference (not vendored).

## Local Tests

```bash
UV_EXCLUDE_NEWER="6 days" uv pip install --python "$(command -v python)" pytest pandas networkx
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

The same workflow also emits `coverage-gap-pr-delta` artifacts when the paired
pygraphistry ref touches a shrink-targeting priority file. It compares #177
coverage-gap reports for the pygraphistry PR head against its merge-base and
posts or updates a separate marker-based comment with newly uncovered lines,
newly covered lines, and net coverage percentage deltas. If no requested
priority file is touched, the workflow writes a suppressed artifact and skips
creating a new coverage-delta comment; any existing marker comment is updated
in place to show the suppressed state.

Local delta reproduction from existing #177 coverage-gap JSON reports:

```bash
python -m tests.cypher_tck.coverage_gap_pr_delta \
  --base-report-json /path/to/base-coverage-gap-report.json \
  --head-report-json /path/to/head-coverage-gap-report.json \
  --changed-files /path/to/pygraphistry-changed-files.txt
```

Cross-PR shrink-cycle accounting can be reproduced from a sequence of existing
#177 coverage-gap reports:

```bash
python -m tests.cypher_tck.coverage_gap_cumulative_tracker \
  --report baseline=/path/to/post-1609-coverage-gap-report.json \
  --report pr1604=/path/to/pr1604-coverage-gap-report.json \
  --report pr1605=/path/to/pr1605-coverage-gap-report.json
```

When regenerating reports from pygraphistry master commits, first capture the
public commit list, then pass it with a local pygraphistry checkout. The tracker
uses temporary git worktrees under `build/coverage-gap-cumulative/reports/` and
does not edit the pygraphistry checkout:

```bash
gh api repos/graphistry/pygraphistry/commits > build/pygraphistry-commits.json
python -m tests.cypher_tck.coverage_gap_cumulative_tracker \
  --github-commits-json build/pygraphistry-commits.json \
  --pygraphistry-repo /path/to/pygraphistry \
  --baseline-commit 2d0be647690d \
  --commit-limit 5
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
