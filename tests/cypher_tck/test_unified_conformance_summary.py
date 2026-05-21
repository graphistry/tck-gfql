import json

from tests.cypher_tck import unified_conformance_summary as unified_summary


def _report_artifact(*, debt_keys=()) -> dict[str, object]:
    debt_key_list = list(debt_keys)
    return {
        "schema_version": 1,
        "generated_at": "2026-05-20T00:00:00Z",
        "source_refs": {
            "open_cypher_tck": {
                "commit": "59edf2e1c17b845bf97c334ed06b2eb780950c13",
                "path": "tck",
                "repo": "https://github.com/opencypher/openCypher",
            }
        },
        "scenario_counts": {
            "total": 4,
            "supported": 3,
            "xfail": 1,
            "skip": 0,
            "other": 0,
            "gfql_defined": 3,
            "gfql_missing": 1,
        },
        "gfql_counts": {
            "translated_non_none": 3,
            "translated_supported": 2,
            "translated_xfail": 1,
            "translated_skip": 0,
            "supported_missing_gfql": 1,
            "supported_pure": 2,
            "supported_impure": 1,
        },
        "direct_cypher_counts": {
            "overlap_translated_supported": 2,
            "translated_supported_total": 2,
            "promoted_only": 1,
            "promoted_only_rows": 1,
            "promoted_only_expected_errors": 0,
            "total_snapshot": 3,
            "represented_total": 4,
        },
        "expected_error_counts": {
            "cypher_string_supported": 0,
            "direct_cypher_promoted_only": 0,
            "direct_cypher_nonvalidation_debt": len(debt_key_list),
            "direct_cypher_nonvalidation_by_outcome": {},
        },
        "debt_keys": debt_key_list,
    }


def _entry(
    key: str,
    *,
    support_status: str,
    implementation_status: str,
    ownership: str,
    reason: str | None = None,
    direct_cypher_debt: dict[str, str] | None = None,
) -> dict[str, object]:
    entry: dict[str, object] = {
        "key": key,
        "support_status": support_status,
        "implementation_status": implementation_status,
        "ownership": ownership,
        "tags": [],
    }
    if reason is not None:
        entry["reason"] = reason
    if direct_cypher_debt is not None:
        entry["direct_cypher_debt"] = direct_cypher_debt
    return entry


def _manifest(*entries: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": 2,
        "compatible_report_schema_version": 1,
        "category_definitions": {
            "supported": "Expected pass scenario.",
            "xfail": "Known conformance debt.",
            "skip": "Temporarily excluded scenario status.",
            "not_yet_implemented": "Scenario without current implementation.",
        },
        "scenario_entries": list(entries),
    }


def _delta(
    *,
    changed_cases=(),
    removed_cases=(),
    remaining_debt=(),
    added_passing_cases=(),
    added_expected_error_cases=(),
) -> dict[str, object]:
    changed_case_list = list(changed_cases)
    removed_case_list = list(removed_cases)
    remaining_debt_list = list(remaining_debt)
    added_passing_case_list = list(added_passing_cases)
    added_expected_error_case_list = list(added_expected_error_cases)
    return {
        "schema_version": 1,
        "input_schema_version": 1,
        "old": {"schema_version": 1},
        "new": {"schema_version": 1},
        "summary_counts": {
            "added_passing_cases": len(added_passing_case_list),
            "added_expected_error_cases": len(added_expected_error_case_list),
            "removed_cases": len(removed_case_list),
            "changed_cases": len(changed_case_list),
            "remaining_debt": len(remaining_debt_list),
        },
        "direct_cypher_counts_delta": {"total_snapshot": 0},
        "expected_error_counts_delta": {"direct_cypher_nonvalidation_debt": 0},
        "added_passing_cases": added_passing_case_list,
        "added_expected_error_cases": added_expected_error_case_list,
        "removed_cases": removed_case_list,
        "changed_cases": changed_case_list,
        "remaining_debt": remaining_debt_list,
        "input_warnings": [],
    }


