import json
from pathlib import Path

from tests.cypher_tck import coverage_gap_cumulative_tracker


TARGET = "graphistry/compute/gfql/cypher/lowering.py"


def _ranges(*items: tuple[int, int]) -> list[dict[str, int]]:
    return [{"start": start, "end": end} for start, end in items]


def _file_payload(path: str, ranges: list[dict[str, int]]) -> dict[str, object]:
    zero_hit_count = sum(item["end"] - item["start"] + 1 for item in ranges)
    return {
        "coverage_percent": round(((100 - zero_hit_count) / 100) * 100, 2),
        "executable_line_count": 100,
        "hit_line_count": 100 - zero_hit_count,
        "path": path,
        "zero_hit_line_count": zero_hit_count,
        "zero_hit_ranges": ranges,
    }


def _report(label: str, ranges: list[dict[str, int]]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_refs": {
            "pygraphistry": {
                "branch": "master",
                "commit": label,
            }
        },
        "files": [_file_payload(TARGET, ranges)],
    }


def _point(label: str, ranges: list[dict[str, int]]):
    return coverage_gap_cumulative_tracker.ReportPoint(
        label=label,
        report=_report(label, ranges),
    )


def test_build_cumulative_report_classifies_gap_closed() -> None:
    report = coverage_gap_cumulative_tracker.build_cumulative_report(
        [
            _point("baseline", _ranges((10, 12), (20, 20))),
            _point("head", _ranges((11, 12))),
        ],
        generated_at="2026-05-23T00:00:00Z",
    )

    target = report["files"][0]

    assert report["schema_version"] == 1
    assert report["trajectory"] == "gap_closed"
    assert report["summary_counts"]["cumulative_closed_zero_hit_line_count"] == 2
    assert report["summary_counts"]["cumulative_opened_zero_hit_line_count"] == 0
    assert report["summary_counts"]["net_zero_hit_line_delta"] == -2
    assert target["trajectory"] == "gap_closed"
    assert target["cumulative_closed_zero_hit_ranges"] == [
        {"start": 10, "end": 10},
        {"start": 20, "end": 20},
    ]
    assert report["top_closures"][0]["path"] == TARGET


def test_build_cumulative_report_classifies_gap_opened() -> None:
    report = coverage_gap_cumulative_tracker.build_cumulative_report(
        [
            _point("baseline", _ranges((10, 10))),
            _point("head", _ranges((10, 10), (30, 31))),
        ],
        generated_at="2026-05-23T00:00:00Z",
    )

    target = report["files"][0]

    assert report["trajectory"] == "gap_opened"
    assert report["summary_counts"]["cumulative_opened_zero_hit_line_count"] == 2
    assert report["summary_counts"]["net_zero_hit_line_delta"] == 2
    assert target["cumulative_opened_zero_hit_ranges"] == [
        {"start": 30, "end": 31}
    ]
    assert report["top_opens"][0]["path"] == TARGET


def test_build_cumulative_report_classifies_shuffled_gap_and_tracks_gross_movement() -> None:
    report = coverage_gap_cumulative_tracker.build_cumulative_report(
        [
            _point("baseline", _ranges((10, 10))),
            _point("mid", _ranges((10, 10), (30, 30))),
            _point("head", _ranges((30, 30))),
        ],
        generated_at="2026-05-23T00:00:00Z",
    )

    target = report["files"][0]

    assert report["trajectory"] == "gap_shuffled"
    assert report["summary_counts"]["cumulative_closed_zero_hit_line_count"] == 1
    assert report["summary_counts"]["cumulative_opened_zero_hit_line_count"] == 1
    assert report["summary_counts"]["gross_closed_zero_hit_line_count"] == 1
    assert report["summary_counts"]["gross_opened_zero_hit_line_count"] == 1
    assert target["trajectory"] == "gap_shuffled"
    assert len(report["transitions"]) == 2


def test_build_cumulative_report_classifies_flat_cycle() -> None:
    report = coverage_gap_cumulative_tracker.build_cumulative_report(
        [
            _point("baseline", _ranges((10, 10))),
            _point("head", _ranges((10, 10))),
        ],
        generated_at="2026-05-23T00:00:00Z",
    )

    markdown = coverage_gap_cumulative_tracker.render_markdown(report)

    assert report["trajectory"] == "flat"
    assert report["summary_counts"]["net_zero_hit_line_delta"] == 0
    assert "Cycle is flat" in markdown
    assert "Coverage Gap Cumulative Tracker" in markdown


def test_main_writes_json_and_markdown_from_precomputed_reports(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    head_path = tmp_path / "head.json"
    json_output = tmp_path / "cumulative.json"
    markdown_output = tmp_path / "cumulative.md"
    baseline_path.write_text(json.dumps(_report("base-sha", _ranges((10, 10)))))
    head_path.write_text(json.dumps(_report("head-sha", _ranges((20, 20)))))

    coverage_gap_cumulative_tracker.main(
        [
            "--report",
            f"baseline={baseline_path}",
            "--report",
            f"head={head_path}",
            "--json-output",
            str(json_output),
            "--markdown-output",
            str(markdown_output),
            "--generated-at",
            "2026-05-23T00:00:00Z",
        ]
    )

    parsed = json.loads(json_output.read_text(encoding="utf-8"))
    markdown = markdown_output.read_text(encoding="utf-8")

    assert parsed["cycle"]["baseline_label"] == "baseline"
    assert parsed["cycle"]["final_label"] == "head"
    assert parsed["trajectory"] == "gap_shuffled"
    assert "Top 5 Closures" in markdown
    assert "Top 5 Opens" in markdown


def test_read_github_commit_refs_returns_chronological_shas(tmp_path: Path) -> None:
    path = tmp_path / "commits.json"
    path.write_text(
        json.dumps(
            [
                {"sha": "newest"},
                {"sha": "middle"},
                {"sha": "oldest"},
            ]
        ),
        encoding="utf-8",
    )

    assert coverage_gap_cumulative_tracker.read_github_commit_refs(path) == [
        "oldest",
        "middle",
        "newest",
    ]
    assert coverage_gap_cumulative_tracker.read_github_commit_refs(path, limit=2) == [
        "middle",
        "newest",
    ]
    assert coverage_gap_cumulative_tracker.read_github_commit_refs(
        path, baseline_commit="old"
    ) == ["middle", "newest"]
