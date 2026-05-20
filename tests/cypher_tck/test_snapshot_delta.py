import json

from tests.cypher_tck import snapshot_delta


def _artifact(*, cases, debt_keys=()):
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
        "direct_cypher_counts": {
            "promoted_only_rows": sum(
                1 for case in cases if case["category"] == "passing"
            ),
            "promoted_only_expected_errors": sum(
                1 for case in cases if case["category"] == "expected_error"
            ),
            "total_snapshot": len(cases),
        },
        "expected_error_counts": {
            "direct_cypher_promoted_only": sum(
                1 for case in cases if case["category"] == "expected_error"
            ),
            "direct_cypher_nonvalidation_debt": len(debt_key_list),
        },
        "debt_keys": debt_key_list,
        "direct_cypher_cases": list(cases),
    }


def test_build_delta_categorizes_required_case_groups() -> None:
    old = _artifact(
        cases=[
            {
                "key": "cardinality-drift",
                "category": "passing",
                "cardinality": 1,
                "ordered": False,
                "types": {"x": "int"},
            },
            {
                "key": "order-drift",
                "category": "passing",
                "cardinality": 1,
                "ordered": False,
                "types": {"x": "int"},
            },
            {
                "key": "type-drift",
                "category": "passing",
                "cardinality": 1,
                "ordered": False,
                "types": {"x": "int"},
            },
            {"key": "removed-row", "category": "passing", "cardinality": 1},
            {
                "key": "remaining-debt",
                "category": "debt",
                "outcome": "success_wrong_rows",
                "reason": "direct_cypher_nonvalidation:success_wrong_rows",
            },
        ],
        debt_keys=[
            {
                "key": "remaining-debt",
                "outcome": "success_wrong_rows",
                "reason": "direct_cypher_nonvalidation:success_wrong_rows",
            }
        ],
    )
    new = _artifact(
        cases=[
            {
                "key": "cardinality-drift",
                "category": "passing",
                "cardinality": 2,
                "ordered": False,
                "types": {"x": "int"},
            },
            {
                "key": "order-drift",
                "category": "passing",
                "cardinality": 1,
                "ordered": True,
                "types": {"x": "int"},
            },
            {
                "key": "type-drift",
                "category": "passing",
                "cardinality": 1,
                "ordered": False,
                "types": {"x": "str"},
            },
            {"key": "added-row", "category": "passing", "cardinality": 1},
            {
                "key": "added-error",
                "category": "expected_error",
                "error_code": "GFQL_DIRECT_EXPECTED",
            },
            {
                "key": "remaining-debt",
                "category": "debt",
                "outcome": "success_wrong_rows",
                "reason": "direct_cypher_nonvalidation:success_wrong_rows",
            },
        ],
        debt_keys=[
            {
                "key": "remaining-debt",
                "outcome": "success_wrong_rows",
                "reason": "direct_cypher_nonvalidation:success_wrong_rows",
            }
        ],
    )

    delta = snapshot_delta.build_delta(old, new)

    assert delta["summary_counts"] == {
        "added_passing_cases": 1,
        "added_expected_error_cases": 1,
        "removed_cases": 1,
        "changed_cases": 3,
        "remaining_debt": 1,
    }
    assert [case["key"] for case in delta["added_passing_cases"]] == ["added-row"]
    assert [case["key"] for case in delta["added_expected_error_cases"]] == [
        "added-error"
    ]
    assert [case["key"] for case in delta["removed_cases"]] == ["removed-row"]
    assert [case["key"] for case in delta["remaining_debt"]] == ["remaining-debt"]

    changes_by_key = {
        case["key"]: [change["field"] for change in case["changes"]]
        for case in delta["changed_cases"]
    }
    assert changes_by_key == {
        "cardinality-drift": ["cardinality"],
        "order-drift": ["order"],
        "type-drift": ["type"],
    }


def test_build_delta_uses_debt_keys_for_remaining_debt_without_case_inventory() -> None:
    old = {
        "schema_version": 1,
        "generated_at": "2026-05-20T00:00:00Z",
        "source_refs": {},
        "direct_cypher_counts": {"total_snapshot": 1},
        "expected_error_counts": {"direct_cypher_nonvalidation_debt": 1},
        "debt_keys": [
            {
                "key": "old-debt",
                "outcome": "success_wrong_rows",
                "reason": "direct_cypher_nonvalidation:success_wrong_rows",
            }
        ],
    }
    new = {
        "schema_version": 1,
        "generated_at": "2026-05-20T00:00:01Z",
        "source_refs": {},
        "direct_cypher_counts": {"total_snapshot": 2},
        "expected_error_counts": {"direct_cypher_nonvalidation_debt": 1},
        "debt_keys": [
            {
                "key": "new-debt",
                "outcome": "TypeError",
                "reason": "direct_cypher_nonvalidation:TypeError",
            }
        ],
    }

    delta = snapshot_delta.build_delta(old, new)

    assert "old artifact has no direct_cypher_cases inventory" in (
        delta["input_warnings"][0]
    )
    assert "new artifact has no direct_cypher_cases inventory" in (
        delta["input_warnings"][1]
    )
    assert [case["key"] for case in delta["removed_cases"]] == ["old-debt"]
    assert [case["key"] for case in delta["remaining_debt"]] == ["new-debt"]
    assert delta["direct_cypher_counts_delta"]["total_snapshot"] == 1


def test_debt_keys_override_inconsistent_optional_case_inventory() -> None:
    artifact = _artifact(
        cases=[{"key": "still-debt", "category": "passing", "cardinality": 1}],
        debt_keys=[
            {
                "key": "still-debt",
                "outcome": "success_wrong_rows",
                "reason": "direct_cypher_nonvalidation:success_wrong_rows",
            }
        ],
    )

    delta = snapshot_delta.build_delta(_artifact(cases=[]), artifact)

    assert [case["key"] for case in delta["remaining_debt"]] == ["still-debt"]
    assert "debt_keys entry 'still-debt' overrides" in delta["input_warnings"][0]


def test_render_markdown_is_pr_summary_ready() -> None:
    delta = snapshot_delta.build_delta(
        _artifact(cases=[]),
        _artifact(
            cases=[
                {"key": "added-row", "category": "passing", "cardinality": 1},
                {
                    "key": "added-error",
                    "category": "expected_error",
                    "error_code": "GFQL_DIRECT_EXPECTED",
                },
            ]
        ),
    )

    markdown = snapshot_delta.render_markdown(delta)

    assert "# Direct-Cypher Snapshot Delta" in markdown
    assert "| Added passing cases | 1 |" in markdown
    assert "| Added expected-error cases | 1 |" in markdown
    assert "| added-row | passing, cardinality=1 |" in markdown
    assert "| added-error | expected_error |" in markdown


def test_main_writes_json_and_markdown_outputs(tmp_path, capsys) -> None:
    old_path = tmp_path / "old.json"
    new_path = tmp_path / "new.json"
    json_output = tmp_path / "delta.json"
    markdown_output = tmp_path / "delta.md"
    old_path.write_text(json.dumps(_artifact(cases=[])), encoding="utf-8")
    new_path.write_text(
        json.dumps(_artifact(cases=[{"key": "added-row", "category": "passing"}])),
        encoding="utf-8",
    )

    snapshot_delta.main(
        [
            str(old_path),
            str(new_path),
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
    assert parsed["summary_counts"]["added_passing_cases"] == 1
    assert "Direct-Cypher Snapshot Delta" in markdown
    assert f"JSON delta written: {json_output}" in stdout