def test_build_summary_clean_run_has_no_debt_movement() -> None:
    debt = {
        "key": "existing-debt",
        "category": "debt",
        "outcome": "success_wrong_rows",
        "reason": "direct_cypher_nonvalidation:success_wrong_rows",
    }
    summary = unified_summary.build_summary(
        _report_artifact(debt_keys=[debt]),
        _manifest(
            _entry(
                "supported-case",
                support_status="supported",
                implementation_status="translated",
                ownership="supported",
            ),
            _entry(
                "existing-debt",
                support_status="xfail",
                implementation_status="translated",
                ownership="expression-long-tail",
                reason="Known row mismatch",
                direct_cypher_debt={
                    "outcome": "success_wrong_rows",
                    "reason": "direct_cypher_nonvalidation:success_wrong_rows",
                },
            ),
        ),
        _delta(remaining_debt=[debt]),
    )

    assert summary["schema_version"] == 1
    assert summary["headline"]["scenario_counts"]["total"] == 4
    assert summary["manifest"]["direct_cypher_debt_count"] == 1
    assert summary["direct_cypher_delta"]["remaining_debt"][0]["key"] == (
        "existing-debt"
    )
    assert summary["debt_movement"]["counts"] == {
        "newly_broken": 0,
        "recovered": 0,
        "removed_debt": 0,
        "remaining_debt": 1,
    }

    markdown = unified_summary.render_markdown(summary)
    assert "# Unified Conformance Summary" in markdown
    assert "| Newly broken support classifications | 0 |" in markdown
    assert "| Remaining direct-Cypher debt | 1 |" in markdown


def test_build_summary_reports_bumped_debt_as_newly_broken_xfail() -> None:
    changed_to_debt = {
        "key": "new-xfail",
        "old_category": "passing",
        "new_category": "debt",
        "changes": [{"field": "category", "old": "passing", "new": "debt"}],
    }
    summary = unified_summary.build_summary(
        _report_artifact(),
        _manifest(
            _entry(
                "new-xfail",
                support_status="xfail",
                implementation_status="translated",
                ownership="row-pipeline-read-forms",
                reason="Newly detected row-pipeline mismatch",
            )
        ),
        _delta(changed_cases=[changed_to_debt], remaining_debt=[changed_to_debt]),
    )

    movement = summary["debt_movement"]
    assert movement["counts"]["newly_broken"] == 1
    broken = movement["newly_broken"][0]
    assert broken["key"] == "new-xfail"
    assert broken["manifest"]["support_status"] == "xfail"
    assert broken["manifest"]["reason"] == "Newly detected row-pipeline mismatch"

    markdown = unified_summary.render_markdown(summary)
    assert "| Newly broken support classifications | 1 |" in markdown
    assert "## Direct-Cypher Changed Cases" in markdown
    assert "| new-xfail | passing -> debt | category |" in markdown
    assert "| new-xfail | passing -> debt | xfail | translated |" in markdown


def test_build_summary_reports_recovered_debt_transition() -> None:
    recovered = {
        "key": "recovered-xfail",
        "old_category": "debt",
        "new_category": "passing",
        "changes": [{"field": "category", "old": "debt", "new": "passing"}],
    }
    summary = unified_summary.build_summary(
        _report_artifact(),
        _manifest(
            _entry(
                "recovered-xfail",
                support_status="supported",
                implementation_status="direct_cypher_only",
                ownership="direct-cypher-promotion",
            )
        ),
        _delta(
            changed_cases=[recovered],
            added_passing_cases=[{"key": "recovered-xfail", "category": "passing"}],
        ),
    )

    movement = summary["debt_movement"]
    assert movement["counts"]["recovered"] == 1
    assert movement["recovered"][0]["manifest"]["support_status"] == "supported"
    assert summary["direct_cypher_delta"]["added_passing_cases"][0]["key"] == (
        "recovered-xfail"
    )

    markdown = unified_summary.render_markdown(summary)
    assert "| recovered-xfail | category=passing |" in markdown
    assert "| Recovered debt transitions | 1 |" in markdown
    assert (
        "| recovered-xfail | debt -> passing | supported | direct_cypher_only |"
        in markdown
    )


def test_main_writes_json_and_markdown_outputs(tmp_path, capsys) -> None:
    report_path = tmp_path / "report.json"
    manifest_path = tmp_path / "manifest.json"
    delta_path = tmp_path / "delta.json"
    json_output = tmp_path / "summary.json"
    markdown_output = tmp_path / "summary.md"
    report_path.write_text(json.dumps(_report_artifact()), encoding="utf-8")
    manifest_path.write_text(
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
    delta_path.write_text(json.dumps(_delta()), encoding="utf-8")

    unified_summary.main(
        [
            "--report-json",
            str(report_path),
            "--manifest",
            str(manifest_path),
            "--snapshot-delta",
            str(delta_path),
            "--json-output",
            str(json_output),
            "--markdown-output",
            str(markdown_output),
        ]
    )

    parsed = json.loads(json_output.read_text(encoding="utf-8"))
    markdown = markdown_output.read_text(encoding="utf-8")
    stdout = capsys.readouterr().out

    assert parsed["schema_version"] == 1
    assert "Unified Conformance Summary" in markdown
    assert f"Unified JSON summary written: {json_output}" in stdout
