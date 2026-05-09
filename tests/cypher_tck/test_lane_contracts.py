from __future__ import annotations

from tests.cypher_tck.gap_priority import (
    PRIMARY_FAMILY_DEFINITIONS,
    classify_primary_xfail_family,
)
from tests.cypher_tck.direct_cypher_xfail_contract import (
    DIRECT_CYPHER_PROMOTED_FROM_XFAIL_MATCHES_EXPECTED_KEYS,
)
from tests.cypher_tck.lane_contracts import (
    EXPRESSION_LONG_TAIL_TRANCHE1_EXPECTED_STATUS,
    EXPRESSION_LONG_TAIL_TRANCHE1_FORBIDDEN_TAGS,
    EXPRESSION_LONG_TAIL_TRANCHE1_KEYS,
    EXPRESSION_LONG_TAIL_TRANCHE2_EXPECTED_STATUS,
    EXPRESSION_LONG_TAIL_TRANCHE2_FORBIDDEN_TAGS,
    EXPRESSION_LONG_TAIL_TRANCHE2_KEYS,
    EXPRESSION_LONG_TAIL_TRANCHE3_EXPECTED_STATUS,
    EXPRESSION_LONG_TAIL_TRANCHE3_FORBIDDEN_TAGS,
    EXPRESSION_LONG_TAIL_TRANCHE3_KEYS,
    GROUPED_MATCH_AGG_TRANCHE1_EXPECTED_STATUS,
    GROUPED_MATCH_AGG_TRANCHE1_FORBIDDEN_TAGS,
    GROUPED_MATCH_AGG_TRANCHE1_KEYS,
    OPTIONAL_NULL_TRANCHE1_EXPECTED_STATUS,
    OPTIONAL_NULL_TRANCHE1_FORBIDDEN_TAGS,
    OPTIONAL_NULL_TRANCHE1_KEYS,
    OTHER_READ_GAPS_TRANCHE1_EXPECTED_STATUS,
    OTHER_READ_GAPS_TRANCHE1_FORBIDDEN_TAGS,
    OTHER_READ_GAPS_TRANCHE1_KEYS,
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


def test_grouped_match_aggregate_tranche1_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(GROUPED_MATCH_AGG_TRANCHE1_KEYS) - set(scenarios))
    assert missing == []


def test_grouped_match_aggregate_tranche1_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in GROUPED_MATCH_AGG_TRANCHE1_KEYS:
        scenario = scenarios[key]
        assert scenario.status == GROUPED_MATCH_AGG_TRANCHE1_EXPECTED_STATUS
        for forbidden_tag in GROUPED_MATCH_AGG_TRANCHE1_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_grouped_match_aggregate_tranche1_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in GROUPED_MATCH_AGG_TRANCHE1_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "grouped-match-aggregates"


def test_grouped_match_aggregate_lane_has_issue_tracker_wired() -> None:
    grouped_match_agg = next(
        definition
        for definition in PRIMARY_FAMILY_DEFINITIONS
        if definition.lane_id == "grouped-match-aggregates"
    )
    assert grouped_match_agg.tracker_ref == "#45"
    assert grouped_match_agg.tracker_url == "https://github.com/graphistry/tck-gfql/issues/45"


def test_optional_null_tranche1_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(OPTIONAL_NULL_TRANCHE1_KEYS) - set(scenarios))
    assert missing == []


def test_optional_null_tranche1_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in OPTIONAL_NULL_TRANCHE1_KEYS:
        scenario = scenarios[key]
        assert scenario.status == OPTIONAL_NULL_TRANCHE1_EXPECTED_STATUS
        for forbidden_tag in OPTIONAL_NULL_TRANCHE1_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_optional_null_tranche1_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in OPTIONAL_NULL_TRANCHE1_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "optional-match-null-extension"


def test_optional_null_lane_has_issue_tracker_wired() -> None:
    optional_null = next(
        definition
        for definition in PRIMARY_FAMILY_DEFINITIONS
        if definition.lane_id == "optional-match-null-extension"
    )
    assert optional_null.tracker_ref == "#44"
    assert optional_null.tracker_url == "https://github.com/graphistry/tck-gfql/issues/44"


def test_expression_long_tail_tranche1_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(EXPRESSION_LONG_TAIL_TRANCHE1_KEYS) - set(scenarios))
    assert missing == []


