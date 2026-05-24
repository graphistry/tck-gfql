from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, cast

COMMENT_MARKER = "<!-- tck-gfql-coverage-gap-pr-delta -->"
BASELINE_URL = (
    "https://github.com/graphistry/pygraphistry/issues/1058#issuecomment-4526115525"
)
SCHEMA_VERSION = 1
DEFAULT_OUTPUT_DIR = Path("build/pr-conformance-summary")
DEFAULT_JSON_OUTPUT = DEFAULT_OUTPUT_DIR / "coverage-gap-pr-delta.json"
DEFAULT_MARKDOWN_OUTPUT = DEFAULT_OUTPUT_DIR / "coverage-gap-pr-delta.md"
DEFAULT_COMMENT_OUTPUT = DEFAULT_OUTPUT_DIR / "coverage-gap-pr-delta-comment.md"

PRIORITY_FILES = (
    "graphistry/compute/gfql/cypher/lowering.py",
    "graphistry/compute/gfql/row/pipeline.py",
    "graphistry/compute/gfql/cypher/parser.py",
    "graphistry/compute/gfql/frontends/cypher/binder.py",
    "graphistry/compute/gfql_unified.py",
    "graphistry/compute/gfql/cypher/call_procedures.py",
    "graphistry/compute/gfql/call/validation.py",
    "graphistry/compute/gfql/temporal/constructors.py",
    "graphistry/compute/gfql/expr_parser.py",
)

# Coverage-gap PR delta contract:
# - This consumes two #177 coverage-gap JSON reports. It does not change that
#   report schema or the conformance schemas from #147/#152/#156/#162/#164/#166.
# - Output is evidence-only PR-comment material: newly uncovered executable
#   lines, newly covered executable lines, and per-file coverage percent deltas.
# - Comments are suppressed unless the pygraphistry PR touches at least one
#   requested priority file.


def _read_json(path: Path) -> dict[str, Any]:
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


def _range_lines(ranges: object) -> set[int]:
    lines: set[int] = set()
    if not isinstance(ranges, Sequence):
        return lines
    for item in ranges:
        if not isinstance(item, Mapping):
            continue
        start = item.get("start")
        end = item.get("end")
        if not isinstance(start, int) or not isinstance(end, int):
            continue
        lines.update(range(start, end + 1))
    return lines


def _line_ranges(lines: Iterable[int]) -> list[dict[str, int]]:
    sorted_lines = sorted(set(lines))
    if not sorted_lines:
        return []

    ranges: list[dict[str, int]] = []
    start = previous = sorted_lines[0]
    for line in sorted_lines[1:]:
        if line == previous + 1:
            previous = line
            continue
        ranges.append({"start": start, "end": previous})
        start = previous = line
    ranges.append({"start": start, "end": previous})
    return ranges


def _range_text(ranges: Sequence[Mapping[str, int]], *, limit: int = 8) -> str:
    if not ranges:
        return "none"
    rendered: list[str] = []
    for item in ranges[:limit]:
        start = item["start"]
        end = item["end"]
        rendered.append(str(start) if start == end else f"{start}-{end}")
    remaining = len(ranges) - limit
    if remaining > 0:
        rendered.append(f"+{remaining} more")
    return ", ".join(rendered)


def _changed_paths(changed_files: Sequence[str]) -> list[str]:
    priority = set(PRIORITY_FILES)
    normalized = {path.strip().lstrip("./") for path in changed_files if path.strip()}
    return [path for path in PRIORITY_FILES if path in priority and path in normalized]


