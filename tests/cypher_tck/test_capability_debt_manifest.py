from __future__ import annotations

from copy import deepcopy

import pytest

from tests.cypher_tck import capability_debt_manifest as manifest_module
from tests.cypher_tck import report as report_module
from tests.cypher_tck.capability_debt_manifest import ManifestValidationError
from tests.cypher_tck.direct_cypher_xfail_contract import (
    DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY,
)
from tests.cypher_tck.models import Expected, GraphFixture, Scenario
from tests.cypher_tck.scenarios import SCENARIOS


def _artifact() -> dict[str, object]:
    return report_module.build_json_artifact(generated_at="2026-05-20T00:00:00Z")


def _manifest() -> dict[str, object]:
    return manifest_module.load_manifest()


def _entry_by_key(manifest: dict[str, object], key: str) -> dict[str, object]:
    entries = manifest["scenario_entries"]
    assert isinstance(entries, list)
    return next(entry for entry in entries if entry["key"] == key)


def _first_xfail_key() -> str:
    return next(scenario.key for scenario in SCENARIOS if scenario.status == "xfail")


def _single_expected_error_scenario() -> Scenario:
    return Scenario(
        key="unit-error-1",
        feature_path="synthetic/unit.feature",
        scenario="synthetic expected-error scenario",
        cypher="RETURN range(1, 'bad')",
        graph=GraphFixture(nodes=(), edges=()),
        expected=Expected(rows=None),
        gfql=None,
        status="supported",
        tags=("cypher-string", "cypher-string-error"),
    )


def _single_scenario_manifest(
    *,
    expected_error: dict[str, object] | None = None,
) -> dict[str, object]:
    entry: dict[str, object] = {
        "key": "unit-error-1",
        "support_status": "supported",
        "implementation_status": "direct_cypher_only",
        "ownership": "direct-cypher-promotion",
        "tags": ["cypher-string", "cypher-string-error"],
    }
    if expected_error is not None:
        entry["expected_error"] = expected_error
    return {
        "schema_version": manifest_module.MANIFEST_SCHEMA_VERSION,
        "compatible_report_schema_version": report_module.SCHEMA_VERSION,
        "category_definitions": dict(manifest_module.CATEGORY_DEFINITIONS),
        "scenario_entries": [entry],
    }


