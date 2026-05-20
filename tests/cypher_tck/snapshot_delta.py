from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

INPUT_SCHEMA_VERSION = 1
OUTPUT_SCHEMA_VERSION = 1
DEFAULT_JSON_OUTPUT = Path("build/direct-cypher-snapshot-delta.json")
DEFAULT_MARKDOWN_OUTPUT = Path("build/direct-cypher-snapshot-delta.md")

PASSING = "passing"
EXPECTED_ERROR = "expected_error"
DEBT = "debt"

_CARDINALITY_FIELDS = ("cardinality", "row_count", "rows_count", "expected_rows")
_ORDER_FIELDS = ("order", "ordered", "order_sensitive", "order_policy")
_TYPE_FIELDS = ("types", "column_types", "result_types")


@dataclass(frozen=True)
class SnapshotCase:
    key: str
    category: str
    details: Mapping[str, Any]


def _read_json(path: Path) -> Dict[str, Any]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return parsed


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _normalize_category(value: object) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip().lower().replace("-", "_")
    if normalized in {"pass", "passes", "passing", "row", "rows", "success"}:
        return PASSING
    if normalized in {
        "error",
        "errors",
        "expected_error",
        "expected_errors",
        "expectederror",
    }:
        return EXPECTED_ERROR
    if normalized in {"debt", "known_debt", "nonvalidation_debt", "xfail"}:
        return DEBT
    return normalized or None


def _case_to_json(case: SnapshotCase) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"category": case.category, "key": case.key}
    for key, value in sorted(case.details.items()):
        if key not in payload:
            payload[key] = value
    return payload


def _coerce_case(raw_case: object) -> Optional[SnapshotCase]:
    if not isinstance(raw_case, dict):
        return None
    key = raw_case.get("key")
    if not isinstance(key, str) or not key:
        return None
    category = _normalize_category(raw_case.get("category", raw_case.get("status")))
    if category is None:
        return None
    return SnapshotCase(key=key, category=category, details=dict(raw_case))


def _case_inventory(
    artifact: Mapping[str, Any],
    *,
    label: str,
) -> Tuple[Dict[str, SnapshotCase], List[str]]:
    warnings: List[str] = []
    cases: Dict[str, SnapshotCase] = {}
    raw_cases = artifact.get("direct_cypher_cases")

    if raw_cases is None:
        warnings.append(
            f"{label} artifact has no direct_cypher_cases inventory; "
            "case-level pass/error deltas are limited to fields present in the artifact."
        )
    elif isinstance(raw_cases, list):
        for index, raw_case in enumerate(raw_cases):
            case = _coerce_case(raw_case)
            if case is None:
                warnings.append(
                    f"{label} direct_cypher_cases[{index}] is missing a usable key/category"
                )
                continue
            cases[case.key] = case
    else:
        warnings.append(f"{label} direct_cypher_cases must be a list when present")

    raw_debt_keys = artifact.get("debt_keys", ())
    if isinstance(raw_debt_keys, list):
        for raw_debt in raw_debt_keys:
            if not isinstance(raw_debt, dict):
                continue
            key = raw_debt.get("key")
            if not isinstance(key, str) or not key:
                continue
            existing = cases.get(key)
            if existing is not None and existing.category != DEBT:
                warnings.append(
                    f"{label} debt_keys entry {key!r} overrides "
                    f"direct_cypher_cases category {existing.category!r}"
                )
            details = dict(raw_debt)
            details["category"] = DEBT
            cases[key] = SnapshotCase(key=key, category=DEBT, details=details)
    else:
        warnings.append(f"{label} debt_keys must be a list when present")

    return cases, warnings


def _first_present(details: Mapping[str, Any], fields: Iterable[str]) -> object:
    for field in fields:
        if field in details:
            return details[field]
    return None


def _jsonish(value: object) -> object:
    if isinstance(value, (dict, list, tuple, str, int, float, bool)) or value is None:
        return value
    return repr(value)


