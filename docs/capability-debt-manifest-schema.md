# Capability/debt manifest schema

`tests/cypher_tck/capability_debt_manifest.json` is the public
scenario-level ownership and debt contract for the tck-gfql harness. It is
generated from first-party harness metadata by
`tests.cypher_tck.capability_debt_manifest` and validated by pytest against the
current scenario inventory and the #147 conformance JSON report artifact.

The manifest complements the report artifact instead of replacing it:

- The report artifact owns headline counts, source refs, runtime profile labels,
  expected-error counts, and direct-Cypher debt inventory.
- The capability/debt manifest owns per-scenario support status,
  implementation status, ownership labels, tags, reason strings, optional
  direct-Cypher debt details, and optional expected-error matcher blocks.

## Versioning

| Field | Current value | Policy |
|---|---:|---|
| `schema_version` | `2` | Bump for renamed fields, changed meanings, removed categories, or optional fields that downstream consumers should explicitly acknowledge. |
| `compatible_report_schema_version` | `1` | Must match the #147 report artifact schema version consumed by the validator. |

Additive fields that are optional and have documented defaults may keep the
current version when existing keys retain their meaning. Entries without an
optional `expected_error` block remain valid unless the paired report artifact
contains an actual expected-error case for that scenario.

## Top-level shape

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `schema_version` | integer | yes | Manifest contract version. |
| `compatible_report_schema_version` | integer | yes | Report artifact schema version this manifest validates against. |
| `category_definitions` | object | yes | Human-readable category definitions used by reports, handoffs, and future generated pick-lists. |
| `scenario_entries` | array | yes | One entry per represented scenario key. |

## Scenario entry shape

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `key` | string | yes | Stable scenario key from `tests.cypher_tck.scenarios`. |
| `support_status` | string | yes | One of `supported`, `xfail`, `skip`, or `other`. |
| `implementation_status` | string | yes | One of `translated`, `direct_cypher_only`, or `not_yet_implemented`. |
| `ownership` | string | yes | Harness-owned routing label such as `supported`, `direct-cypher-promotion`, `skipped`, or a primary xfail family id. |
| `tags` | array of strings | yes | Sorted scenario tags from harness metadata. |
| `reason` | string | required for xfail/skip debt | Human-readable first-party reason for represented debt. |
| `direct_cypher_debt` | object | optional | Direct-Cypher non-validation drift details when the report artifact lists the key in `debt_keys`. |
| `expected_error` | object | optional | Structured expected-error matcher for direct-Cypher expected-error cases. |

`direct_cypher_debt` contains:

| Field | Type | Meaning |
|---|---|---|
| `outcome` | string | Current non-validation outcome bucket. |
| `reason` | string | Stable `direct_cypher_nonvalidation:<outcome>` reason string. |

`expected_error` contains structured matcher input consumed by the comparator
diagnostics:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `code` | string | optional | Stable error code when available. |
| `key_fields` | object | optional | Key field/value pairs expected in the actual error payload. |
| `anchored_substrings` | array of strings | optional | Short substrings that must appear in the diagnostic message when no stronger structured field exists. |

## Validation contract

`python -m tests.cypher_tck.capability_debt_manifest --validate` and the pytest
suite fail when the manifest drifts from executable harness metadata. The
validator checks:

- exact scenario-key coverage;
- support status, implementation status, ownership, tag, and reason drift;
- missing xfail/debt reasons;
- direct-Cypher `debt_keys` alignment with the report artifact;
- aggregate-count drift against the #147 report artifact;
- stale or missing expected-error matcher blocks when direct-Cypher expected
  error cases are present in a paired report artifact.

Future issue forms or handoff pick-lists should use `category_definitions` and
the entry field names above rather than copying category wording into separate
surfaces.