def _single_scenario_artifact(
    *,
    direct_cypher_cases: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    scenarios = [_single_expected_error_scenario()]
    artifact: dict[str, object] = {
        "schema_version": report_module.SCHEMA_VERSION,
        "source_refs": {
            "local_fixtures": {
                "scenario_inventory_sha256": report_module._scenario_inventory_revision(
                    scenarios
                ),
            },
        },
        "scenario_counts": {
            "total": 1,
            "supported": 1,
            "xfail": 0,
            "skip": 0,
            "other": 0,
        },
        "expected_error_counts": {"direct_cypher_nonvalidation_debt": 0},
        "debt_keys": [],
    }
    if direct_cypher_cases is not None:
        artifact["direct_cypher_cases"] = direct_cypher_cases
    return artifact


def _expected_error_block() -> dict[str, object]:
    return {
        "code": "GFQL_RANGE_ARGUMENT",
        "key_fields": {
            "category": "validation",
            "field": "range",
            "value": "bad",
        },
        "anchored_substrings": ["range", "bad"],
    }


def _actual_expected_error_case() -> dict[str, object]:
    return {
        "key": "unit-error-1",
        "category": "expected_error",
        "expected_error": {
            "code": "GFQL_RANGE_ARGUMENT",
            "category": "validation",
            "field": "range",
            "value": "bad",
            "message": "range argument rejected: bad",
        },
    }


def test_default_capability_debt_manifest_validates_against_report_artifact() -> None:
    summary = manifest_module.validate_manifest(_manifest(), artifact=_artifact())

    assert summary.scenario_count == len(SCENARIOS)
    assert summary.status_counts == {"skip": 5, "supported": 2954, "xfail": 699}
    assert summary.implementation_counts == {
        "direct_cypher_only": 266,
        "not_yet_implemented": 454,
        "translated": 2938,
    }
    assert summary.direct_cypher_debt_count == len(
        DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY
    )


def test_manifest_sample_entries_cover_current_categories() -> None:
    manifest = _manifest()
    category_definitions = manifest["category_definitions"]
    assert isinstance(category_definitions, dict)
    assert set(category_definitions) == {
        "not_yet_implemented",
        "skip",
        "supported",
        "xfail",
    }

    supported = _entry_by_key(manifest, "match-where1-3")
    assert supported["support_status"] == "supported"
    assert supported["implementation_status"] == "translated"
    assert supported["ownership"] == "supported"

    xfail = _entry_by_key(manifest, "call1-1")
    assert xfail["support_status"] == "xfail"
    assert xfail["implementation_status"] == "not_yet_implemented"
    assert xfail["reason"] == "CALL procedures are not supported"
    assert xfail["ownership"] == "procedures-and-call"

    direct_cypher_only = _entry_by_key(manifest, "call1-7")
    assert direct_cypher_only["support_status"] == "supported"
    assert direct_cypher_only["implementation_status"] == "direct_cypher_only"
    assert direct_cypher_only["ownership"] == "direct-cypher-promotion"

    experimental_surface = _entry_by_key(manifest, "firstparty-typed-schema1-1")
    assert experimental_surface["support_status"] == "supported"
    assert experimental_surface["implementation_status"] == "direct_cypher_only"
    assert experimental_surface["ownership"] == "direct-cypher-promotion"
    assert "experimental-surface" in experimental_surface["tags"]
    assert "typed-schema" in experimental_surface["tags"]

    skip = _entry_by_key(manifest, "firstparty-predicates-isnotin1-1")
    assert skip["support_status"] == "skip"
    assert skip["implementation_status"] == "not_yet_implemented"
    assert skip["ownership"] == "skipped"
    assert skip["reason"] == (
        "pygraphistry#966 is still open; is_not_in() is not available on "
        "current pygraphistry master"
    )


def test_manifest_rejects_stale_scenario_key() -> None:
    manifest = deepcopy(_manifest())
    entries = manifest["scenario_entries"]
    assert isinstance(entries, list)
    entries[0]["key"] = "stale-scenario-key"

    with pytest.raises(ManifestValidationError, match="unknown scenario keys"):
        manifest_module.validate_manifest(manifest, artifact=_artifact())


def test_manifest_rejects_missing_debt_reason() -> None:
    manifest = deepcopy(_manifest())
    _entry_by_key(manifest, _first_xfail_key())["reason"] = ""

    with pytest.raises(ManifestValidationError, match="missing reason"):
        manifest_module.validate_manifest(manifest, artifact=_artifact())


def test_manifest_rejects_undocumented_current_scenario() -> None:
    manifest = deepcopy(_manifest())
    entries = manifest["scenario_entries"]
    assert isinstance(entries, list)
    xfail_key = _first_xfail_key()
    manifest["scenario_entries"] = [
        entry for entry in entries if entry["key"] != xfail_key
    ]

    with pytest.raises(ManifestValidationError, match="missing manifest entries"):
        manifest_module.validate_manifest(manifest, artifact=_artifact())


def test_manifest_rejects_direct_cypher_debt_mismatch() -> None:
    manifest = deepcopy(_manifest())
    debt_key = next(iter(DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY))
    _entry_by_key(manifest, debt_key).pop("direct_cypher_debt")

    with pytest.raises(ManifestValidationError, match="direct_cypher_debt"):
        manifest_module.validate_manifest(manifest, artifact=_artifact())


def test_manifest_rejects_report_schema_mismatch() -> None:
    manifest = deepcopy(_manifest())
    manifest["compatible_report_schema_version"] = 999

    with pytest.raises(
        ManifestValidationError, match="compatible_report_schema_version"
    ):
        manifest_module.validate_manifest(manifest, artifact=_artifact())


def test_manifest_rejects_stale_report_artifact_inventory_hash() -> None:
    artifact = _artifact()
    artifact["source_refs"]["local_fixtures"]["scenario_inventory_sha256"] = "stale"  # type: ignore[index]

    with pytest.raises(ManifestValidationError, match="inventory hash is stale"):
        manifest_module.validate_manifest(_manifest(), artifact=artifact)


def test_manifest_expected_error_block_matches_actual_case_output() -> None:
    scenarios = [_single_expected_error_scenario()]
    summary = manifest_module.validate_manifest(
        _single_scenario_manifest(expected_error=_expected_error_block()),
        artifact=_single_scenario_artifact(
            direct_cypher_cases=[_actual_expected_error_case()]
        ),
        scenarios=scenarios,
    )

    assert summary.scenario_count == 1
    assert summary.direct_cypher_debt_count == 0


def test_manifest_expected_error_claim_mismatch_reports_anchored_diagnostic() -> None:
    scenarios = [_single_expected_error_scenario()]

    with pytest.raises(ManifestValidationError) as exc:
        manifest_module.validate_manifest(
            _single_scenario_manifest(expected_error=_expected_error_block()),
            artifact=_single_scenario_artifact(
                direct_cypher_cases=[
                    {"key": "unit-error-1", "category": "passing", "row_count": 1}
                ]
            ),
            scenarios=scenarios,
        )

    message = str(exc.value)
    assert "unit-error-1: expected_error claim mismatch" in message
    assert "expected error mismatch for scenario unit-error-1" in message
    assert "context: field='code'" in message
    assert "actual: '<missing error code>'" in message


def test_manifest_expected_error_drift_reports_anchored_diagnostic() -> None:
    scenarios = [_single_expected_error_scenario()]
    stale_block = _expected_error_block()
    stale_block["code"] = "STALE_CODE"

    with pytest.raises(ManifestValidationError) as exc:
        manifest_module.validate_manifest(
            _single_scenario_manifest(expected_error=stale_block),
            artifact=_single_scenario_artifact(
                direct_cypher_cases=[_actual_expected_error_case()]
            ),
            scenarios=scenarios,
        )

    message = str(exc.value)
    assert "unit-error-1: expected_error drift" in message
    assert "expected error mismatch for scenario unit-error-1" in message
    assert "context: field='code'" in message
    assert "expected: 'STALE_CODE'" in message
    assert "actual: 'GFQL_RANGE_ARGUMENT'" in message


def test_manifest_expected_error_drift_reports_anchored_substring() -> None:
    scenarios = [_single_expected_error_scenario()]
    stale_block = _expected_error_block()
    stale_block["anchored_substrings"] = ["missing-token"]

    with pytest.raises(ManifestValidationError) as exc:
        manifest_module.validate_manifest(
            _single_scenario_manifest(expected_error=stale_block),
            artifact=_single_scenario_artifact(
                direct_cypher_cases=[_actual_expected_error_case()]
            ),
            scenarios=scenarios,
        )

    message = str(exc.value)
    assert "unit-error-1: expected_error drift" in message
    assert "context: field='anchored_substrings[0]'" in message
    assert "expected: 'missing-token'" in message
    assert "anchored substring was not present" in message


def test_manifest_expected_error_absent_block_detects_structured_actual_drift() -> None:
    scenarios = [_single_expected_error_scenario()]

    with pytest.raises(ManifestValidationError) as exc:
        manifest_module.validate_manifest(
            _single_scenario_manifest(),
            artifact=_single_scenario_artifact(
                direct_cypher_cases=[_actual_expected_error_case()]
            ),
            scenarios=scenarios,
        )

    message = str(exc.value)
    assert "unit-error-1: expected_error drift" in message
    assert "manifest expected_error block is absent" in message


def test_manifest_expected_error_absent_block_remains_backward_compatible() -> None:
    scenarios = [_single_expected_error_scenario()]
    summary = manifest_module.validate_manifest(
        _single_scenario_manifest(),
        artifact=_single_scenario_artifact(),
        scenarios=scenarios,
    )

    assert summary.scenario_count == 1