def _case_changes(old: SnapshotCase, new: SnapshotCase) -> List[Dict[str, Any]]:
    checks = (
        ("category", old.category, new.category),
        (
            "cardinality",
            _first_present(old.details, _CARDINALITY_FIELDS),
            _first_present(new.details, _CARDINALITY_FIELDS),
        ),
        (
            "order",
            _first_present(old.details, _ORDER_FIELDS),
            _first_present(new.details, _ORDER_FIELDS),
        ),
        (
            "type",
            _first_present(old.details, _TYPE_FIELDS),
            _first_present(new.details, _TYPE_FIELDS),
        ),
    )
    changes: List[Dict[str, Any]] = []
    for field, old_value, new_value in checks:
        if old_value != new_value:
            changes.append(
                {
                    "field": field,
                    "old": _jsonish(old_value),
                    "new": _jsonish(new_value),
                }
            )
    return changes


def _numeric_delta(
    old: Mapping[str, Any],
    new: Mapping[str, Any],
    key: str,
) -> Dict[str, int]:
    old_counts = old.get(key, {})
    new_counts = new.get(key, {})
    if not isinstance(old_counts, dict):
        old_counts = {}
    if not isinstance(new_counts, dict):
        new_counts = {}

    delta: Dict[str, int] = {}
    for count_key in sorted(set(old_counts) | set(new_counts)):
        old_value = old_counts.get(count_key, 0)
        new_value = new_counts.get(count_key, 0)
        if isinstance(old_value, int) and isinstance(new_value, int):
            delta[count_key] = new_value - old_value
    return delta


def _input_summary(artifact: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "generated_at": artifact.get("generated_at"),
        "schema_version": artifact.get("schema_version"),
        "source_refs": artifact.get("source_refs", {}),
    }


def _sorted_cases(cases: Iterable[SnapshotCase]) -> List[Dict[str, Any]]:
    return [_case_to_json(case) for case in sorted(cases, key=lambda item: item.key)]


def build_delta(
    old_artifact: Mapping[str, Any],
    new_artifact: Mapping[str, Any],
) -> Dict[str, Any]:
    old_schema = old_artifact.get("schema_version")
    new_schema = new_artifact.get("schema_version")
    warnings: List[str] = []
    if old_schema != INPUT_SCHEMA_VERSION:
        warnings.append(f"old artifact schema_version is {old_schema!r}, expected 1")
    if new_schema != INPUT_SCHEMA_VERSION:
        warnings.append(f"new artifact schema_version is {new_schema!r}, expected 1")

    old_cases, old_warnings = _case_inventory(old_artifact, label="old")
    new_cases, new_warnings = _case_inventory(new_artifact, label="new")
    warnings.extend(old_warnings)
    warnings.extend(new_warnings)

    old_keys = set(old_cases)
    new_keys = set(new_cases)
    added_keys = sorted(new_keys - old_keys)
    removed_keys = sorted(old_keys - new_keys)
    shared_keys = sorted(old_keys & new_keys)

    added_passing = [
        new_cases[key] for key in added_keys if new_cases[key].category == PASSING
    ]
    added_expected_errors = [
        new_cases[key]
        for key in added_keys
        if new_cases[key].category == EXPECTED_ERROR
    ]
    removed_cases = [old_cases[key] for key in removed_keys]

    changed_cases: List[Dict[str, Any]] = []
    for key in shared_keys:
        changes = _case_changes(old_cases[key], new_cases[key])
        if changes:
            changed_cases.append(
                {
                    "key": key,
                    "old_category": old_cases[key].category,
                    "new_category": new_cases[key].category,
                    "changes": changes,
                }
            )

    remaining_debt = [
        new_cases[key] for key in sorted(new_cases) if new_cases[key].category == DEBT
    ]

    summary_counts = {
        "added_passing_cases": len(added_passing),
        "added_expected_error_cases": len(added_expected_errors),
        "removed_cases": len(removed_cases),
        "changed_cases": len(changed_cases),
        "remaining_debt": len(remaining_debt),
    }

    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "input_schema_version": INPUT_SCHEMA_VERSION,
        "old": _input_summary(old_artifact),
        "new": _input_summary(new_artifact),
        "summary_counts": summary_counts,
        "direct_cypher_counts_delta": _numeric_delta(
            old_artifact, new_artifact, "direct_cypher_counts"
        ),
        "expected_error_counts_delta": _numeric_delta(
            old_artifact, new_artifact, "expected_error_counts"
        ),
        "added_passing_cases": _sorted_cases(added_passing),
        "added_expected_error_cases": _sorted_cases(added_expected_errors),
        "removed_cases": _sorted_cases(removed_cases),
        "changed_cases": changed_cases,
        "remaining_debt": _sorted_cases(remaining_debt),
        "input_warnings": warnings,
    }


