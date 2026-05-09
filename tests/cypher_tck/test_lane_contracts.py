from __future__ import annotations

from tests.cypher_tck.gap_priority import (
    PRIMARY_FAMILY_DEFINITIONS,
    classify_primary_xfail_family,
)
from tests.cypher_tck.lane_contracts import (
    ROW_PIPELINE_TRANCHE1_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE1_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE1_KEYS,
)
from tests.cypher_tck.scenarios import SCENARIOS


def _scenario_map():
    return {scenario.key: scenario for scenario in SCENARIOS}


def test_row_pipeline_tranche1_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(ROW_PIPELINE_TRANCHE1_KEYS) - set(scenarios))
    assert missing == []


def test_row_pipeline_tranche1_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE1_KEYS:
        scenario = scenarios[key]
        assert scenario.status == ROW_PIPELINE_TRANCHE1_EXPECTED_STATUS
        for forbidden_tag in ROW_PIPELINE_TRANCHE1_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_row_pipeline_tranche1_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE1_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "row-pipeline-read-forms"


def test_row_pipeline_lane_has_issue_tracker_wired() -> None:
    row_pipeline = next(
        definition
        for definition in PRIMARY_FAMILY_DEFINITIONS
        if definition.lane_id == "row-pipeline-read-forms"
    )
    assert row_pipeline.tracker_ref == "#43"
    assert row_pipeline.tracker_url == "https://github.com/graphistry/tck-gfql/issues/43"
