from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, cast

from tests.cypher_tck import coverage_gap_pr_delta, coverage_gap_report

SCHEMA_VERSION = 1
BASELINE_URL = (
    "https://github.com/graphistry/pygraphistry/issues/1058#issuecomment-4526115525"
)
DEFAULT_OUTPUT_DIR = Path("build/coverage-gap-cumulative")
DEFAULT_JSON_OUTPUT = DEFAULT_OUTPUT_DIR / "coverage-gap-cumulative.json"
DEFAULT_MARKDOWN_OUTPUT = DEFAULT_OUTPUT_DIR / "coverage-gap-cumulative.md"
DEFAULT_REPORT_DIR = DEFAULT_OUTPUT_DIR / "reports"
PRIORITY_FILES = coverage_gap_pr_delta.PRIORITY_FILES

# Coverage-gap cumulative tracker contract:
# - This consumes #177 coverage-gap JSON reports and emits a separate
#   schema-versioned cumulative artifact. It does not change the #177 input
#   schema or any conformance artifact schemas.
# - Output is evidence-only shrink-cycle accounting across pygraphistry master
#   commits. It reports zero-hit executable range movement, not deletion
#   recommendations.
# - Pygraphistry source checkouts are read-only inputs. Commit-driven runs use
#   temporary git worktrees under the output directory rather than editing the
#   user's pygraphistry checkout.


@dataclass(frozen=True)
class ReportPoint:
    label: str
    report: Mapping[str, Any]
    report_path: Path | None = None


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


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


def _missing_lines(report: Mapping[str, Any], path: str) -> set[int] | None:
    payload = _file_map(report).get(path)
    if payload is None:
        return None
    return _range_lines(payload.get("zero_hit_ranges", []))


def _line_count(report: Mapping[str, Any], path: str, key: str) -> int | None:
    payload = _file_map(report).get(path)
    if payload is None:
        return None
    value = payload.get(key)
    return value if isinstance(value, int) else None


def _coverage_percent(report: Mapping[str, Any], path: str) -> float | None:
    payload = _file_map(report).get(path)
    if payload is None:
        return None
    value = payload.get("coverage_percent")
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    return None


def _trajectory(*, opened: int, closed: int) -> str:
    if closed > opened:
        return "gap_closed"
    if opened > closed:
        return "gap_opened"
    if opened or closed:
        return "gap_shuffled"
    return "flat"


def _transition_delta(
    *,
    base: Mapping[str, Any],
    head: Mapping[str, Any],
    from_label: str,
    to_label: str,
) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    opened_total = 0
    closed_total = 0
    for path in PRIORITY_FILES:
        base_missing = _missing_lines(base, path)
        head_missing = _missing_lines(head, path)
        comparison_status = "compared"
        opened: set[int] = set()
        closed: set[int] = set()
        if base_missing is None and head_missing is None:
            comparison_status = "missing_from_reports"
        elif base_missing is None:
            comparison_status = "missing_from_base"
        elif head_missing is None:
            comparison_status = "missing_from_head"
        else:
            opened = head_missing - base_missing
            closed = base_missing - head_missing
        opened_total += len(opened)
        closed_total += len(closed)
        files.append(
            {
                "path": path,
                "comparison_status": comparison_status,
                "opened_zero_hit_line_count": len(opened),
                "opened_zero_hit_ranges": _line_ranges(opened),
                "closed_zero_hit_line_count": len(closed),
                "closed_zero_hit_ranges": _line_ranges(closed),
            }
        )
    return {
        "from_label": from_label,
        "to_label": to_label,
        "opened_zero_hit_line_count": opened_total,
        "closed_zero_hit_line_count": closed_total,
        "trajectory": _trajectory(opened=opened_total, closed=closed_total),
        "files": files,
    }


def _source_ref(report: Mapping[str, Any]) -> Mapping[str, Any]:
    source_refs = report.get("source_refs", {})
    if not isinstance(source_refs, Mapping):
        return {}
    pygraphistry = source_refs.get("pygraphistry", {})
    return pygraphistry if isinstance(pygraphistry, Mapping) else {}


def _point_ref(point: ReportPoint) -> dict[str, Any]:
    ref: dict[str, Any] = {"label": point.label}
    if point.report_path is not None:
        ref["report_path"] = str(point.report_path)
    source_ref = _source_ref(point.report)
    if source_ref:
        ref["source_ref"] = dict(source_ref)
    return ref