def test_expression_long_tail_tranche1_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    promoted = set(DIRECT_CYPHER_PROMOTED_FROM_XFAIL_MATCHES_EXPECTED_KEYS)
    for key in EXPRESSION_LONG_TAIL_TRANCHE1_KEYS:
        scenario = scenarios[key]
        if key in promoted:
            assert scenario.status == "supported"
            assert "cypher-string" in scenario.tags
        else:
            assert scenario.status == EXPRESSION_LONG_TAIL_TRANCHE1_EXPECTED_STATUS
            for forbidden_tag in EXPRESSION_LONG_TAIL_TRANCHE1_FORBIDDEN_TAGS:
                assert forbidden_tag not in scenario.tags


def test_expression_long_tail_tranche1_family_classification_contract() -> None:
    scenarios = _scenario_map()
    promoted = set(DIRECT_CYPHER_PROMOTED_FROM_XFAIL_MATCHES_EXPECTED_KEYS)
    for key in EXPRESSION_LONG_TAIL_TRANCHE1_KEYS:
        scenario = scenarios[key]
        if key in promoted:
            assert scenario.status == "supported"
            assert "cypher-string" in scenario.tags
        else:
            assert classify_primary_xfail_family(scenario) == "expression-long-tail"


def test_expression_long_tail_lane_has_issue_tracker_wired() -> None:
    expression_long_tail = next(
        definition
        for definition in PRIMARY_FAMILY_DEFINITIONS
        if definition.lane_id == "expression-long-tail"
    )
    assert expression_long_tail.tracker_ref == "#51"
    assert expression_long_tail.tracker_url == "https://github.com/graphistry/tck-gfql/issues/51"


def test_expression_long_tail_tranche2_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(EXPRESSION_LONG_TAIL_TRANCHE2_KEYS) - set(scenarios))
    assert missing == []


def test_expression_long_tail_tranche2_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE2_KEYS:
        scenario = scenarios[key]
        assert scenario.status == EXPRESSION_LONG_TAIL_TRANCHE2_EXPECTED_STATUS
        for forbidden_tag in EXPRESSION_LONG_TAIL_TRANCHE2_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_expression_long_tail_tranche2_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE2_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "expression-long-tail"


def test_expression_long_tail_tranche3_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(EXPRESSION_LONG_TAIL_TRANCHE3_KEYS) - set(scenarios))
    assert missing == []


def test_expression_long_tail_tranche3_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE3_KEYS:
        scenario = scenarios[key]
        assert scenario.status == EXPRESSION_LONG_TAIL_TRANCHE3_EXPECTED_STATUS
        for forbidden_tag in EXPRESSION_LONG_TAIL_TRANCHE3_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_expression_long_tail_tranche3_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE3_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "expression-long-tail"


def test_other_read_gaps_tranche1_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(OTHER_READ_GAPS_TRANCHE1_KEYS) - set(scenarios))
    assert missing == []


def test_other_read_gaps_tranche1_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in OTHER_READ_GAPS_TRANCHE1_KEYS:
        scenario = scenarios[key]
        assert scenario.status == OTHER_READ_GAPS_TRANCHE1_EXPECTED_STATUS
        for forbidden_tag in OTHER_READ_GAPS_TRANCHE1_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_other_read_gaps_tranche1_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in OTHER_READ_GAPS_TRANCHE1_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "other-read-gaps"


def test_other_read_gaps_lane_has_issue_tracker_wired() -> None:
    other_read_gaps = next(
        definition
        for definition in PRIMARY_FAMILY_DEFINITIONS
        if definition.lane_id == "other-read-gaps"
    )
    assert other_read_gaps.tracker_ref == "#52"
    assert other_read_gaps.tracker_url == "https://github.com/graphistry/tck-gfql/issues/52"


def test_all_primary_lanes_have_concrete_issue_tracker_refs() -> None:
    for definition in PRIMARY_FAMILY_DEFINITIONS:
        assert definition.tracker_ref.startswith("#"), definition.lane_id


def test_all_primary_lanes_have_issue_tracker_urls() -> None:
    for definition in PRIMARY_FAMILY_DEFINITIONS:
        assert definition.tracker_url is not None, definition.lane_id
        assert definition.tracker_url.startswith("https://github.com/graphistry/tck-gfql/issues/")
