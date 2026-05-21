from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.cypher_tck import (
    capability_debt_manifest,
    snapshot_delta,
    unified_conformance_summary,
)

COMMENT_MARKER = "<!-- tck-gfql-unified-conformance-summary -->"
DEFAULT_OUTPUT_DIR = Path("build/pr-conformance-summary")
DEFAULT_COMMENT_FILENAME = "unified-conformance-pr-comment.md"


def _resolve(path: Path, *, root: Path) -> Path:
    if path.is_absolute():
        return path
    return root / path


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


def _pythonpath_for(checkout_dir: Path, pygraphistry_path: Path | None) -> str:
    parts = [str(checkout_dir)]
    if pygraphistry_path is not None:
        parts.append(str(pygraphistry_path))
    existing = os.environ.get("PYTHONPATH")
    if existing:
        parts.append(existing)
    return os.pathsep.join(parts)


def _run_report(
    *,
    checkout_dir: Path,
    output_path: Path,
    pygraphistry_path: Path | None,
) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath_for(checkout_dir, pygraphistry_path)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "tests.cypher_tck.report",
            "--json-output",
            str(output_path),
        ],
        check=True,
        cwd=checkout_dir,
        env=env,
    )


def _has_case_delta(delta: Mapping[str, Any]) -> bool:
    counts = delta.get("summary_counts", {})
    if not isinstance(counts, Mapping):
        return True
    delta_keys = (
        "added_passing_cases",
        "added_expected_error_cases",
        "removed_cases",
        "changed_cases",
    )
    return any(counts.get(key, 0) for key in delta_keys)


def render_comment(
    *,
    markdown_summary: str,
    delta: Mapping[str, Any],
    base_label: str,
    head_label: str,
    json_artifact_name: str,
) -> str:
    lines = [
        COMMENT_MARKER,
        "",
        "_Automated tck-gfql conformance summary for this PR._",
        "",
        f"- Base: `{base_label}`",
        f"- Head: `{head_label}`",
        f"- Structured artifact: `{json_artifact_name}`",
    ]
    if not _has_case_delta(delta):
        lines.append("- Direct-Cypher delta: no added, removed, or changed cases.")
    lines.extend(["", markdown_summary.rstrip(), ""])
    return "\n".join(lines)