def build_cumulative_report(
    points: Sequence[ReportPoint],
    *,
    baseline_url: str = BASELINE_URL,
    generated_at: str | None = None,
) -> dict[str, Any]:
    if len(points) < 2:
        raise ValueError("at least two coverage-gap reports are required")

    baseline = points[0]
    final = points[-1]
    transitions = [
        _transition_delta(
            base=points[index].report,
            head=points[index + 1].report,
            from_label=points[index].label,
            to_label=points[index + 1].label,
        )
        for index in range(len(points) - 1)
    ]

    file_summaries: list[dict[str, Any]] = []
    cumulative_opened_total = 0
    cumulative_closed_total = 0
    gross_opened_total = 0
    gross_closed_total = 0
    unavailable_count = 0
    for path in PRIORITY_FILES:
        baseline_missing = _missing_lines(baseline.report, path)
        final_missing = _missing_lines(final.report, path)
        comparison_status = "compared"
        cumulative_opened: set[int] = set()
        cumulative_closed: set[int] = set()
        if baseline_missing is None and final_missing is None:
            comparison_status = "missing_from_reports"
        elif baseline_missing is None:
            comparison_status = "missing_from_baseline"
        elif final_missing is None:
            comparison_status = "missing_from_final"
        else:
            cumulative_opened = final_missing - baseline_missing
            cumulative_closed = baseline_missing - final_missing
        if comparison_status != "compared":
            unavailable_count += 1

        gross_opened = 0
        gross_closed = 0
        for transition in transitions:
            for item in cast(Sequence[Mapping[str, Any]], transition["files"]):
                if item.get("path") != path:
                    continue
                gross_opened += int(item.get("opened_zero_hit_line_count", 0))
                gross_closed += int(item.get("closed_zero_hit_line_count", 0))

        cumulative_opened_total += len(cumulative_opened)
        cumulative_closed_total += len(cumulative_closed)
        gross_opened_total += gross_opened
        gross_closed_total += gross_closed
        baseline_zero_hit_count = (
            len(baseline_missing) if baseline_missing is not None else None
        )
        final_zero_hit_count = len(final_missing) if final_missing is not None else None
        net_delta = (
            final_zero_hit_count - baseline_zero_hit_count
            if baseline_zero_hit_count is not None and final_zero_hit_count is not None
            else None
        )
        file_summaries.append(
            {
                "path": path,
                "comparison_status": comparison_status,
                "baseline_zero_hit_line_count": baseline_zero_hit_count,
                "final_zero_hit_line_count": final_zero_hit_count,
                "net_zero_hit_line_delta": net_delta,
                "baseline_coverage_percent": _coverage_percent(baseline.report, path),
                "final_coverage_percent": _coverage_percent(final.report, path),
                "baseline_executable_line_count": _line_count(
                    baseline.report, path, "executable_line_count"
                ),
                "final_executable_line_count": _line_count(
                    final.report, path, "executable_line_count"
                ),
                "cumulative_opened_zero_hit_line_count": len(cumulative_opened),
                "cumulative_opened_zero_hit_ranges": _line_ranges(cumulative_opened),
                "cumulative_closed_zero_hit_line_count": len(cumulative_closed),
                "cumulative_closed_zero_hit_ranges": _line_ranges(cumulative_closed),
                "gross_opened_zero_hit_line_count": gross_opened,
                "gross_closed_zero_hit_line_count": gross_closed,
                "trajectory": _trajectory(
                    opened=len(cumulative_opened),
                    closed=len(cumulative_closed),
                ),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at or _iso_now(),
        "status": "ready",
        "baseline_url": baseline_url,
        "cycle": {
            "baseline_label": baseline.label,
            "final_label": final.label,
            "report_count": len(points),
            "transition_count": len(transitions),
        },
        "summary_counts": {
            "priority_file_count": len(PRIORITY_FILES),
            "unavailable_priority_file_count": unavailable_count,
            "cumulative_opened_zero_hit_line_count": cumulative_opened_total,
            "cumulative_closed_zero_hit_line_count": cumulative_closed_total,
            "net_zero_hit_line_delta": (
                cumulative_opened_total - cumulative_closed_total
            ),
            "gross_opened_zero_hit_line_count": gross_opened_total,
            "gross_closed_zero_hit_line_count": gross_closed_total,
            "files_with_cumulative_opens": sum(
                1
                for item in file_summaries
                if item["cumulative_opened_zero_hit_line_count"]
            ),
            "files_with_cumulative_closures": sum(
                1
                for item in file_summaries
                if item["cumulative_closed_zero_hit_line_count"]
            ),
        },
        "trajectory": _trajectory(
            opened=cumulative_opened_total,
            closed=cumulative_closed_total,
        ),
        "report_points": [_point_ref(point) for point in points],
        "transitions": transitions,
        "files": file_summaries,
        "top_closures": _top_files(
            file_summaries,
            count_key="cumulative_closed_zero_hit_line_count",
            ranges_key="cumulative_closed_zero_hit_ranges",
        ),
        "top_opens": _top_files(
            file_summaries,
            count_key="cumulative_opened_zero_hit_line_count",
            ranges_key="cumulative_opened_zero_hit_ranges",
        ),
    }


def _top_files(
    files: Sequence[Mapping[str, Any]],
    *,
    count_key: str,
    ranges_key: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    ranked = sorted(
        (item for item in files if int(item.get(count_key, 0)) > 0),
        key=lambda item: (-int(item.get(count_key, 0)), str(item.get("path", ""))),
    )
    return [
        {
            "path": item.get("path"),
            "line_count": item.get(count_key),
            "ranges": item.get(ranges_key, []),
        }
        for item in ranked[:limit]
    ]


def _headline(report: Mapping[str, Any]) -> str:
    counts = cast(Mapping[str, Any], report.get("summary_counts", {}))
    trajectory = report.get("trajectory")
    net = int(counts.get("net_zero_hit_line_delta", 0))
    closed = int(counts.get("cumulative_closed_zero_hit_line_count", 0))
    opened = int(counts.get("cumulative_opened_zero_hit_line_count", 0))
    if trajectory == "gap_closed":
        return (
            f"Cycle is net closing coverage gaps: {closed} zero-hit lines closed, "
            f"{opened} opened, net {net}."
        )
    if trajectory == "gap_opened":
        return (
            f"Cycle is net opening coverage gaps: {opened} zero-hit lines opened, "
            f"{closed} closed, net +{net}."
        )
    if trajectory == "gap_shuffled":
        return (
            f"Cycle is shuffling coverage gaps: {closed} zero-hit lines closed and "
            f"{opened} opened with no net reduction."
        )
    return "Cycle is flat: no cumulative priority-file zero-hit movement detected."


def _delta_text(value: object) -> str:
    if not isinstance(value, int):
        return "n/a"
    return f"+{value}" if value > 0 else str(value)


def _render_file_table(files: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [
        "| File | Trajectory | Net zero-hit delta | Closed ranges | Opened ranges | Gross closed/opened |",
        "|---|---|---:|---|---|---:|",
    ]
    for item in files:
        closed = cast(
            Sequence[Mapping[str, int]],
            item.get("cumulative_closed_zero_hit_ranges", []),
        )
        opened = cast(
            Sequence[Mapping[str, int]],
            item.get("cumulative_opened_zero_hit_ranges", []),
        )
        gross = (
            f"{item.get('gross_closed_zero_hit_line_count', 0)} / "
            f"{item.get('gross_opened_zero_hit_line_count', 0)}"
        )
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{item.get('path')}`",
                    str(item.get("trajectory", "flat")),
                    _delta_text(item.get("net_zero_hit_line_delta")),
                    _range_text(closed),
                    _range_text(opened),
                    gross,
                )
            )
            + " |"
        )
    return lines


def _render_top_table(title: str, files: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not files:
        lines.append("_None._")
        return lines
    lines.extend(["| File | Lines | Ranges |", "|---|---:|---|"])
    for item in files:
        ranges = cast(Sequence[Mapping[str, int]], item.get("ranges", []))
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{item.get('path')}`",
                    str(item.get("line_count", 0)),
                    _range_text(ranges),
                )
            )
            + " |"
        )
    return lines


