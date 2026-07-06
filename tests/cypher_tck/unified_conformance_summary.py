from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence, cast

from tests.cypher_tck import capability_debt_manifest, report, snapshot_delta
from tests.cypher_tck.models import Scenario

SUMMARY_SCHEMA_VERSION = 1
DEFAULT_JSON_OUTPUT = Path("build/unified-conformance-summary.json")
DEFAULT_MARKDOWN_OUTPUT = Path("build/unified-conformance-summary.md")

DEBT_CATEGORY = "debt"

# Unified conformance summary contract:
# - This is a consumer artifact over the #147 report, #152 manifest, and #156
#   snapshot-delta outputs. It does not redefine or mutate those input schemas.
# - `schema_version` starts at 1 and must be bumped for incompatible output
#   shape or meaning changes.
# - Markdown output is intended for PR comments; JSON output is the downstream
#   tooling contract.


def _read_json(path: Path) -> dict[str, Any]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return cast(dict[str, Any], parsed)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _as_mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _as_list(value: object) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _as_case_list(value: object) -> list[Mapping[str, Any]]:
    return [item for item in _as_list(value) if isinstance(item, Mapping)]


def _counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def _input_warnings(
    report_artifact: Mapping[str, Any],
    manifest: Mapping[str, Any],
    delta: Mapping[str, Any],
    scenarios: Sequence[Scenario],
) -> list[str]:
    warnings: list[str] = []
    if report_artifact.get("schema_version") != report.SCHEMA_VERSION:
        warnings.append(
            "report artifact schema_version is "
            f"{report_artifact.get('schema_version')!r}, expected {report.SCHEMA_VERSION}"
        )
    if (
        manifest.get("schema_version")
        != capability_debt_manifest.MANIFEST_SCHEMA_VERSION
    ):
        warnings.append(
            "manifest schema_version is "
            f"{manifest.get('schema_version')!r}, expected "
            f"{capability_debt_manifest.MANIFEST_SCHEMA_VERSION}"
        )
    if manifest.get("compatible_report_schema_version") != report.SCHEMA_VERSION:
        warnings.append(
            "manifest compatible_report_schema_version is "
            f"{manifest.get('compatible_report_schema_version')!r}, expected "
            f"{report.SCHEMA_VERSION}"
        )
    if delta.get("schema_version") != snapshot_delta.OUTPUT_SCHEMA_VERSION:
        warnings.append(
            "snapshot delta schema_version is "
            f"{delta.get('schema_version')!r}, expected "
            f"{snapshot_delta.OUTPUT_SCHEMA_VERSION}"
        )
    if delta.get("input_schema_version") != snapshot_delta.INPUT_SCHEMA_VERSION:
        warnings.append(
            "snapshot delta input_schema_version is "
            f"{delta.get('input_schema_version')!r}, expected "
            f"{snapshot_delta.INPUT_SCHEMA_VERSION}"
        )
    delta_warnings = delta.get("input_warnings")
    if isinstance(delta_warnings, list):
        warnings.extend(str(warning) for warning in delta_warnings)
    try:
        capability_debt_manifest.validate_manifest(
            manifest,
            artifact=report_artifact,
            scenarios=scenarios,
        )
    except capability_debt_manifest.ManifestValidationError as exc:
        warnings.extend(f"manifest validation: {error}" for error in exc.errors)
    return warnings


