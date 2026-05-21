import json

from tests.cypher_tck import pr_conformance_comment
from tests.cypher_tck.test_unified_conformance_summary import (
    _entry,
    _manifest,
    _report_artifact,
)


def test_main_writes_marker_comment_and_artifacts_for_no_change_run(tmp_path) -> None:
    base_dir = tmp_path / "base"
    head_dir = tmp_path / "head"
    output_dir = tmp_path / "out"
    base_dir.mkdir()
    head_dir.mkdir()
    base_report = tmp_path / "base-report.json"
    head_report = tmp_path / "head-report.json"
    manifest = tmp_path / "manifest.json"
    summary_json = output_dir / "summary.json"
    comment_markdown = output_dir / "comment.md"
    report_artifact = _report_artifact()
    base_report.write_text(json.dumps(report_artifact), encoding="utf-8")
    head_report.write_text(json.dumps(report_artifact), encoding="utf-8")
    manifest.write_text(
        json.dumps(
            _manifest(
                _entry(
                    "supported-case",
                    support_status="supported",
                    implementation_status="translated",
                    ownership="supported",
                )
            )
        ),
        encoding="utf-8",
    )

    pr_conformance_comment.main(
        [
            "--base-dir",
            str(base_dir),
            "--head-dir",
            str(head_dir),
            "--output-dir",
            str(output_dir),
            "--base-report-json",
            str(base_report),
            "--head-report-json",
            str(head_report),
            "--manifest",
            str(manifest),
            "--summary-json",
            str(summary_json),
            "--comment-markdown",
            str(comment_markdown),
            "--base-label",
            "main",
            "--head-label",
            "issue-170",
            "--skip-report-generation",
        ]
    )

    parsed = json.loads(summary_json.read_text(encoding="utf-8"))
    comment = comment_markdown.read_text(encoding="utf-8")

    assert parsed["schema_version"] == 1
    assert pr_conformance_comment.COMMENT_MARKER in comment
    assert "Direct-Cypher delta: no added, removed, or changed cases." in comment
    assert "# Unified Conformance Summary" in comment
    assert "`main`" in comment
    assert "`issue-170`" in comment
