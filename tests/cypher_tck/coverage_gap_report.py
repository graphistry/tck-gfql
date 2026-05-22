from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, cast

COVERAGE_GAP_SCHEMA_VERSION = 1
DEFAULT_JSON_OUTPUT = Path("build/coverage-gap-report.json")
DEFAULT_MARKDOWN_OUTPUT = Path("build/coverage-gap-report.md")
DEFAULT_COVERAGE_DATA = Path("build/.coverage.tck-gfql")
DEFAULT_PYTEST_ARGS = ("tests/cypher_tck/test_tck_runner.py", "-q")

TARGET_DIRECTORIES = (
    "graphistry/compute/gfql",
    "graphistry/compute/predicates",
)
TARGET_FILES = (
    "graphistry/compute/ast.py",
    "graphistry/compute/chain.py",
    "graphistry/compute/hop.py",
    "graphistry/compute/gfql_unified.py",
)
PRIORITY_FILES = (
    "graphistry/compute/gfql/cypher/lowering.py",
    "graphistry/compute/gfql/row/pipeline.py",
    "graphistry/compute/gfql/cypher/parser.py",
    "graphistry/compute/gfql/frontends/cypher/binder.py",
    "graphistry/compute/gfql_unified.py",
)

# Coverage-gap report contract:
# - This is a new schema_versioned evidence artifact for pygraphistry GFQL shrink
#   targeting. It does not mutate the #147/#152/#156/#162/#164/#166 contracts.
# - Coverage accounting is restricted to the first-party pygraphistry GFQL source
#   surface listed above; pygraphistry files are read-only inputs.
# - The report identifies zero-hit executable ranges only. It intentionally does
#   not recommend deletion or other code changes; pygraphistry shrink workers own
#   those decisions.


@dataclass(frozen=True)
class RunnerResult:
    returncode: int
    command: tuple[str, ...]


@dataclass(frozen=True)
class FileCoverage:
    path: Path
    relative_path: str
    total_lines: int
    executable_lines: tuple[int, ...]
    missing_lines: tuple[int, ...]
    hit_lines: tuple[int, ...]


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _repo_root_from_graphistry_path(path: Path) -> Path:
    resolved = path.resolve()
    if (resolved / "graphistry" / "compute").is_dir():
        return resolved
    if resolved.name == "graphistry" and (resolved / "compute").is_dir():
        return resolved.parent
    raise ValueError(
        f"{path} does not look like a pygraphistry checkout or graphistry package root"
    )


def resolve_pygraphistry_root(pygraphistry_path: Path | None) -> Path:
    if pygraphistry_path is not None:
        return _repo_root_from_graphistry_path(pygraphistry_path)

    try:
        import graphistry  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "graphistry is required. Set --pygraphistry-path or PYGRAPHISTRY_PATH."
        ) from exc

    package_path = Path(cast(str, graphistry.__file__)).resolve().parent
    return _repo_root_from_graphistry_path(package_path)


