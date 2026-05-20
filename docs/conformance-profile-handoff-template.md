# Conformance profile handoff template

Use this template when a conformance lane needs coordination between
`graphistry/tck-gfql` and `graphistry/pygraphistry`. Fill in the fields that
apply and leave non-applicable fields marked `not required` with a short
rationale.

## Header

| Field | Value |
|---|---|
| Handoff title | `<short conformance profile or lane name>` |
| Date | `<YYYY-MM-DD>` |
| Coordinator | `<name or handle>` |
| tck-gfql ref | `<branch, tag, or sha>` |
| pygraphistry ref | `<branch, tag, or sha>` |
| Upstream source commit | `<recorded openCypher commit, if relevant>` |
| Execution profile | `cpu-pandas / cpu-polars / gpu-cudf / mixed` |
| Validation location | `local / GitHub Actions / dgx-spark / other` |

## Classification

| Field | Value |
|---|---|
| Primary owner repo | `tck-gfql / pygraphistry / shared` |
| Failure class | `harness translation / pygraphistry implementation / environment-dependency / upstream freshness / docs-process` |
| Snapshot category touched | `phase_support / direct_cypher_support / direct_cypher_xfail_contract / gap_priority / lane_contracts / coverage_baseline / none` |
| Public issue(s) | `<repo#issue links>` |
| Private artifact(s) | `<plans/... links, if any>` |

## Scenario or feature scope

| Field | Value |
|---|---|
| Feature family | `<for example clauses/with-orderBy>` |
| Scenario keys | `<keys or pointer to generated list>` |
| Current status | `supported / xfail / wrong rows / validation error / not imported` |
| Expected next status | `<target>` |
| User value | `high / medium / low` |
| Architecture risk | `high / medium / low` |

## Evidence

| Evidence type | Link, command, or result |
|---|---|
| Local command | `<command>` |
| CI run | `<url>` |
| Report output | `<summary or artifact path>` |
| Cross-repo ref pair | `<tck-gfql sha> + <pygraphistry sha>` |
| GPU/RAPIDS evidence | `<required/not required; dgx-spark run link or command>` |

## Routing decision

| Destination | Action |
|---|---|
| tck-gfql | `<scenario import, runner, support snapshot, gap metadata, docs>` |
| pygraphistry | `<implementation, parser/lowering, GFQL runtime, reference/parity tests>` |
| both | `<branch-paired CI or handoff item>` |

## Required updates before close

- [ ] Public issue uses independent-design framing.
- [ ] No third-party fixtures or tests are imported.
- [ ] No upstream source files are vendored or copied into `tck-gfql`.
- [ ] Recorded source commit and provenance references are preserved where relevant.
- [ ] Snapshot category updates are named explicitly.
- [ ] CI gate owner is named explicitly.
- [ ] GPU/RAPIDS validation is either completed or marked not required with rationale.
- [ ] Cross-link added between `tck-gfql` and `pygraphistry` issues/PRs when both repos are touched.

## Closeout summary

```markdown
Conformance handoff closeout:
- tck-gfql ref:
- pygraphistry ref:
- Scenario families:
- Snapshot categories updated:
- Tests/CI:
- GPU/RAPIDS:
- Remaining owner:
- Follow-up issue:
```
