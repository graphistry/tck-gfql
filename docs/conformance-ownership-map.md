# tck-gfql / pygraphistry conformance ownership map

This map defines the ownership boundary between `graphistry/tck-gfql` and
`graphistry/pygraphistry` for GFQL Cypher conformance work. The split is
intentional: `tck-gfql` owns the conformance harness, scenario translations,
and conformance debt inventory; `pygraphistry` owns the runtime, compiler,
reference/parity tests, and user-facing GFQL behavior.

The upstream freshness audit in graphistry/tck-gfql#148 confirmed that the
recorded openCypher TCK source commit
`59edf2e1c17b845bf97c334ed06b2eb780950c13` matches upstream main commit
`677cbafabb8c3c5eed458fd3b1ec0daec8d67d23` for `tck/features/**`.
No upstream scenario regeneration is needed for this ownership pass.

## Keep in tck-gfql

| Surface | Owner | Why it stays here |
|---|---|---|
| `tests/cypher_tck/scenarios/tck/features/**` | `tck-gfql` | Upstream-derived scenario translations, fixture metadata, xfail/skip status, and expected result capture belong with the harness that imports and reports them. |
| `tests/cypher_tck/scenarios/fixtures.py` | `tck-gfql` | Scenario-specific graph fixtures are part of the harness validation model and must stay close to translated scenario metadata. |
| `tests/cypher_tck/test_tck_runner.py` and focused runner tests | `tck-gfql` | Runner semantics, comparison behavior, and scenario status enforcement are harness concerns. |
| `tests/cypher_tck/report.py` | `tck-gfql` | The conformance report summarizes represented scenarios, status counts, direct-Cypher support, and debt buckets from harness-owned metadata. |
| `tests/cypher_tck/phase_support.py` | `tck-gfql` | Snapshot fixture for deterministic scenario support and promotion decisions. |
| `tests/cypher_tck/direct_cypher_support.py` | `tck-gfql` | Snapshot fixture for direct-Cypher overlap and promoted-only support counts. |
| `tests/cypher_tck/direct_cypher_xfail_contract.py` | `tck-gfql` | Harness-owned branch-paired debt snapshot for non-validation xfails and promoted direct-Cypher outcomes. |
| `tests/cypher_tck/gap_priority.py` and `tests/cypher_tck/lane_contracts.py` | `tck-gfql` | Capability and debt metadata that drive conformance lanes, tracker links, and report prioritization. |
| `tests/cypher_tck/GAP_ANALYSIS.md` and `tests/cypher_tck/analysis/**` | `tck-gfql` | Human-readable conformance gap inventory and lane planning artifacts. |
| `.github/workflows/ci.yml` and `.github/workflows/nightly.yml` | `tck-gfql` | Harness CI/nightly flows own selected pygraphistry ref resolution, harness execution, report generation, and the pygraphistry-version badge. |
| `README.md`, `DEVELOP.md`, `SYNC.md`, and this document | `tck-gfql` | Public harness setup, development, coordination, and ownership guidance. |
| `NOTICE` and source commit references | `tck-gfql` | Upstream openCypher derivative provenance and recorded source commit references must remain visible with the harness. |

`tck-gfql` may execute against a local or CI-provided pygraphistry checkout, but
that execution dependency does not move runtime source ownership into this repo.

## Keep in pygraphistry