def build_outputs(
    *,
    base_dir: Path,
    head_dir: Path,
    output_dir: Path,
    base_report_json: Path,
    head_report_json: Path,
    manifest_path: Path,
    snapshot_delta_json: Path,
    snapshot_delta_markdown: Path,
    summary_json: Path,
    summary_markdown: Path,
    comment_markdown: Path,
    base_label: str,
    head_label: str,
    pygraphistry_path: Path | None = None,
    generate_reports: bool = True,
    json_artifact_name: str = "unified-conformance-summary",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if generate_reports:
        _run_report(
            checkout_dir=base_dir,
            output_path=base_report_json,
            pygraphistry_path=pygraphistry_path,
        )
        _run_report(
            checkout_dir=head_dir,
            output_path=head_report_json,
            pygraphistry_path=pygraphistry_path,
        )

    delta = snapshot_delta.build_delta(
        _read_json(base_report_json),
        _read_json(head_report_json),
    )
    delta_markdown = snapshot_delta.render_markdown(delta)
    _write_json(snapshot_delta_json, delta)
    _write_text(snapshot_delta_markdown, delta_markdown)

    summary = unified_conformance_summary.build_summary(
        _read_json(head_report_json),
        _read_json(manifest_path),
        delta,
    )
    markdown = unified_conformance_summary.render_markdown(summary)
    _write_json(summary_json, summary)
    _write_text(summary_markdown, markdown)
    _write_text(
        comment_markdown,
        render_comment(
            markdown_summary=markdown,
            delta=delta,
            base_label=base_label,
            head_label=head_label,
            json_artifact_name=json_artifact_name,
        ),
    )
    return summary


def _default_label(env_name: str, fallback: str) -> str:
    value = os.environ.get(env_name)
    return value if value else fallback


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate PR-comment markdown and JSON artifacts for the unified "
            "tck-gfql conformance summary."
        )
    )
    parser.add_argument("--base-dir", type=Path, required=True)
    parser.add_argument("--head-dir", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--base-report-json", type=Path)
    parser.add_argument("--head-report-json", type=Path)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=capability_debt_manifest.DEFAULT_MANIFEST_PATH,
    )
    parser.add_argument("--snapshot-delta-json", type=Path)
    parser.add_argument("--snapshot-delta-markdown", type=Path)
    parser.add_argument("--summary-json", type=Path)
    parser.add_argument("--summary-markdown", type=Path)
    parser.add_argument("--comment-markdown", type=Path)
    parser.add_argument("--pygraphistry-path", type=Path)
    parser.add_argument(
        "--skip-report-generation",
        action="store_true",
        help="Use pre-existing base/head report artifacts instead of running report.",
    )
    parser.add_argument(
        "--base-label",
        default=_default_label("GITHUB_BASE_REF", "main"),
        help="Human-readable base ref label for the PR comment.",
    )
    parser.add_argument(
        "--head-label",
        default=_default_label("GITHUB_HEAD_REF", _default_label("GITHUB_SHA", "HEAD")),
        help="Human-readable head ref label for the PR comment.",
    )
    parser.add_argument(
        "--json-artifact-name",
        default="unified-conformance-summary",
        help="Workflow artifact name shown in the generated comment.",
    )
    args = parser.parse_args(argv)

    head_dir = args.head_dir.resolve()
    base_dir = args.base_dir.resolve()
    output_dir = _resolve(args.output_dir, root=head_dir).resolve()
    base_report_json = (
        _resolve(args.base_report_json, root=head_dir)
        if args.base_report_json is not None
        else output_dir / "base-cypher-tck-report.json"
    )
    head_report_json = (
        _resolve(args.head_report_json, root=head_dir)
        if args.head_report_json is not None
        else output_dir / "head-cypher-tck-report.json"
    )
    snapshot_delta_json = (
        _resolve(args.snapshot_delta_json, root=head_dir)
        if args.snapshot_delta_json is not None
        else output_dir / "direct-cypher-snapshot-delta.json"
    )
    snapshot_delta_markdown = (
        _resolve(args.snapshot_delta_markdown, root=head_dir)
        if args.snapshot_delta_markdown is not None
        else output_dir / "direct-cypher-snapshot-delta.md"
    )
    summary_json = (
        _resolve(args.summary_json, root=head_dir)
        if args.summary_json is not None
        else output_dir / "unified-conformance-summary.json"
    )
    summary_markdown = (
        _resolve(args.summary_markdown, root=head_dir)
        if args.summary_markdown is not None
        else output_dir / "unified-conformance-summary.md"
    )
    comment_markdown = (
        _resolve(args.comment_markdown, root=head_dir)
        if args.comment_markdown is not None
        else output_dir / DEFAULT_COMMENT_FILENAME
    )
    manifest_path = _resolve(args.manifest, root=head_dir)
    pygraphistry_path = (
        args.pygraphistry_path.resolve() if args.pygraphistry_path is not None else None
    )

    build_outputs(
        base_dir=base_dir,
        head_dir=head_dir,
        output_dir=output_dir,
        base_report_json=base_report_json,
        head_report_json=head_report_json,
        manifest_path=manifest_path,
        snapshot_delta_json=snapshot_delta_json,
        snapshot_delta_markdown=snapshot_delta_markdown,
        summary_json=summary_json,
        summary_markdown=summary_markdown,
        comment_markdown=comment_markdown,
        base_label=args.base_label,
        head_label=args.head_label,
        pygraphistry_path=pygraphistry_path,
        generate_reports=not args.skip_report_generation,
        json_artifact_name=args.json_artifact_name,
    )
    print(f"PR comment markdown written: {comment_markdown}")
    print(f"Unified JSON summary written: {summary_json}")
    print(f"Snapshot delta JSON written: {snapshot_delta_json}")


if __name__ == "__main__":
    main()
