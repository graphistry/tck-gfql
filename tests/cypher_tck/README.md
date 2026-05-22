# Cypher TCK conformance tests (GFQL)

This suite translates a subset of the openCypher TCK into GFQL AST/wire protocol
queries and validates results against the reference enumerator and pandas, with
optional cuDF runs when enabled.

## Source of truth
- openCypher TCK: https://github.com/opencypher/openCypher/tree/main/tck
- Local clone (gitignored): `plans/cypher-tck-conformance/tck`

## Provenance
- Clone date: 2025-12-29
- Repo commit: `59edf2e1c17b845bf97c334ed06b2eb780950c13`
- License: Apache License 2.0 (`plans/cypher-tck-conformance/tck/LICENSE`)

## Goals
- Translate supported Cypher scenarios into GFQL equivalents.
- Run each translated case on:
  - Reference enumerator (oracle)
  - `engine='pandas'`
  - `engine='cudf'` (only when `TEST_CUDF=1` and cudf is available)
- Record unsupported scenarios with explicit xfail/skip reasons and capability tags.
- Preserve traceability to the original Cypher query and expected results.
  - Capability tags include `target-table-ops`, `target-expr-dsl`, `defer-quantifier`,
    `defer-path-enum`, `defer-unwind`, `defer-union`.

## Running
```bash
pytest tests/cypher_tck -xvs
TEST_CUDF=1 pytest tests/cypher_tck -xvs
PYGRAPHISTRY_PATH=/path/to/pygraphistry python -m tests.cypher_tck.report
python -m tests.cypher_tck.snapshot_delta old-report.json new-report.json \
  --json-output build/direct-cypher-snapshot-delta.json \
  --markdown-output build/direct-cypher-snapshot-delta.md
python -m tests.cypher_tck.unified_conformance_summary \
  --report-json build/cypher-tck-report.json \
  --manifest tests/cypher_tck/capability_debt_manifest.json \
  --snapshot-delta build/direct-cypher-snapshot-delta.json \
  --json-output build/unified-conformance-summary.json \
  --markdown-output build/unified-conformance-summary.md
PYGRAPHISTRY_PATH=/path/to/pygraphistry python -m tests.cypher_tck.coverage_gap_report \
  --json-output build/coverage-gap-report.json \
  --markdown-output build/coverage-gap-report.md
```

## Porting backlog
```bash
PYGRAPHISTRY_PATH=/path/to/pygraphistry python -m tests.cypher_tck.porting_backlog
python -m tests.cypher_tck.porting_backlog
BACKLOG_LIMIT=20 python -m tests.cypher_tck.porting_backlog
```

## Notes
- The TCK repo is not vendored; use the local clone under `plans/`.
- Each translated scenario should include a reference back to the TCK path,
  the original Cypher, and the expected rows or aggregates.
- For xfail scenarios, `gfql` may contain a non-executable plan built with
  `tests.cypher_tck.gfql_plan` to document the intended translation. When a
  target-table-ops or target-expr-dsl scenario lacks a manual plan, a minimal
  clause-based plan is generated from the Cypher text at load time.
- Track feature gaps and workarounds in `tests/cypher_tck/GAP_ANALYSIS.md`.
- `tests.cypher_tck.report` now emits both conformance counts and a reusable
  lane-priority view for backlog planning, including tracker placeholders for
  the current top candidate workstreams.
- `tests.cypher_tck.snapshot_delta` compares two direct-Cypher report artifacts
  and writes a structured JSON delta plus a PR-ready markdown summary. Plain
  `tests.cypher_tck.report` artifacts provide aggregate count and debt deltas;
  artifacts that also include a first-party `direct_cypher_cases` inventory
  enable exact added/removed/changed case summaries.
- `tests.cypher_tck.unified_conformance_summary` consumes the report JSON,
  capability/debt manifest, and snapshot-delta JSON artifacts to write a
  schema-versioned JSON summary plus PR-ready markdown. It is a consumer of the
  three artifact contracts and does not change their schemas.
- `tests.cypher_tck.coverage_gap_report` runs the scenario suite under
  coverage.py and writes a schema-versioned pygraphistry GFQL zero-hit range
  inventory as JSON plus markdown. It is evidence-only for shrink targeting:
  the report does not recommend deletion or modify pygraphistry files.
- `tests.cypher_tck.capability_debt_manifest` validates the versioned
  capability/debt manifest. Manifest schema version 2 adds an optional
  per-scenario `expected_error` block:

  ```json
  {
    "expected_error": {
      "code": "GFQL_RANGE_ARGUMENT",
      "key_fields": {
        "category": "validation",
        "field": "range",
        "value": "bad"
      },
      "anchored_substrings": ["range", "bad"]
    }
  }
  ```

  The block is structured matcher input for case-level direct-Cypher expected
  error payloads when a report artifact includes `direct_cypher_cases`. Entries
  without the block remain valid against artifacts that do not carry case-level
  actual error payloads.