def _file_map(report: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    files = report.get("files", [])
    if not isinstance(files, Sequence):
        return {}
    mapped: dict[str, Mapping[str, Any]] = {}
    for payload in files:
        if not isinstance(payload, Mapping):
            continue
        path = payload.get("path")
        if isinstance(path, str):
            mapped[path] = payload
    return mapped


def _percent_delta(base: object, head: object) -> float | None:
    if not isinstance(base, (int, float)) or not isinstance(head, (int, float)):
        return None
    return round(float(head) - float(base), 2)


def _line_count(payload: Mapping[str, Any], key: str) -> int | None:
    value = payload.get(key)
    return value if isinstance(value, int) else None


def _source_refs(report: Mapping[str, Any]) -> Mapping[str, Any]:
    source_refs = report.get("source_refs", {})
    return source_refs if isinstance(source_refs, Mapping) else {}


def build_delta(
    *,
    base_report: Mapping[str, Any] | None,
    head_report: Mapping[str, Any] | None,
    changed_files: Sequence[str],
    baseline_url: str = BASELINE_URL,
    base_label: str = "pygraphistry merge-base",
    head_label: str = "pygraphistry PR head",
) -> dict[str, Any]:
    touched_priority_files = _changed_paths(changed_files)
    if not touched_priority_files:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "suppressed",
            "suppression_reason": "no priority files touched",
            "baseline_url": baseline_url,
            "base_label": base_label,
            "head_label": head_label,
            "priority_files": list(PRIORITY_FILES),
            "touched_priority_files": [],
            "summary_counts": {
                "touched_priority_file_count": 0,
                "newly_uncovered_line_count": 0,
                "newly_covered_line_count": 0,
                "files_with_regressions": 0,
                "files_with_gains": 0,
            },
            "files": [],
        }

    if base_report is None or head_report is None:
        raise ValueError(
            "base_report and head_report are required when priority files changed"
        )

    base_files = _file_map(base_report)
    head_files = _file_map(head_report)
    file_deltas: list[dict[str, Any]] = []
    newly_uncovered_total = 0
    newly_covered_total = 0

    for path in touched_priority_files:
        base_payload = base_files.get(path, {})
        head_payload = head_files.get(path, {})
        base_present = path in base_files
        head_present = path in head_files
        comparison_status = "compared"
        if not base_present and not head_present:
            comparison_status = "missing_from_reports"
        elif not base_present:
            comparison_status = "missing_from_base"
        elif not head_present:
            comparison_status = "missing_from_head"

        newly_uncovered: list[int] = []
        newly_covered: list[int] = []
        if comparison_status == "compared":
            base_missing = _range_lines(base_payload.get("zero_hit_ranges", []))
            head_missing = _range_lines(head_payload.get("zero_hit_ranges", []))
            newly_uncovered = sorted(head_missing - base_missing)
            newly_covered = sorted(base_missing - head_missing)
        newly_uncovered_total += len(newly_uncovered)
        newly_covered_total += len(newly_covered)
        file_deltas.append(
            {
                "path": path,
                "comparison_status": comparison_status,
                "base_coverage_percent": base_payload.get("coverage_percent"),
                "head_coverage_percent": head_payload.get("coverage_percent"),
                "net_coverage_percent_delta": (
                    _percent_delta(
                        base_payload.get("coverage_percent"),
                        head_payload.get("coverage_percent"),
                    )
                    if comparison_status == "compared"
                    else None
                ),
                "base_hit_line_count": _line_count(base_payload, "hit_line_count"),
                "head_hit_line_count": _line_count(head_payload, "hit_line_count"),
                "base_executable_line_count": _line_count(
                    base_payload, "executable_line_count"
                ),
                "head_executable_line_count": _line_count(
                    head_payload, "executable_line_count"
                ),
                "base_zero_hit_line_count": _line_count(
                    base_payload, "zero_hit_line_count"
                ),
                "head_zero_hit_line_count": _line_count(
                    head_payload, "zero_hit_line_count"
                ),
                "newly_uncovered_line_count": len(newly_uncovered),
                "newly_uncovered_ranges": _line_ranges(newly_uncovered),
                "newly_covered_line_count": len(newly_covered),
                "newly_covered_ranges": _line_ranges(newly_covered),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
        "baseline_url": baseline_url,
        "base_label": base_label,
        "head_label": head_label,
        "priority_files": list(PRIORITY_FILES),
        "touched_priority_files": touched_priority_files,
        "source_refs": {
            "base": _source_refs(base_report),
            "head": _source_refs(head_report),
        },
        "summary_counts": {
            "touched_priority_file_count": len(touched_priority_files),
            "newly_uncovered_line_count": newly_uncovered_total,
            "newly_covered_line_count": newly_covered_total,
            "files_with_regressions": sum(
                1 for item in file_deltas if item["newly_uncovered_line_count"]
            ),
            "files_with_gains": sum(
                1 for item in file_deltas if item["newly_covered_line_count"]
            ),
        },
        "files": file_deltas,
    }


def build_pending_delta(
    *,
    changed_files: Sequence[str],
    baseline_url: str = BASELINE_URL,
    base_label: str = "pygraphistry merge-base",
    head_label: str = "pygraphistry PR head",
) -> dict[str, Any]:
    touched_priority_files = _changed_paths(changed_files)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "pending",
        "baseline_url": baseline_url,
        "base_label": base_label,
        "head_label": head_label,
        "priority_files": list(PRIORITY_FILES),
        "touched_priority_files": touched_priority_files,
        "summary_counts": {
            "touched_priority_file_count": len(touched_priority_files),
            "newly_uncovered_line_count": 0,
            "newly_covered_line_count": 0,
            "files_with_regressions": 0,
            "files_with_gains": 0,
        },
        "files": [],
    }