| Surface | Owner | Why it stays there |
|---|---|---|
| `graphistry/compute/**` | `pygraphistry` | GFQL runtime, Cypher parser/lowering/binder, validation errors, physical execution, and backend dispatch are implementation concerns. |
| `graphistry/compute/gfql/defer_codes.py` | `pygraphistry` | Stable logical-plan defer-code identifiers are emitted by the runtime and consumed by tests and handoff artifacts. |
| `graphistry/compute/exceptions.py` | `pygraphistry` | Structured `GFQLValidationError`/`GFQLSyntaxError` error-code and expected-error wording surface is runtime-owned. |
| `tests/gfql/**` | `pygraphistry` | GFQL oracle, reference enumerator, and parity tests cover implementation behavior independent of the TCK harness. |
| `graphistry/tests/compute/gfql/**` | `pygraphistry` | Runtime, compiler, Cypher frontend, strict-mode, parity, and backend-specific conformance tests belong with implementation code. |
| `graphistry/tests/compute/gfql/coverage_baselines/*.json` | `pygraphistry` | Coverage baselines are tied to implementation files, runtime profiles, pandas/cuDF engines, and pygraphistry CI budgets. |
| `.github/workflows/ci.yml` job `tck-gfql` | `pygraphistry` | pygraphistry owns the integration gate that checks out a selected tck-gfql ref and runs the external harness against the current implementation. |
| `.github/workflows/ci.yml` GFQL jobs | `pygraphistry` | GFQL core tests, strict typing, differential/parity, surface guard, and coverage audit are implementation gates. |
| `.github/workflows/ci-gpu.yml` | `pygraphistry` | RAPIDS/cuDF execution and GPU availability are pygraphistry runtime concerns. `tck-gfql` should request GPU validation only when a scenario family depends on cuDF/RAPIDS behavior. |
| `docs/source/gfql/**` | `pygraphistry` | User-facing GFQL and Cypher behavior docs belong with the library release surface. |

The inspected pygraphistry checkout has no tracked `graphistry/tests/cypher_tck`
or `tests/cypher_tck` directory. Its `tests/gfql/README.md` points users to the
external `graphistry/tck-gfql` repository for Cypher TCK conformance.

## Shared artifact contracts

| Contract | Contract file | Consumers | Version-bump policy |
|---|---|---|---|
| Conformance JSON report artifact | `tests/cypher_tck/report.py`, output `build/cypher-tck-report.json` | tck-gfql CI/nightly summaries, pygraphistry integration jobs, coordinator handoffs, downstream dashboards | The JSON `schema_version` starts at `1`. Bump it for incompatible shape or meaning changes. Additive optional fields may keep the current version if existing keys retain meaning and stable ordering. |
| Upstream source provenance | `README.md`, `tests/cypher_tck/README.md`, `NOTICE`, and `tests/cypher_tck/report.py` source refs | tck-gfql maintainers, pygraphistry release reviewers, audit comments | Preserve recorded upstream repo, path, source commit, and license notice. Update the commit only in a dedicated freshness/import lane, not in ownership-map or runtime lanes. |
| Capability/debt manifest | `tests/cypher_tck/capability_debt_manifest.json`, `tests/cypher_tck/capability_debt_manifest.py`, with source metadata from `tests/cypher_tck/gap_priority.py`, `tests/cypher_tck/lane_contracts.py`, `tests/cypher_tck/direct_cypher_xfail_contract.py`, and `tests/cypher_tck/GAP_ANALYSIS.md` | tck-gfql report generation, issue templates, pygraphistry implementation planning | The manifest `schema_version` starts at `1`. Bump it for renamed fields, changed meanings, or removed categories. Additive optional fields may keep the current version when existing keys retain meaning. |
| Defer-code identifiers | `pygraphistry:graphistry/compute/gfql/defer_codes.py` | pygraphistry runtime/tests, tck-gfql debt metadata, handoff templates | Treat identifiers as stable once referenced by tck-gfql artifacts. Add new identifiers without renaming old ones; rename or meaning changes require a coordinated pygraphistry+tck-gfql update and release note. |
| Expected error codes and wording | `pygraphistry:graphistry/compute/exceptions.py`, `pygraphistry:docs/source/gfql/spec/python_embedding.md`, and focused pygraphistry tests | pygraphistry API users, tck-gfql expected-error scenarios, conformance reports | Error-code changes are compatibility changes and need coordinated test updates. Human wording may be clarified, but tck-gfql should assert stable codes/classes where available rather than fragile full strings. |
| Coverage baseline artifacts | `pygraphistry:graphistry/tests/compute/gfql/coverage_baselines/*.json` | pygraphistry GFQL coverage audit, release readiness reports | pygraphistry owns baseline updates. tck-gfql may cite coverage receipts in handoffs but should not edit these baselines. Baseline schema changes are pygraphistry-owned and should include migration notes. |
| Cross-repo CI ref selection | `tck-gfql:.github/workflows/ci.yml`, `tck-gfql:.github/workflows/nightly.yml`, `pygraphistry:.github/workflows/ci.yml` job `tck-gfql` | Both CI systems and coordinator handoffs | Keep ref-pair fields explicit in logs and summaries. Changing fallback branch names, dispatch inputs, or install mode requires coordinated PRs or a documented transition window. |
| Coordinator conformance handoff | `docs/conformance-profile-handoff-template.md` | Issue authors, PR authors, release coordinators | Template field removals or renamed classifications require a docs update and issue-template migration. Additive fields may be introduced when they are optional or have a documented default. |