def _relative_to_repo(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def discover_target_files(pygraphistry_root: Path) -> list[Path]:
    targets: set[Path] = set()
    for directory in TARGET_DIRECTORIES:
        directory_path = pygraphistry_root / directory
        if directory_path.is_dir():
            targets.update(path for path in directory_path.rglob("*.py") if path.is_file())
    for file_name in TARGET_FILES:
        file_path = pygraphistry_root / file_name
        if file_path.is_file():
            targets.add(file_path)

    priority_index = {path: index for index, path in enumerate(PRIORITY_FILES)}

    def sort_key(path: Path) -> tuple[int, int, str]:
        relative = _relative_to_repo(path, pygraphistry_root)
        priority = priority_index.get(relative)
        if priority is None:
            return (1, 0, relative)
        return (0, priority, relative)

    return sorted(targets, key=sort_key)


def _coverage_include_arg(files: Sequence[Path]) -> str:
    return ",".join(str(path.resolve()) for path in files)


def _pythonpath_for(checkout_dir: Path, pygraphistry_path: Path | None) -> str:
    parts = [str(checkout_dir.resolve())]
    if pygraphistry_path is not None:
        parts.append(str(pygraphistry_path.resolve()))
    existing = os.environ.get("PYTHONPATH")
    if existing:
        parts.append(existing)
    return os.pathsep.join(parts)


def run_scenarios_under_coverage(
    *,
    checkout_dir: Path,
    pygraphistry_path: Path | None,
    coverage_data: Path,
    target_files: Sequence[Path],
    pytest_args: Sequence[str],
) -> RunnerResult:
    if not target_files:
        raise ValueError("coverage target file list is empty")

    coverage_data.parent.mkdir(parents=True, exist_ok=True)
    command = (
        sys.executable,
        "-m",
        "coverage",
        "run",
        "--data-file",
        str(coverage_data),
        "--include",
        _coverage_include_arg(target_files),
        "-m",
        "pytest",
        *pytest_args,
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath_for(checkout_dir, pygraphistry_path)
    completed = subprocess.run(command, cwd=checkout_dir, env=env, check=False)
    return RunnerResult(returncode=completed.returncode, command=tuple(command))


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


def _range_text(ranges: Sequence[Mapping[str, int]], *, limit: int = 12) -> str:
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


def _total_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def analyze_coverage_data(
    *,
    coverage_data: Path,
    pygraphistry_root: Path,
    target_files: Sequence[Path],
) -> list[FileCoverage]:
    try:
        import coverage  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "coverage is required to analyze coverage-gap reports."
        ) from exc

    cov = coverage.Coverage(data_file=str(coverage_data))
    cov.load()
    data = cov.get_data()

    files: list[FileCoverage] = []
    for path in target_files:
        _, statements, _, missing, _ = cov.analysis2(str(path))
        executed = sorted(
            line for line in (data.lines(str(path)) or []) if line in set(statements)
        )
        files.append(
            FileCoverage(
                path=path,
                relative_path=_relative_to_repo(path, pygraphistry_root),
                total_lines=_total_lines(path),
                executable_lines=tuple(sorted(statements)),
                missing_lines=tuple(sorted(missing)),
                hit_lines=tuple(executed),
            )
        )
    return files


def _git_output(repo: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ("git", "-C", str(repo), *args),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = completed.stdout.strip()
    return value or None


def _source_ref(repo: Path) -> dict[str, Any]:
    ref: dict[str, Any] = {"path": str(repo)}
    commit = _git_output(repo, "rev-parse", "HEAD")
    if commit is not None:
        ref["commit"] = commit
    branch = _git_output(repo, "rev-parse", "--abbrev-ref", "HEAD")
    if branch is not None:
        ref["branch"] = branch
    dirty = _git_output(repo, "status", "--short")
    if dirty is not None:
        ref["dirty"] = bool(dirty)
    return ref


def _file_payload(file_coverage: FileCoverage) -> dict[str, Any]:
    executable_count = len(file_coverage.executable_lines)
    missing_count = len(file_coverage.missing_lines)
    hit_count = len(set(file_coverage.executable_lines) - set(file_coverage.missing_lines))
    coverage_percent = None
    if executable_count:
        coverage_percent = round((hit_count / executable_count) * 100, 2)
    return {
        "coverage_percent": coverage_percent,
        "executable_line_count": executable_count,
        "hit_line_count": hit_count,
        "is_priority": file_coverage.relative_path in PRIORITY_FILES,
        "path": file_coverage.relative_path,
        "total_lines": file_coverage.total_lines,
        "zero_hit_line_count": missing_count,
        "zero_hit_ranges": _line_ranges(file_coverage.missing_lines),
    }


def build_report(
    *,
    files: Sequence[FileCoverage],
    checkout_dir: Path,
    pygraphistry_root: Path,
    coverage_data: Path,
    runner: RunnerResult | None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    file_payloads = [_file_payload(file_coverage) for file_coverage in files]
    priority_paths = set(PRIORITY_FILES)
    priority_payloads = [
        payload for payload in file_payloads if payload["path"] in priority_paths
    ]
    executable_total = sum(
        int(payload["executable_line_count"]) for payload in file_payloads
    )
    zero_hit_total = sum(int(payload["zero_hit_line_count"]) for payload in file_payloads)
    hit_total = sum(int(payload["hit_line_count"]) for payload in file_payloads)

    return {
        "schema_version": COVERAGE_GAP_SCHEMA_VERSION,
        "generated_at": generated_at or _iso_now(),
        "source_refs": {
            "tck_gfql": _source_ref(checkout_dir),
            "pygraphistry": _source_ref(pygraphistry_root),
        },
        "coverage_scope": {
            "target_directories": list(TARGET_DIRECTORIES),
            "target_files": list(TARGET_FILES),
            "priority_files": list(PRIORITY_FILES),
            "coverage_data": str(coverage_data),
        },
        "runner": {
            "command": list(runner.command) if runner is not None else [],
            "returncode": runner.returncode if runner is not None else None,
        },
        "summary_counts": {
            "file_count": len(file_payloads),
            "priority_file_count": len(priority_payloads),
            "files_with_zero_hit_ranges": sum(
                1 for payload in file_payloads if payload["zero_hit_line_count"]
            ),
            "executable_line_count": executable_total,
            "hit_line_count": hit_total,
            "zero_hit_line_count": zero_hit_total,
        },
        "priority_files": priority_payloads,
        "files": file_payloads,
    }


def _markdown_table(rows: Sequence[Sequence[object]]) -> list[str]:
    lines = ["| File | Coverage | Hit / executable | Zero-hit ranges |", "|---|---:|---:|---|"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return lines


def _file_row(payload: Mapping[str, Any]) -> tuple[str, str, str, str]:
    coverage_percent = payload.get("coverage_percent")
    coverage_text = "n/a" if coverage_percent is None else f"{coverage_percent}%"
    hit_text = f"{payload.get('hit_line_count', 0)} / {payload.get('executable_line_count', 0)}"
    ranges = cast(Sequence[Mapping[str, int]], payload.get("zero_hit_ranges", []))
    return (
        f"`{payload.get('path')}`",
        coverage_text,
        hit_text,
        _range_text(ranges),
    )


def render_markdown(report: Mapping[str, Any]) -> str:
    counts = cast(Mapping[str, Any], report.get("summary_counts", {}))
    runner = cast(Mapping[str, Any], report.get("runner", {}))
    source_refs = cast(Mapping[str, Any], report.get("source_refs", {}))
    pygraphistry_ref = cast(Mapping[str, Any], source_refs.get("pygraphistry", {}))
    tck_ref = cast(Mapping[str, Any], source_refs.get("tck_gfql", {}))

    lines = [
        "# Coverage Gap Report",
        "",
        "_Evidence-only pygraphistry GFQL coverage inventory for shrink targeting._",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- tck-gfql: `{tck_ref.get('branch', 'unknown')}` "
        f"`{str(tck_ref.get('commit', 'unknown'))[:12]}`",
        f"- pygraphistry: `{pygraphistry_ref.get('branch', 'unknown')}` "
        f"`{str(pygraphistry_ref.get('commit', 'unknown'))[:12]}`",
        f"- Runner return code: `{runner.get('returncode')}`",
        "",
        "## Headline Counts",
        "",
        f"- Files analyzed: `{counts.get('file_count', 0)}`",
        f"- Priority files analyzed: `{counts.get('priority_file_count', 0)}`",
        f"- Files with zero-hit executable ranges: `{counts.get('files_with_zero_hit_ranges', 0)}`",
        f"- Hit executable lines: `{counts.get('hit_line_count', 0)} / {counts.get('executable_line_count', 0)}`",
        f"- Zero-hit executable lines: `{counts.get('zero_hit_line_count', 0)}`",
        "",
        "## Priority Files",
        "",
    ]

    priority_files = cast(Sequence[Mapping[str, Any]], report.get("priority_files", []))
    if priority_files:
        lines.extend(_markdown_table([_file_row(payload) for payload in priority_files]))
    else:
        lines.append("_No priority files were present in the analyzed checkout._")

    lines.extend(["", "## Full Inventory", ""])
    files = cast(Sequence[Mapping[str, Any]], report.get("files", []))
    if files:
        lines.extend(_markdown_table([_file_row(payload) for payload in files]))
    else:
        lines.append("_No files were analyzed._")

    lines.extend(
        [
            "",
            "This report is coverage evidence only; shrink decisions remain with pygraphistry owners.",
            "",
        ]
    )
    return "\n".join(lines)


def build_outputs(
    *,
    checkout_dir: Path,
    pygraphistry_path: Path | None,
    coverage_data: Path,
    json_output: Path,
    markdown_output: Path,
    pytest_args: Sequence[str],
    skip_run: bool = False,
) -> dict[str, Any]:
    pygraphistry_root = resolve_pygraphistry_root(pygraphistry_path)
    target_files = discover_target_files(pygraphistry_root)
    runner = None
    if not skip_run:
        runner = run_scenarios_under_coverage(
            checkout_dir=checkout_dir,
            pygraphistry_path=pygraphistry_path,
            coverage_data=coverage_data,
            target_files=target_files,
            pytest_args=pytest_args,
        )
        if runner.returncode != 0:
            raise SystemExit(runner.returncode)

    files = analyze_coverage_data(
        coverage_data=coverage_data,
        pygraphistry_root=pygraphistry_root,
        target_files=target_files,
    )
    report = build_report(
        files=files,
        checkout_dir=checkout_dir,
        pygraphistry_root=pygraphistry_root,
        coverage_data=coverage_data,
        runner=runner,
    )
    markdown = render_markdown(report)
    _write_json(json_output, report)
    _write_text(markdown_output, markdown)
    return report


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run tck-gfql scenarios under coverage and emit a pygraphistry GFQL "
            "zero-hit range inventory."
        )
    )
    parser.add_argument(
        "--checkout-dir",
        type=Path,
        default=Path.cwd(),
        help="tck-gfql checkout directory (default: current working directory)",
    )
    parser.add_argument(
        "--pygraphistry-path",
        type=Path,
        default=Path(os.environ["PYGRAPHISTRY_PATH"])
        if os.environ.get("PYGRAPHISTRY_PATH")
        else None,
        help="pygraphistry checkout/package root (default: PYGRAPHISTRY_PATH/imported graphistry)",
    )
    parser.add_argument(
        "--coverage-data",
        type=Path,
        default=DEFAULT_COVERAGE_DATA,
        help=f"coverage.py data file path (default: {DEFAULT_COVERAGE_DATA})",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
        help=f"Path for structured JSON output (default: {DEFAULT_JSON_OUTPUT})",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=DEFAULT_MARKDOWN_OUTPUT,
        help=f"Path for markdown output (default: {DEFAULT_MARKDOWN_OUTPUT})",
    )
    parser.add_argument(
        "--pytest-arg",
        action="append",
        dest="pytest_args",
        help=(
            "Pytest argument for the coverage run. May be repeated. "
            "Defaults to tests/cypher_tck/test_tck_runner.py -q."
        ),
    )
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Analyze an existing --coverage-data file without running pytest.",
    )
    args = parser.parse_args(argv)

    pytest_args = tuple(args.pytest_args) if args.pytest_args else DEFAULT_PYTEST_ARGS
    report = build_outputs(
        checkout_dir=args.checkout_dir.resolve(),
        pygraphistry_path=args.pygraphistry_path.resolve()
        if args.pygraphistry_path is not None
        else None,
        coverage_data=args.coverage_data,
        json_output=args.json_output,
        markdown_output=args.markdown_output,
        pytest_args=pytest_args,
        skip_run=args.skip_run,
    )
    markdown = render_markdown(report)
    print(markdown)
    print(f"Coverage-gap JSON written: {args.json_output}")
    print(f"Coverage-gap markdown written: {args.markdown_output}")


if __name__ == "__main__":
    main()