def _format_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return "`" + json.dumps(value, sort_keys=True, separators=(",", ":")) + "`"
    return str(value).replace("|", "\\|")


def _case_summary(case: Mapping[str, Any]) -> str:
    parts = [str(case.get("category", ""))]
    for label, fields in (
        ("cardinality", _CARDINALITY_FIELDS),
        ("order", _ORDER_FIELDS),
        ("type", _TYPE_FIELDS),
        ("outcome", ("outcome",)),
    ):
        value = _first_present(case, fields)
        if value is not None:
            parts.append(f"{label}={_format_cell(value)}")
    return ", ".join(part for part in parts if part)


def _render_case_table(title: str, cases: Sequence[Mapping[str, Any]]) -> List[str]:
    lines = [f"## {title}", ""]
    if not cases:
        lines.extend(["None.", ""])
        return lines
    lines.extend(["| key | summary |", "|---|---|"])
    for case in cases:
        lines.append(f"| {case['key']} | {_case_summary(case)} |")
    lines.append("")
    return lines


def _render_changed_table(changed_cases: Sequence[Mapping[str, Any]]) -> List[str]:
    lines = ["## Changed Cases", ""]
    if not changed_cases:
        lines.extend(["None.", ""])
        return lines
    lines.extend(["| key | field | old | new |", "|---|---|---|---|"])
    for case in changed_cases:
        for change in case.get("changes", ()):
            if not isinstance(change, dict):
                continue
            lines.append(
                "| {key} | {field} | {old} | {new} |".format(
                    key=case.get("key", ""),
                    field=change.get("field", ""),
                    old=_format_cell(change.get("old")),
                    new=_format_cell(change.get("new")),
                )
            )
    lines.append("")
    return lines


def render_markdown(delta: Mapping[str, Any]) -> str:
    counts = delta.get("summary_counts", {})
    if not isinstance(counts, dict):
        counts = {}

    lines = [
        "# Direct-Cypher Snapshot Delta",
        "",
        "| category | count |",
        "|---|---:|",
        f"| Added passing cases | {counts.get('added_passing_cases', 0)} |",
        f"| Added expected-error cases | {counts.get('added_expected_error_cases', 0)} |",
        f"| Removed cases | {counts.get('removed_cases', 0)} |",
        f"| Changed cases | {counts.get('changed_cases', 0)} |",
        f"| Remaining debt | {counts.get('remaining_debt', 0)} |",
        "",
    ]

    warnings = delta.get("input_warnings", ())
    if warnings:
        lines.extend(["## Input Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    for title, key in (
        ("Added Passing Cases", "added_passing_cases"),
        ("Added Expected-Error Cases", "added_expected_error_cases"),
        ("Removed Cases", "removed_cases"),
    ):
        cases = delta.get(key, ())
        if not isinstance(cases, list):
            cases = []
        lines.extend(_render_case_table(title, cases))

    changed_cases = delta.get("changed_cases", ())
    if not isinstance(changed_cases, list):
        changed_cases = []
    lines.extend(_render_changed_table(changed_cases))

    remaining_debt = delta.get("remaining_debt", ())
    if not isinstance(remaining_debt, list):
        remaining_debt = []
    lines.extend(_render_case_table("Remaining Debt", remaining_debt))

    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare two tck-gfql direct-Cypher JSON conformance artifacts and "
            "write structured JSON plus markdown summaries."
        )
    )
    parser.add_argument("old_artifact", type=Path)
    parser.add_argument("new_artifact", type=Path)
    parser.add_argument(
        "--json-output",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
        help=f"Path for the delta JSON artifact (default: {DEFAULT_JSON_OUTPUT})",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=DEFAULT_MARKDOWN_OUTPUT,
        help=f"Path for the markdown summary (default: {DEFAULT_MARKDOWN_OUTPUT})",
    )
    args = parser.parse_args(argv)

    delta = build_delta(_read_json(args.old_artifact), _read_json(args.new_artifact))
    markdown = render_markdown(delta)
    _write_json(args.json_output, delta)
    _write_text(args.markdown_output, markdown)
    print(markdown)
    print(f"JSON delta written: {args.json_output}")
    print(f"Markdown summary written: {args.markdown_output}")


if __name__ == "__main__":
    main()
