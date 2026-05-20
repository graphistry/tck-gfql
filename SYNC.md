# Cross-repo conformance coordination

This repo owns the Cypher TCK conformance harness used to validate
PyGraphistry's GFQL implementation. The harness code, scenario translations,
snapshot fixtures, and conformance debt metadata live under `tests/cypher_tck/`
in `graphistry/tck-gfql`.

PyGraphistry does not track a mirrored `tests/cypher_tck/` directory on the
inspected default integration surface. Instead, pygraphistry CI checks out this
external repository and runs the harness against the pygraphistry workspace.

## Normal direction

- Edit harness code, translated scenario metadata, conformance reports, support
  snapshots, and gap/debt metadata in `graphistry/tck-gfql`.
- Edit GFQL runtime, Cypher parsing/lowering, validation errors, reference
  oracle/parity tests, coverage baselines, and GPU/RAPIDS behavior in
  `graphistry/pygraphistry`.
- Run the harness against a pygraphistry checkout by passing
  `PYGRAPHISTRY_PATH` and, when dependencies must be installed,
  `PYGRAPHISTRY_INSTALL=1`.

```bash
PYGRAPHISTRY_PATH=/path/to/pygraphistry PYGRAPHISTRY_INSTALL=1 ./bin/ci.sh
```

## Branch-paired exceptions

During a coordinated feature lane, both repos may temporarily need branches with
matching names so CI can resolve the intended ref pair. Keep those edits in
their owning repo and document the pair in the PR body or handoff:

- `tck-gfql` branch/ref and SHA
- `pygraphistry` branch/ref and SHA
- execution profile (`cpu-pandas`, `gpu-cudf`, or mixed)
- snapshot category touched, if any
- owner repo for the next action

Do not copy or rsync `tests/cypher_tck/` into pygraphistry as part of normal
coordination. If a one-off local experiment requires copied files, keep it
outside tracked source and reconcile the actual change back into the owning repo
before opening a PR.

## Useful commands

```bash
# tck-gfql harness against installed/current pygraphistry
./bin/ci.sh

# tck-gfql harness against a sibling pygraphistry checkout
PYGRAPHISTRY_PATH=/path/to/pygraphistry PYGRAPHISTRY_INSTALL=1 ./bin/ci.sh

# Text report for local or CI summaries
python -m tests.cypher_tck.report
```

## Notes

- Keep local upstream TCK clones under `plans/` so they remain gitignored.
- The scenario layout in this repo mirrors the upstream TCK feature tree under
  `tests/cypher_tck/scenarios/tck/features/`.
- See `docs/conformance-ownership-map.md` for the public ownership boundary and
  shared artifact contracts.