def render_markdown(report: Mapping[str, Any]) -> str:
    counts = cast(Mapping[str, Any], report.get("summary_counts", {}))
    cycle = cast(Mapping[str, Any], report.get("cycle", {}))
    lines = [
        "# Coverage Gap Cumulative Tracker",
        "",
        "_Evidence-only pygraphistry GFQL shrink-cycle coverage-gap accounting._",
        "",
        f"- Baseline: [post-#1609 coverage-gap report]({report.get('baseline_url')})",
        f"- Cycle: `{cycle.get('baseline_label')}` -> `{cycle.get('final_label')}`",
        f"- Reports compared: `{cycle.get('report_count', 0)}`",
        f"- Trajectory: `{report.get('trajectory')}`",
        f"- Headline: {_headline(report)}",
        "",
        "## Headline Counts",
        "",
        f"- Cumulative zero-hit lines closed: `{counts.get('cumulative_closed_zero_hit_line_count', 0)}`",
        f"- Cumulative zero-hit lines opened: `{counts.get('cumulative_opened_zero_hit_line_count', 0)}`",
        f"- Net zero-hit line delta: `{_delta_text(counts.get('net_zero_hit_line_delta'))}`",
        f"- Gross closed/opened movement across transitions: `{counts.get('gross_closed_zero_hit_line_count', 0)} / {counts.get('gross_opened_zero_hit_line_count', 0)}`",
        f"- Priority files unavailable in baseline/final comparison: `{counts.get('unavailable_priority_file_count', 0)}`",
        "",
    ]
    lines.extend(
        _render_top_table(
            "Top 5 Closures",
            cast(Sequence[Mapping[str, Any]], report.get("top_closures", [])),
        )
    )
    lines.extend([""])
    lines.extend(
        _render_top_table(
            "Top 5 Opens",
            cast(Sequence[Mapping[str, Any]], report.get("top_opens", [])),
        )
    )
    lines.extend(["", "## Per-File Cumulative Delta", ""])
    files = cast(Sequence[Mapping[str, Any]], report.get("files", []))
    if files:
        lines.extend(_render_file_table(files))
    else:
        lines.append("_No priority files were compared._")
    lines.extend(
        [
            "",
            "This report is coverage evidence only; shrink decisions remain with pygraphistry owners.",
            "",
        ]
    )
    return "\n".join(lines)


