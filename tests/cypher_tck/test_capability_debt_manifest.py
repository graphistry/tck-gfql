from __future__ import annotations

from copy import deepcopy

import pytest

from tests.cypher_tck import capability_debt_manifest as manifest_module
from tests.cypher_tck import report as report_module
from tests.cypher_tck.capability_debt_manifest import ManifestValidationError
from tests.cypher_tck.direct_cypher_xfail_contract import (
    DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY,
)
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


def test_default_capability_debt_manifest_validates_against_report_artifact() -> None:
    summary = manifest_module.validate_manifest(_manifest(), artifact=_artifact())

    assert summary.scenario_count == len(SCENARIOS)
    assert summary.status_counts == {"supported": 2926, "xfail": 701}
    assert summary.implementation_counts == {
        "direct_cypher_only": 238,
        "not_yet_implemented": 451,
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

    entries = manifest["scenario_entries"]
    assert isinstance(entries, list)
    assert not any(entry["support_status"] == "skip" for entry in entries)


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
