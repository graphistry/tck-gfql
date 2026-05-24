import json
from pathlib import Path

from tests.cypher_tck import coverage_gap_pr_delta


def _file_payload(
    path: str,
    *,
    coverage_percent: float,
    missing_ranges: list[dict[str, int]],
    executable_count: int = 100,
) -> dict[str, object]:
    zero_hit_count = sum(
        int(item["end"]) - int(item["start"]) + 1 for item in missing_ranges
    )
    return {
        "coverage_percent": coverage_percent,
        "executable_line_count": executable_count,
        "hit_line_count": executable_count - zero_hit_count,
        "path": path,
        "zero_hit_line_count": zero_hit_count,
        "zero_hit_ranges": missing_ranges,
    }


def _report(*files: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_refs": {
            "pygraphistry": {
                "branch": "test-branch",
                "commit": "abc123",
            }
        },
        "files": list(files),
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_main_writes_delta_comment_for_touched_priority_file(tmp_path) -> None:
    changed_files = tmp_path / "changed-files.txt"
    base_report = tmp_path / "base-coverage.json"
    head_report = tmp_path / "head-coverage.json"
    output_json = tmp_path / "delta.json"
    output_markdown = tmp_path / "delta.md"
    comment_markdown = tmp_path / "comment.md"
    github_output = tmp_path / "github-output.txt"
    target = "graphistry/compute/gfql/cypher/lowering.py"
    changed_files.write_text(f"{target}\n", encoding="utf-8")
    _write_json(
        base_report,
        _report(
            _file_payload(
                target,
                coverage_percent=75.0,
                missing_ranges=[
                    {"start": 10, "end": 11},
                    {"start": 20, "end": 20},
                ],
            )
        ),
    )
    _write_json(
        head_report,
        _report(
            _file_payload(
                target,
                coverage_percent=76.0,
                missing_ranges=[
                    {"start": 11, "end": 11},
                    {"start": 30, "end": 30},
                ],
            )
        ),
    )

    coverage_gap_pr_delta.main(
        [
            "--base-report-json",
            str(base_report),
            "--head-report-json",
            str(head_report),
            "--changed-files",
            str(changed_files),
            "--json-output",
            str(output_json),
            "--markdown-output",
            str(output_markdown),
            "--comment-markdown",
            str(comment_markdown),
            "--github-output",
            str(github_output),
            "--base-label",
            "master merge-base",
            "--head-label",
            "shrink/pr",
        ]
    )

    parsed = json.loads(output_json.read_text(encoding="utf-8"))
    comment = comment_markdown.read_text(encoding="utf-8")

    assert parsed["schema_version"] == 1
    assert parsed["status"] == "ready"
    assert parsed["summary_counts"]["newly_uncovered_line_count"] == 1
    assert parsed["summary_counts"]["newly_covered_line_count"] == 2
    assert parsed["files"][0]["comparison_status"] == "compared"
    assert parsed["files"][0]["newly_uncovered_ranges"] == [{"start": 30, "end": 30}]
    assert parsed["files"][0]["newly_covered_ranges"] == [
        {"start": 10, "end": 10},
        {"start": 20, "end": 20},
    ]
    assert parsed["files"][0]["net_coverage_percent_delta"] == 1.0
    assert coverage_gap_pr_delta.COMMENT_MARKER in comment
    assert coverage_gap_pr_delta.BASELINE_URL in comment
    assert "`graphistry/compute/gfql/cypher/lowering.py`" in comment
    assert "30" in comment
    assert "10, 20" in comment
    assert "should_comment=true" in github_output.read_text(encoding="utf-8")


def test_main_suppresses_comment_when_no_priority_file_touched(tmp_path) -> None:
    changed_files = tmp_path / "changed-files.txt"
    output_json = tmp_path / "delta.json"
    output_markdown = tmp_path / "delta.md"
    comment_markdown = tmp_path / "comment.md"
    github_output = tmp_path / "github-output.txt"
    changed_files.write_text(
        "graphistry/compute/gfql/non_priority.py\nREADME.md\n",
        encoding="utf-8",
    )

    coverage_gap_pr_delta.main(
        [
            "--changed-files",
            str(changed_files),
            "--json-output",
            str(output_json),
            "--markdown-output",
            str(output_markdown),
            "--comment-markdown",
            str(comment_markdown),
            "--github-output",
            str(github_output),
            "--allow-suppressed-without-reports",
        ]
    )

    parsed = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_markdown.read_text(encoding="utf-8")

    assert parsed["status"] == "suppressed"
    assert parsed["touched_priority_files"] == []
    assert "no requested priority files were touched" in markdown
    assert "should_comment=false" in github_output.read_text(encoding="utf-8")