def _parse_report_arg(value: str) -> tuple[str | None, Path]:
    if "=" not in value:
        return None, Path(value)
    label, path = value.split("=", 1)
    if not label or not path:
        raise ValueError(f"invalid report argument {value!r}; expected LABEL=PATH")
    return label, Path(path)


def read_report_points(values: Sequence[str]) -> list[ReportPoint]:
    points: list[ReportPoint] = []
    for index, value in enumerate(values):
        label, path = _parse_report_arg(value)
        report = _read_json(path)
        source_ref = _source_ref(report)
        fallback_label = str(source_ref.get("commit") or path.stem)
        points.append(
            ReportPoint(
                label=label or (fallback_label if fallback_label else f"report-{index}"),
                report=report,
                report_path=path,
            )
        )
    return points


def _matches_commit_prefix(sha: str, commit: str) -> bool:
    left = sha.lower()
    right = commit.lower()
    return left.startswith(right) or right.startswith(left)


def read_github_commit_refs(
    path: Path,
    *,
    limit: int | None = None,
    baseline_commit: str | None = None,
) -> list[str]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, list):
        raise ValueError(f"{path} must contain a GitHub commits JSON array")
    refs: list[str] = []
    for item in parsed:
        if not isinstance(item, Mapping):
            continue
        sha = item.get("sha")
        if isinstance(sha, str) and sha:
            refs.append(sha)
    refs.reverse()
    if baseline_commit is not None:
        for index, sha in enumerate(refs):
            if _matches_commit_prefix(sha, baseline_commit):
                refs = refs[index + 1 :]
                break
        else:
            raise ValueError(f"baseline commit {baseline_commit!r} not found in {path}")
    if limit is not None:
        refs = refs[-limit:]
    return refs


def _safe_commit_dir(commit: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z_.-]+", "-", commit)
    return normalized[:40] or "commit"


def _run_git(repo: Path, *args: str) -> None:
    subprocess.run(("git", "-C", str(repo), *args), check=True)