def _manifest_entries(manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return _as_case_list(manifest.get("scenario_entries"))


def _manifest_by_key(manifest: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    entries: dict[str, Mapping[str, Any]] = {}
    for entry in _manifest_entries(manifest):
        key = entry.get("key")
        if isinstance(key, str):
            entries[key] = entry
    return entries


def _manifest_summary(manifest: Mapping[str, Any]) -> dict[str, Any]:
    entries = _manifest_entries(manifest)
    support_counts: Counter[str] = Counter()
    implementation_counts: Counter[str] = Counter()
    reason_count = 0
    direct_cypher_debt_count = 0
    for entry in entries:
        support_status = entry.get("support_status")
        implementation_status = entry.get("implementation_status")
        if isinstance(support_status, str):
            support_counts[support_status] += 1
        if isinstance(implementation_status, str):
            implementation_counts[implementation_status] += 1
        reason = entry.get("reason")
        if isinstance(reason, str) and reason.strip():
            reason_count += 1
        if isinstance(entry.get("direct_cypher_debt"), Mapping):
            direct_cypher_debt_count += 1

    return {
        "scenario_entry_count": len(entries),
        "support_status_counts": _counter_dict(support_counts),
        "implementation_status_counts": _counter_dict(implementation_counts),
        "reasoned_debt_entry_count": reason_count,
        "direct_cypher_debt_count": direct_cypher_debt_count,
    }


def _case_category(case: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = case.get(key)
        if isinstance(value, str):
            return value
    return None


def _case_key(case: Mapping[str, Any]) -> str | None:
    key = case.get("key")
    if isinstance(key, str) and key:
        return key
    return None


def _manifest_context(
    key: str,
    manifest_by_key: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    entry = manifest_by_key.get(key, {})
    context: dict[str, Any] = {
        "key": key,
        "support_status": entry.get("support_status", "missing_manifest_entry"),
        "implementation_status": entry.get(
            "implementation_status", "missing_manifest_entry"
        ),
        "ownership": entry.get("ownership", "missing_manifest_entry"),
    }
    reason = entry.get("reason")
    if isinstance(reason, str) and reason:
        context["reason"] = reason
    direct_cypher_debt = entry.get("direct_cypher_debt")
    if isinstance(direct_cypher_debt, Mapping):
        context["direct_cypher_debt"] = dict(direct_cypher_debt)
    return context


def _enrich_case(
    case: Mapping[str, Any],
    manifest_by_key: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    key = _case_key(case)
    if key is None:
        return dict(case)
    enriched = dict(case)
    enriched["manifest"] = _manifest_context(key, manifest_by_key)
    return enriched


def _debt_movement(
    delta: Mapping[str, Any],
    manifest_by_key: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    newly_broken: list[dict[str, Any]] = []
    recovered: list[dict[str, Any]] = []
    removed_debt: list[dict[str, Any]] = []

    for case in _as_case_list(delta.get("changed_cases")):
        old_category = _case_category(case, "old_category")
        new_category = _case_category(case, "new_category")
        if old_category != DEBT_CATEGORY and new_category == DEBT_CATEGORY:
            newly_broken.append(_enrich_case(case, manifest_by_key))
        elif old_category == DEBT_CATEGORY and new_category != DEBT_CATEGORY:
            recovered.append(_enrich_case(case, manifest_by_key))

    for case in _as_case_list(delta.get("removed_cases")):
        if _case_category(case, "category") == DEBT_CATEGORY:
            removed_debt.append(_enrich_case(case, manifest_by_key))

    remaining_debt = [
        _enrich_case(case, manifest_by_key)
        for case in _as_case_list(delta.get("remaining_debt"))
    ]

    return {
        "counts": {
            "newly_broken": len(newly_broken),
            "recovered": len(recovered),
            "removed_debt": len(removed_debt),
            "remaining_debt": len(remaining_debt),
        },
        "newly_broken": newly_broken,
        "recovered": recovered,
        "removed_debt": removed_debt,
        "remaining_debt": remaining_debt,
    }


def _headline_counts(report_artifact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": report_artifact.get("generated_at"),
        "source_refs": report_artifact.get("source_refs", {}),
        "scenario_counts": report_artifact.get("scenario_counts", {}),
        "gfql_counts": report_artifact.get("gfql_counts", {}),
        "direct_cypher_counts": report_artifact.get("direct_cypher_counts", {}),
        "expected_error_counts": report_artifact.get("expected_error_counts", {}),
        "debt_key_count": len(_as_list(report_artifact.get("debt_keys"))),
    }


def build_summary(
    report_artifact: Mapping[str, Any],
    manifest: Mapping[str, Any],
    delta: Mapping[str, Any],
    *,
    scenarios: Sequence[Scenario] = capability_debt_manifest.SCENARIOS,
) -> dict[str, Any]:
    manifest_by_key = _manifest_by_key(manifest)
    movement = _debt_movement(delta, manifest_by_key)
    summary_counts = _as_mapping(delta.get("summary_counts"))
    added_passing_cases = _as_case_list(delta.get("added_passing_cases"))
    added_expected_error_cases = _as_case_list(delta.get("added_expected_error_cases"))
    removed_cases = _as_case_list(delta.get("removed_cases"))
    changed_cases = _as_case_list(delta.get("changed_cases"))
    remaining_debt = _as_case_list(delta.get("remaining_debt"))

    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "inputs": {
            "report_schema_version": report_artifact.get("schema_version"),
            "manifest_schema_version": manifest.get("schema_version"),
            "snapshot_delta_schema_version": delta.get("schema_version"),
        },
        "headline": _headline_counts(report_artifact),
        "manifest": _manifest_summary(manifest),
        "direct_cypher_delta": {
            "summary_counts": dict(summary_counts),
            "direct_cypher_counts_delta": dict(
                _as_mapping(delta.get("direct_cypher_counts_delta"))
            ),
            "expected_error_counts_delta": dict(
                _as_mapping(delta.get("expected_error_counts_delta"))
            ),
            "added_passing_cases": [dict(case) for case in added_passing_cases],
            "added_expected_error_cases": [
                dict(case) for case in added_expected_error_cases
            ],
            "removed_cases": [dict(case) for case in removed_cases],
            "changed_cases": [dict(case) for case in changed_cases],
            "remaining_debt": [dict(case) for case in remaining_debt],
        },
        "debt_movement": movement,
        "newly_broken_support_classifications": movement["newly_broken"],
        "input_warnings": _input_warnings(
            report_artifact,
            manifest,
            delta,
            scenarios,
        ),
    }


def _format_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return "`" + json.dumps(value, sort_keys=True, separators=(",", ":")) + "`"
    return str(value).replace("|", "\\|")


def _count(mapping: Mapping[str, Any], key: str) -> object:
    return mapping.get(key, 0)


def _render_key_table(title: str, cases: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not cases:
        lines.extend(["None.", ""])
        return lines
    lines.extend(
        [
            "| key | transition | support | implementation | ownership | reason |",
            "|---|---|---|---|---|---|",
        ]
    )
    for case in cases:
        manifest = _as_mapping(case.get("manifest"))
        transition = ""
        old_category = case.get("old_category")
        new_category = case.get("new_category")
        if old_category is not None or new_category is not None:
            transition = f"{old_category or ''} -> {new_category or ''}"
        else:
            transition = str(case.get("category", ""))
        lines.append(
            "| {key} | {transition} | {support} | {implementation} | {ownership} | {reason} |".format(
                key=_format_cell(case.get("key")),
                transition=_format_cell(transition),
                support=_format_cell(manifest.get("support_status")),
                implementation=_format_cell(manifest.get("implementation_status")),
                ownership=_format_cell(manifest.get("ownership")),
                reason=_format_cell(manifest.get("reason")),
            )
        )
    lines.append("")
    return lines


def _case_summary(case: Mapping[str, Any]) -> str:
    fields = (
        "category",
        "cardinality",
        "row_count",
        "ordered",
        "outcome",
        "error_code",
    )
    parts = [
        f"{field}={_format_cell(case[field])}"
        for field in fields
        if field in case and case[field] is not None
    ]
    return ", ".join(parts)


def _render_case_table(title: str, cases: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not cases:
        lines.extend(["None.", ""])
        return lines
    lines.extend(["| key | summary |", "|---|---|"])
    for case in cases:
        lines.append(f"| {_format_cell(case.get('key'))} | {_case_summary(case)} |")
    lines.append("")
    return lines


def _render_changed_table(changed_cases: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = ["## Direct-Cypher Changed Cases", ""]
    if not changed_cases:
        lines.extend(["None.", ""])
        return lines
    lines.extend(["| key | transition | changed fields |", "|---|---|---|"])
    for case in changed_cases:
        changes = [
            str(change.get("field"))
            for change in _as_case_list(case.get("changes"))
            if change.get("field") is not None
        ]
        transition = "{old} -> {new}".format(
            old=case.get("old_category", ""),
            new=case.get("new_category", ""),
        )
        lines.append(
            "| {key} | {transition} | {changes} |".format(
                key=_format_cell(case.get("key")),
                transition=_format_cell(transition),
                changes=_format_cell(", ".join(changes)),
            )
        )
    lines.append("")
    return lines


def render_markdown(summary: Mapping[str, Any]) -> str:
    headline = _as_mapping(summary.get("headline"))
    scenario_counts = _as_mapping(headline.get("scenario_counts"))
    gfql_counts = _as_mapping(headline.get("gfql_counts"))
    direct_counts = _as_mapping(headline.get("direct_cypher_counts"))
    expected_error_counts = _as_mapping(headline.get("expected_error_counts"))
    manifest_summary = _as_mapping(summary.get("manifest"))
    support_counts = _as_mapping(manifest_summary.get("support_status_counts"))
    implementation_counts = _as_mapping(
        manifest_summary.get("implementation_status_counts")
    )
    delta = _as_mapping(summary.get("direct_cypher_delta"))
    delta_counts = _as_mapping(delta.get("summary_counts"))
    movement = _as_mapping(summary.get("debt_movement"))
    movement_counts = _as_mapping(movement.get("counts"))

    lines = [
        "# Unified Conformance Summary",
        "",
        "## Headline Counts",
        "",
        "| metric | value |",
        "|---|---:|",
        f"| Scenarios total | {_count(scenario_counts, 'total')} |",
        f"| Supported | {_count(scenario_counts, 'supported')} |",
        f"| Xfail | {_count(scenario_counts, 'xfail')} |",
        f"| Skip | {_count(scenario_counts, 'skip')} |",
        f"| GFQL translated | {_count(gfql_counts, 'translated_non_none')} |",
        f"| Direct-Cypher total snapshot | {_count(direct_counts, 'total_snapshot')} |",
        f"| Direct-Cypher promoted-only rows | {_count(direct_counts, 'promoted_only_rows')} |",
        f"| Direct-Cypher promoted-only expected errors | {_count(direct_counts, 'promoted_only_expected_errors')} |",
        f"| Direct-Cypher non-validation debt | {_count(expected_error_counts, 'direct_cypher_nonvalidation_debt')} |",
        "",
        "## Manifest Summary",
        "",
        "| metric | value |",
        "|---|---:|",
        f"| Manifest scenario entries | {_count(manifest_summary, 'scenario_entry_count')} |",
        f"| Manifest supported | {_count(support_counts, 'supported')} |",
        f"| Manifest xfail | {_count(support_counts, 'xfail')} |",
        f"| Manifest skip | {_count(support_counts, 'skip')} |",
        f"| Manifest translated | {_count(implementation_counts, 'translated')} |",
        f"| Manifest direct-Cypher only | {_count(implementation_counts, 'direct_cypher_only')} |",
        f"| Manifest not yet implemented | {_count(implementation_counts, 'not_yet_implemented')} |",
        f"| Manifest direct-Cypher debt keys | {_count(manifest_summary, 'direct_cypher_debt_count')} |",
        "",
        "## Direct-Cypher Delta",
        "",
        "| category | count |",
        "|---|---:|",
        f"| Added passing cases | {_count(delta_counts, 'added_passing_cases')} |",
        f"| Added expected-error cases | {_count(delta_counts, 'added_expected_error_cases')} |",
        f"| Removed cases | {_count(delta_counts, 'removed_cases')} |",
        f"| Changed cases | {_count(delta_counts, 'changed_cases')} |",
        f"| Remaining debt | {_count(delta_counts, 'remaining_debt')} |",
        "",
        "## Debt Movement",
        "",
        "| category | count |",
        "|---|---:|",
        f"| Newly broken support classifications | {_count(movement_counts, 'newly_broken')} |",
        f"| Recovered debt transitions | {_count(movement_counts, 'recovered')} |",
        f"| Removed debt cases | {_count(movement_counts, 'removed_debt')} |",
        f"| Remaining direct-Cypher debt | {_count(movement_counts, 'remaining_debt')} |",
        "",
    ]

    lines.extend(
        _render_case_table(
            "Direct-Cypher Added Passing Cases",
            cast(list[Mapping[str, Any]], delta.get("added_passing_cases", [])),
        )
    )
    lines.extend(
        _render_case_table(
            "Direct-Cypher Added Expected-Error Cases",
            cast(list[Mapping[str, Any]], delta.get("added_expected_error_cases", [])),
        )
    )
    lines.extend(
        _render_case_table(
            "Direct-Cypher Removed Cases",
            cast(list[Mapping[str, Any]], delta.get("removed_cases", [])),
        )
    )
    lines.extend(
        _render_changed_table(
            cast(list[Mapping[str, Any]], delta.get("changed_cases", []))
        )
    )

    lines.extend(
        _render_key_table(
            "Newly Broken Support Classifications",
            cast(list[Mapping[str, Any]], movement.get("newly_broken", [])),
        )
    )
    lines.extend(
        _render_key_table(
            "Recovered Debt",
            cast(list[Mapping[str, Any]], movement.get("recovered", [])),
        )
    )
    lines.extend(
        _render_key_table(
            "Removed Debt Cases",
            cast(list[Mapping[str, Any]], movement.get("removed_debt", [])),
        )
    )

    warnings = _as_list(summary.get("input_warnings"))
    if warnings:
        lines.extend(["## Input Warnings", ""])
        for warning in warnings:
            warning_lines = str(warning).splitlines() or [""]
            lines.append(f"- {warning_lines[0]}")
            lines.extend(f"  {line}" for line in warning_lines[1:])
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build a unified PR-ready conformance summary from the report JSON, "
            "capability/debt manifest, and direct-Cypher snapshot delta artifacts."
        )
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=report.DEFAULT_JSON_OUTPUT,
        help=f"#147 report artifact path (default: {report.DEFAULT_JSON_OUTPUT})",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=capability_debt_manifest.DEFAULT_MANIFEST_PATH,
        help=(
            "#152 capability/debt manifest path "
            f"(default: {capability_debt_manifest.DEFAULT_MANIFEST_PATH})"
        ),
    )
    parser.add_argument(
        "--snapshot-delta",
        type=Path,
        required=True,
        help="#156 snapshot-delta JSON artifact path",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
        help=f"Path for the unified JSON artifact (default: {DEFAULT_JSON_OUTPUT})",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=DEFAULT_MARKDOWN_OUTPUT,
        help=(
            "Path for the PR-ready markdown summary "
            f"(default: {DEFAULT_MARKDOWN_OUTPUT})"
        ),
    )
    args = parser.parse_args(argv)

    summary = build_summary(
        _read_json(args.report_json),
        _read_json(args.manifest),
        _read_json(args.snapshot_delta),
    )
    markdown = render_markdown(summary)
    _write_json(args.json_output, summary)
    _write_text(args.markdown_output, markdown)
    print(markdown)
    print(f"Unified JSON summary written: {args.json_output}")
    print(f"Unified markdown summary written: {args.markdown_output}")


if __name__ == "__main__":
    main()