## Duplication to remove or replace with generated/synced output

| Duplication / drift | Current files | Recommendation | Merge owner |
|---|---|---|---|
| Stale mirrored-directory sync guidance | `tck-gfql:SYNC.md` says `tests/cypher_tck/` should be rsynced bidirectionally into a corresponding pygraphistry directory; inspected pygraphistry has no tracked `tests/cypher_tck` or `graphistry/tests/cypher_tck`. | Replace with external-harness coordination guidance. Keep `tests/cypher_tck/**` in tck-gfql; keep pygraphistry as a checked-out/installable runtime dependency. Mention branch-paired exception handling only as an explicit temporary override. | `graphistry/tck-gfql` |
| Cross-repo local-run instructions | `tck-gfql:README.md`, `tck-gfql:tests/cypher_tck/README.md`, and `pygraphistry:tests/gfql/README.md` each describe how to run the external harness from a different angle. | Keep full instructions in `tck-gfql:README.md`. Keep `pygraphistry:tests/gfql/README.md` as a short pointer to tck-gfql plus the single local command. Avoid copying detailed tck-gfql setup into pygraphistry docs. | Split: `tck-gfql` owns full harness docs; `pygraphistry` owns pointer text. |
| CI gate language for ref-pair resolution | `tck-gfql:.github/workflows/ci.yml`, `tck-gfql:.github/workflows/nightly.yml`, `pygraphistry:.github/workflows/ci.yml` job `tck-gfql` each describe selected refs through shell output and summaries. | Auto-generate or standardize a short "conformance ref pair" summary from the JSON report artifact and workflow outputs. Keep workflow-specific mechanics local, but use the same field names: `tck_gfql_ref`, `tck_gfql_sha`, `pygraphistry_ref`, `pygraphistry_sha`, `execution_profile`. | Shared contract; implementation changes land in the repo whose workflow is edited. |
| Snapshot/debt category wording | `tests/cypher_tck/GAP_ANALYSIS.md`, `tests/cypher_tck/gap_priority.py`, `tests/cypher_tck/lane_contracts.py`, and `tests/cypher_tck/direct_cypher_xfail_contract.py` repeat lane/debt category names. | Introduce a public capability/debt manifest schema before adding more category surfaces. Auto-generate report sections and handoff pick-lists from that schema when practical. | `graphistry/tck-gfql` |
| Handoff checklist wording | Issue bodies, PR bodies, and private planning artifacts repeat owner repo, ref pair, snapshot category, failure class, GPU/RAPIDS applicability, and cross-link requirements. | Keep `docs/conformance-profile-handoff-template.md` as the public template and use it from issues/PRs. If a future issue form is added, generate its options from the same capability/debt manifest schema. | `graphistry/tck-gfql` first; pygraphistry can link to it from GFQL issue templates. |
| Expected-error assertions | tck-gfql scenario metadata may need to reference pygraphistry error outcomes while pygraphistry owns classes, codes, and messages. | Prefer stable pygraphistry error classes/codes in tck-gfql expected-error metadata. Avoid duplicating full human messages unless no structured code exists; request a pygraphistry code before broadening string-based assertions. | `graphistry/pygraphistry` owns runtime codes; `graphistry/tck-gfql` owns harness metadata. |
| Runtime coverage receipts | pygraphistry coverage baselines and tck-gfql conformance report both summarize readiness, but for different scopes. | Keep coverage baselines only in pygraphistry. Let tck-gfql cite pygraphistry coverage receipt URLs or artifact paths in handoffs instead of copying baseline JSON. | `graphistry/pygraphistry` |

No third-party fixtures or tests are imported by this map. No upstream
openCypher scenario files are regenerated or modified by this map.