def _run_coverage_for_commits(
    *,
    commits: Sequence[str],
    checkout_dir: Path,
    pygraphistry_repo: Path,
    report_dir: Path,
    pytest_args: Sequence[str],
    keep_worktrees: bool,
) -> list[ReportPoint]:
    points: list[ReportPoint] = []
    report_dir.mkdir(parents=True, exist_ok=True)
    for commit in commits:
        safe = _safe_commit_dir(commit)
        worktree = report_dir / f"pygraphistry-{safe}"
        json_output = report_dir / f"coverage-gap-{safe}.json"
        markdown_output = report_dir / f"coverage-gap-{safe}.md"
        coverage_data = report_dir / f".coverage-{safe}"
        try:
            if not worktree.exists():
                _run_git(
                    pygraphistry_repo,
                    "worktree",
                    "add",
                    "--detach",
                    str(worktree),
                    commit,
                )
            report = coverage_gap_report.build_outputs(
                checkout_dir=checkout_dir,
                pygraphistry_path=worktree,
                coverage_data=coverage_data,
                json_output=json_output,
                markdown_output=markdown_output,
                pytest_args=pytest_args,
            )
            points.append(
                ReportPoint(label=commit[:12], report=report, report_path=json_output)
            )
        finally:
            if worktree.exists() and not keep_worktrees:
                _run_git(pygraphistry_repo, "worktree", "remove", "--force", str(worktree))
    return points


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build cumulative pygraphistry GFQL coverage-gap JSON/markdown from "
            "a sequence of #177 coverage-gap reports."
        )
    )
    parser.add_argument(
        "--report",
        action="append",
        default=[],
        help="Coverage-gap report path, optionally LABEL=PATH. Repeat in cycle order.",
    )
    parser.add_argument(
        "--github-commits-json",
        type=Path,
        help=(
            "Optional JSON array from `gh api repos/graphistry/pygraphistry/commits`; "
            "used with --pygraphistry-repo to regenerate reports in chronological order."
        ),
    )
    parser.add_argument(
        "--commit",
        action="append",
        default=[],
        help="Pygraphistry commit SHA to regenerate. Repeat in cycle order.",
    )
    parser.add_argument("--commit-limit", type=int)
    parser.add_argument(
        "--baseline-commit",
        help=(
            "When reading --github-commits-json, discard commits up to and "
            "including this baseline SHA/prefix."
        ),
    )
    parser.add_argument("--checkout-dir", type=Path, default=Path.cwd())
    parser.add_argument("--pygraphistry-repo", type=Path)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--baseline-url", default=BASELINE_URL)
    parser.add_argument("--generated-at")
    parser.add_argument(
        "--pytest-arg",
        action="append",
        dest="pytest_args",
        help=(
            "Pytest argument for generated coverage runs. May be repeated. "
            "Defaults to tests/cypher_tck/test_tck_runner.py -q."
        ),
    )
    parser.add_argument(
        "--keep-worktrees",
        action="store_true",
        help="Keep temporary pygraphistry worktrees under --report-dir after generation.",
    )
    args = parser.parse_args(argv)

    points = read_report_points(args.report)
    commits = list(args.commit)
    if args.github_commits_json is not None:
        commits.extend(
            read_github_commit_refs(
                args.github_commits_json,
                limit=args.commit_limit,
                baseline_commit=args.baseline_commit,
            )
        )
    if commits:
        if args.pygraphistry_repo is None:
            raise SystemExit("--pygraphistry-repo is required with --commit inputs")
        pytest_args = (
            tuple(args.pytest_args)
            if args.pytest_args
            else coverage_gap_report.DEFAULT_PYTEST_ARGS
        )
        points.extend(
            _run_coverage_for_commits(
                commits=commits,
                checkout_dir=args.checkout_dir.resolve(),
                pygraphistry_repo=args.pygraphistry_repo.resolve(),
                report_dir=args.report_dir.resolve(),
                pytest_args=pytest_args,
                keep_worktrees=args.keep_worktrees,
            )
        )
    if len(points) < 2:
        raise SystemExit("at least two --report/--commit inputs are required")

    report = build_cumulative_report(
        points,
        baseline_url=args.baseline_url,
        generated_at=args.generated_at,
    )
    markdown = render_markdown(report)
    _write_json(args.json_output, report)
    _write_text(args.markdown_output, markdown)
    print(markdown)
    print(f"Coverage-gap cumulative JSON written: {args.json_output}")
    print(f"Coverage-gap cumulative markdown written: {args.markdown_output}")


if __name__ == "__main__":
    main()