def _delta_text(value: object) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    prefix = "+" if value > 0 else ""
    return f"{prefix}{value:.2f} pp"


def _render_delta_table(files: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [
        "| File | Status | Coverage delta | Newly-uncovered lines | Newly-covered lines |",
        "|---|---|---:|---|---|",
    ]
    for item in files:
        uncovered = cast(
            Sequence[Mapping[str, int]], item.get("newly_uncovered_ranges", [])
        )
        covered = cast(
            Sequence[Mapping[str, int]], item.get("newly_covered_ranges", [])
        )
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{item.get('path')}`",
                    str(item.get("comparison_status", "compared")),
                    _delta_text(item.get("net_coverage_percent_delta")),
                    _range_text(uncovered),
                    _range_text(covered),
                )
            )
            + " |"
        )
    return lines


def render_markdown(delta: Mapping[str, Any]) -> str:
    status = delta.get("status")
    counts = cast(Mapping[str, Any], delta.get("summary_counts", {}))
    lines = [
        "# Coverage Gap PR Delta",
        "",
        "_Evidence-only pygraphistry GFQL coverage delta for shrink PR review._",
        "",
        f"- Baseline: [post-#1609 coverage-gap report]({delta.get('baseline_url')})",
        f"- Base: `{delta.get('base_label')}`",
        f"- Head: `{delta.get('head_label')}`",
    ]
    if status == "suppressed":
        lines.extend(
            [
                "- Status: suppressed because no requested priority files were touched.",
                "",
                "No coverage-gap PR comment should be posted for this run.",
                "",
            ]
        )
        return "\n".join(lines)
    if status == "pending":
        lines.extend(
            [
                "- Status: pending coverage run because a requested priority file was touched.",
                "",
                "Coverage-gap PR delta artifacts will be regenerated after base/head coverage runs.",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            f"- Touched priority files: `{counts.get('touched_priority_file_count', 0)}`",
            f"- Newly-uncovered executable lines: `{counts.get('newly_uncovered_line_count', 0)}`",
            f"- Newly-covered executable lines: `{counts.get('newly_covered_line_count', 0)}`",
            "",
            "## Priority File Deltas",
            "",
        ]
    )
    files = cast(Sequence[Mapping[str, Any]], delta.get("files", []))
    if files:
        lines.extend(_render_delta_table(files))
    else:
        lines.append("_No priority file deltas were produced._")
    lines.extend(
        [
            "",
            "This comment is coverage evidence only; shrink decisions remain with pygraphistry owners.",
            "",
        ]
    )
    return "\n".join(lines)


def render_comment(delta: Mapping[str, Any], *, json_artifact_name: str) -> str:
    lines = [
        COMMENT_MARKER,
        "",
        "_Automated pygraphistry GFQL coverage-gap delta for this PR._",
        "",
        f"- Baseline: [post-#1609 coverage-gap report]({delta.get('baseline_url')})",
        f"- Base: `{delta.get('base_label')}`",
        f"- Head: `{delta.get('head_label')}`",
        f"- Structured artifact: `{json_artifact_name}`",
        "",
    ]
    markdown = render_markdown(delta).splitlines()
    if markdown and markdown[0] == "# Coverage Gap PR Delta":
        markdown = markdown[1:]
    lines.extend(line for line in markdown if line != "")
    lines.append("")
    return "\n".join(lines)


def read_changed_files(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def write_github_output(path: Path, *, should_comment: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"should_comment={'true' if should_comment else 'false'}\n")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate coverage-gap PR delta JSON/markdown/comment artifacts from "
            "two #177 coverage-gap reports."
        )
    )
    parser.add_argument("--base-report-json", type=Path)
    parser.add_argument("--head-report-json", type=Path)
    parser.add_argument("--changed-files", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--comment-markdown", type=Path, default=DEFAULT_COMMENT_OUTPUT)
    parser.add_argument("--baseline-url", default=BASELINE_URL)
    parser.add_argument("--base-label", default="pygraphistry merge-base")
    parser.add_argument("--head-label", default="pygraphistry PR head")
    parser.add_argument("--json-artifact-name", default="coverage-gap-pr-delta")
    parser.add_argument(
        "--allow-suppressed-without-reports",
        action="store_true",
        help="Allow no-priority-file suppression before coverage reports exist.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help=(
            "Only inspect changed files and write a pending/suppressed artifact. "
            "Use this before deciding whether to run expensive coverage jobs."
        ),
    )
    parser.add_argument(
        "--github-output",
        type=Path,
        default=Path(os.environ["GITHUB_OUTPUT"])
        if os.environ.get("GITHUB_OUTPUT")
        else None,
        help="Optional GitHub Actions output file for should_comment=true/false.",
    )
    args = parser.parse_args(argv)

    changed_files = read_changed_files(args.changed_files)
    touched_priority = _changed_paths(changed_files)
    base_report = None
    head_report = None
    if args.preflight_only and touched_priority:
        delta = build_pending_delta(
            changed_files=changed_files,
            baseline_url=args.baseline_url,
            base_label=args.base_label,
            head_label=args.head_label,
        )
    elif touched_priority or not args.allow_suppressed_without_reports:
        if args.base_report_json is None or args.head_report_json is None:
            raise SystemExit(
                "--base-report-json and --head-report-json are required when "
                "priority files changed"
            )
        base_report = _read_json(args.base_report_json)
        head_report = _read_json(args.head_report_json)
        delta = build_delta(
            base_report=base_report,
            head_report=head_report,
            changed_files=changed_files,
            baseline_url=args.baseline_url,
            base_label=args.base_label,
            head_label=args.head_label,
        )
    else:
        delta = build_delta(
            base_report=base_report,
            head_report=head_report,
            changed_files=changed_files,
            baseline_url=args.baseline_url,
            base_label=args.base_label,
            head_label=args.head_label,
        )
    markdown = render_markdown(delta)
    _write_json(args.json_output, delta)
    _write_text(args.markdown_output, markdown)
    _write_text(
        args.comment_markdown,
        render_comment(delta, json_artifact_name=args.json_artifact_name),
    )
    should_comment = delta.get("status") != "suppressed"
    if args.github_output is not None:
        write_github_output(args.github_output, should_comment=should_comment)

    print(f"Coverage-gap PR delta JSON written: {args.json_output}")
    print(f"Coverage-gap PR delta markdown written: {args.markdown_output}")
    print(f"Coverage-gap PR delta comment written: {args.comment_markdown}")
    print(f"Coverage-gap PR delta should_comment={str(should_comment).lower()}")


if __name__ == "__main__":
    main()
