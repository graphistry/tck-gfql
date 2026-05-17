from __future__ import annotations

from tests.cypher_tck.gap_priority import (
    PRIMARY_FAMILY_DEFINITIONS,
    classify_primary_xfail_family,
)
from tests.cypher_tck.direct_cypher_support import (
    DIRECT_CYPHER_PROMOTION_ERROR_KEYS,
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
    EXPRESSION_LONG_TAIL_TRANCHE4_EXPECTED_STATUS,
    EXPRESSION_LONG_TAIL_TRANCHE4_FORBIDDEN_TAGS,
    EXPRESSION_LONG_TAIL_TRANCHE4_KEYS,
    EXPRESSION_LONG_TAIL_TRANCHE5_EXPECTED_STATUS,
    EXPRESSION_LONG_TAIL_TRANCHE5_FORBIDDEN_TAGS,
    EXPRESSION_LONG_TAIL_TRANCHE5_KEYS,
    EXPRESSION_LONG_TAIL_TRANCHE6_EXPECTED_STATUS,
    EXPRESSION_LONG_TAIL_TRANCHE6_FORBIDDEN_TAGS,
    EXPRESSION_LONG_TAIL_TRANCHE6_KEYS,
    EXPRESSION_LONG_TAIL_TRANCHE7_EXPECTED_STATUS,
    EXPRESSION_LONG_TAIL_TRANCHE7_FORBIDDEN_TAGS,
    EXPRESSION_LONG_TAIL_TRANCHE7_KEYS,
    EXPRESSION_LONG_TAIL_TRANCHE8_EXPECTED_STATUS,
    EXPRESSION_LONG_TAIL_TRANCHE8_FORBIDDEN_TAGS,
    EXPRESSION_LONG_TAIL_TRANCHE8_KEYS,
    EXPRESSION_LONG_TAIL_TRANCHE9_EXPECTED_STATUS,
    EXPRESSION_LONG_TAIL_TRANCHE9_FORBIDDEN_TAGS,
    EXPRESSION_LONG_TAIL_TRANCHE9_KEYS,
    GROUPED_MATCH_AGG_TRANCHE1_EXPECTED_STATUS,
    GROUPED_MATCH_AGG_TRANCHE1_FORBIDDEN_TAGS,
    GROUPED_MATCH_AGG_TRANCHE1_KEYS,
    GROUPED_MATCH_AGG_TRANCHE2_EXPECTED_STATUS,
    GROUPED_MATCH_AGG_TRANCHE2_FORBIDDEN_TAGS,
    GROUPED_MATCH_AGG_TRANCHE2_KEYS,
    GROUPED_MATCH_AGG_TRANCHE3_EXPECTED_STATUS,
    GROUPED_MATCH_AGG_TRANCHE3_FORBIDDEN_TAGS,
    GROUPED_MATCH_AGG_TRANCHE3_KEYS,
    OPTIONAL_NULL_TRANCHE1_EXPECTED_STATUS,
    OPTIONAL_NULL_TRANCHE1_FORBIDDEN_TAGS,
    OPTIONAL_NULL_TRANCHE1_KEYS,
    OPTIONAL_NULL_TRANCHE2_EXPECTED_STATUS,
    OPTIONAL_NULL_TRANCHE2_FORBIDDEN_TAGS,
    OPTIONAL_NULL_TRANCHE2_KEYS,
    OPTIONAL_NULL_TRANCHE3_EXPECTED_STATUS,
    OPTIONAL_NULL_TRANCHE3_FORBIDDEN_TAGS,
    OPTIONAL_NULL_TRANCHE3_KEYS,
    OPTIONAL_NULL_TRANCHE4_EXPECTED_STATUS,
    OPTIONAL_NULL_TRANCHE4_FORBIDDEN_TAGS,
    OPTIONAL_NULL_TRANCHE4_KEYS,
    OTHER_READ_GAPS_TRANCHE1_EXPECTED_STATUS,
    OTHER_READ_GAPS_TRANCHE1_FORBIDDEN_TAGS,
    OTHER_READ_GAPS_TRANCHE1_KEYS,
    PROCEDURES_CALL_TRANCHE1_EXPECTED_STATUS,
    PROCEDURES_CALL_TRANCHE1_FORBIDDEN_TAGS,
    PROCEDURES_CALL_TRANCHE1_KEYS,
    ROW_PIPELINE_TRANCHE1_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE1_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE1_KEYS,
    ROW_PIPELINE_TRANCHE10_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE10_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE10_KEYS,
    ROW_PIPELINE_TRANCHE11_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE11_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE11_KEYS,
    ROW_PIPELINE_TRANCHE12_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE12_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE12_KEYS,
    ROW_PIPELINE_TRANCHE13_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE13_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE13_KEYS,
    ROW_PIPELINE_TRANCHE14_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE14_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE14_KEYS,
    ROW_PIPELINE_TRANCHE2_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE2_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE2_KEYS,
    ROW_PIPELINE_TRANCHE3_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE3_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE3_KEYS,
    ROW_PIPELINE_TRANCHE4_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE4_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE4_KEYS,
    ROW_PIPELINE_TRANCHE5_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE5_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE5_KEYS,
    ROW_PIPELINE_TRANCHE6_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE6_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE6_KEYS,
    ROW_PIPELINE_TRANCHE7_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE7_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE7_KEYS,
    ROW_PIPELINE_TRANCHE8_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE8_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE8_KEYS,
    ROW_PIPELINE_TRANCHE9_EXPECTED_STATUS,
    ROW_PIPELINE_TRANCHE9_FORBIDDEN_TAGS,
    ROW_PIPELINE_TRANCHE9_KEYS,
    WRITE_CLAUSES_TRANCHE1_EXPECTED_STATUS,
    WRITE_CLAUSES_TRANCHE1_FORBIDDEN_TAGS,
    WRITE_CLAUSES_TRANCHE1_KEYS,
)
from tests.cypher_tck.scenarios import SCENARIOS


def _scenario_map():
    return {scenario.key: scenario for scenario in SCENARIOS}


# Keys deliberately promoted out of xfail via the direct-Cypher path: either
# row-oracle matches or expected-error scenarios. Lane tranche contracts treat
# any of these as allowably "supported" rather than a regression.
_DIRECT_CYPHER_PROMOTED_KEYS = (
    set(DIRECT_CYPHER_PROMOTED_FROM_XFAIL_MATCHES_EXPECTED_KEYS)
    | set(DIRECT_CYPHER_PROMOTION_ERROR_KEYS)
)


def _is_direct_cypher_promoted(key: str) -> bool:
    return key in _DIRECT_CYPHER_PROMOTED_KEYS


def _assert_status_and_tags(scenario, expected_status: str, forbidden_tags: tuple[str, ...]) -> None:
    if _is_direct_cypher_promoted(scenario.key):
        assert scenario.status == "supported"
        assert "cypher-string" in scenario.tags
        return

    assert scenario.status == expected_status
    for forbidden_tag in forbidden_tags:
        assert forbidden_tag not in scenario.tags


def _assert_family_or_direct_promoted(scenario, family: str) -> None:
    if _is_direct_cypher_promoted(scenario.key):
        assert scenario.status == "supported"
        assert "cypher-string" in scenario.tags
        return

    assert classify_primary_xfail_family(scenario) == family


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


def test_row_pipeline_tranche2_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(ROW_PIPELINE_TRANCHE2_KEYS) - set(scenarios))
    assert missing == []


def test_row_pipeline_tranche2_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE2_KEYS:
        scenario = scenarios[key]
        assert scenario.status == ROW_PIPELINE_TRANCHE2_EXPECTED_STATUS
        for forbidden_tag in ROW_PIPELINE_TRANCHE2_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_row_pipeline_tranche2_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE2_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "row-pipeline-read-forms"


def test_row_pipeline_tranche3_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(ROW_PIPELINE_TRANCHE3_KEYS) - set(scenarios))
    assert missing == []


def test_row_pipeline_tranche3_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE3_KEYS:
        scenario = scenarios[key]
        _assert_status_and_tags(
            scenario,
            ROW_PIPELINE_TRANCHE3_EXPECTED_STATUS,
            ROW_PIPELINE_TRANCHE3_FORBIDDEN_TAGS,
        )


def test_row_pipeline_tranche3_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE3_KEYS:
        scenario = scenarios[key]
        _assert_family_or_direct_promoted(scenario, "row-pipeline-read-forms")


def test_row_pipeline_tranche4_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(ROW_PIPELINE_TRANCHE4_KEYS) - set(scenarios))
    assert missing == []


def test_row_pipeline_tranche4_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE4_KEYS:
        scenario = scenarios[key]
        assert scenario.status == ROW_PIPELINE_TRANCHE4_EXPECTED_STATUS
        for forbidden_tag in ROW_PIPELINE_TRANCHE4_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_row_pipeline_tranche4_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE4_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "row-pipeline-read-forms"


def test_row_pipeline_tranche5_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(ROW_PIPELINE_TRANCHE5_KEYS) - set(scenarios))
    assert missing == []


def test_row_pipeline_tranche5_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE5_KEYS:
        scenario = scenarios[key]
        assert scenario.status == ROW_PIPELINE_TRANCHE5_EXPECTED_STATUS
        for forbidden_tag in ROW_PIPELINE_TRANCHE5_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_row_pipeline_tranche5_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE5_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "row-pipeline-read-forms"


def test_row_pipeline_tranche6_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(ROW_PIPELINE_TRANCHE6_KEYS) - set(scenarios))
    assert missing == []


def test_row_pipeline_tranche6_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE6_KEYS:
        scenario = scenarios[key]
        assert scenario.status == ROW_PIPELINE_TRANCHE6_EXPECTED_STATUS
        for forbidden_tag in ROW_PIPELINE_TRANCHE6_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_row_pipeline_tranche6_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE6_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "row-pipeline-read-forms"


def test_row_pipeline_tranche7_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(ROW_PIPELINE_TRANCHE7_KEYS) - set(scenarios))
    assert missing == []


def test_row_pipeline_tranche7_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE7_KEYS:
        scenario = scenarios[key]
        assert scenario.status == ROW_PIPELINE_TRANCHE7_EXPECTED_STATUS
        for forbidden_tag in ROW_PIPELINE_TRANCHE7_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_row_pipeline_tranche7_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE7_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "row-pipeline-read-forms"


def test_row_pipeline_tranche8_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(ROW_PIPELINE_TRANCHE8_KEYS) - set(scenarios))
    assert missing == []


def test_row_pipeline_tranche8_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE8_KEYS:
        scenario = scenarios[key]
        assert scenario.status == ROW_PIPELINE_TRANCHE8_EXPECTED_STATUS
        for forbidden_tag in ROW_PIPELINE_TRANCHE8_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_row_pipeline_tranche8_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE8_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "row-pipeline-read-forms"


def test_row_pipeline_tranche9_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(ROW_PIPELINE_TRANCHE9_KEYS) - set(scenarios))
    assert missing == []


def test_row_pipeline_tranche9_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE9_KEYS:
        scenario = scenarios[key]
        assert scenario.status == ROW_PIPELINE_TRANCHE9_EXPECTED_STATUS
        for forbidden_tag in ROW_PIPELINE_TRANCHE9_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_row_pipeline_tranche9_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE9_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "row-pipeline-read-forms"


def test_row_pipeline_tranche10_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(ROW_PIPELINE_TRANCHE10_KEYS) - set(scenarios))
    assert missing == []


def test_row_pipeline_tranche10_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE10_KEYS:
        scenario = scenarios[key]
        assert scenario.status == ROW_PIPELINE_TRANCHE10_EXPECTED_STATUS
        for forbidden_tag in ROW_PIPELINE_TRANCHE10_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_row_pipeline_tranche10_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE10_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "row-pipeline-read-forms"


def test_row_pipeline_tranche11_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(ROW_PIPELINE_TRANCHE11_KEYS) - set(scenarios))
    assert missing == []


def test_row_pipeline_tranche11_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE11_KEYS:
        scenario = scenarios[key]
        assert scenario.status == ROW_PIPELINE_TRANCHE11_EXPECTED_STATUS
        for forbidden_tag in ROW_PIPELINE_TRANCHE11_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_row_pipeline_tranche11_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE11_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "row-pipeline-read-forms"


def test_row_pipeline_tranche12_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(ROW_PIPELINE_TRANCHE12_KEYS) - set(scenarios))
    assert missing == []


def test_row_pipeline_tranche12_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE12_KEYS:
        scenario = scenarios[key]
        assert scenario.status == ROW_PIPELINE_TRANCHE12_EXPECTED_STATUS
        for forbidden_tag in ROW_PIPELINE_TRANCHE12_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_row_pipeline_tranche12_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE12_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "row-pipeline-read-forms"


def test_row_pipeline_tranche13_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(ROW_PIPELINE_TRANCHE13_KEYS) - set(scenarios))
    assert missing == []


def test_row_pipeline_tranche13_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE13_KEYS:
        scenario = scenarios[key]
        _assert_status_and_tags(
            scenario,
            ROW_PIPELINE_TRANCHE13_EXPECTED_STATUS,
            ROW_PIPELINE_TRANCHE13_FORBIDDEN_TAGS,
        )


def test_row_pipeline_tranche13_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE13_KEYS:
        scenario = scenarios[key]
        _assert_family_or_direct_promoted(scenario, "row-pipeline-read-forms")


def test_row_pipeline_tranche14_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(ROW_PIPELINE_TRANCHE14_KEYS) - set(scenarios))
    assert missing == []


def test_row_pipeline_tranche14_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE14_KEYS:
        scenario = scenarios[key]
        _assert_status_and_tags(
            scenario,
            ROW_PIPELINE_TRANCHE14_EXPECTED_STATUS,
            ROW_PIPELINE_TRANCHE14_FORBIDDEN_TAGS,
        )


def test_row_pipeline_tranche14_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in ROW_PIPELINE_TRANCHE14_KEYS:
        scenario = scenarios[key]
        _assert_family_or_direct_promoted(scenario, "row-pipeline-read-forms")


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


def test_grouped_match_aggregate_tranche2_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(GROUPED_MATCH_AGG_TRANCHE2_KEYS) - set(scenarios))
    assert missing == []


def test_grouped_match_aggregate_tranche2_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in GROUPED_MATCH_AGG_TRANCHE2_KEYS:
        scenario = scenarios[key]
        assert scenario.status == GROUPED_MATCH_AGG_TRANCHE2_EXPECTED_STATUS
        for forbidden_tag in GROUPED_MATCH_AGG_TRANCHE2_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_grouped_match_aggregate_tranche2_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in GROUPED_MATCH_AGG_TRANCHE2_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "grouped-match-aggregates"


def test_grouped_match_aggregate_tranche3_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(GROUPED_MATCH_AGG_TRANCHE3_KEYS) - set(scenarios))
    assert missing == []


def test_grouped_match_aggregate_tranche3_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in GROUPED_MATCH_AGG_TRANCHE3_KEYS:
        scenario = scenarios[key]
        assert scenario.status == GROUPED_MATCH_AGG_TRANCHE3_EXPECTED_STATUS
        for forbidden_tag in GROUPED_MATCH_AGG_TRANCHE3_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_grouped_match_aggregate_tranche3_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in GROUPED_MATCH_AGG_TRANCHE3_KEYS:
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


def test_optional_null_tranche2_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(OPTIONAL_NULL_TRANCHE2_KEYS) - set(scenarios))
    assert missing == []


def test_optional_null_tranche2_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in OPTIONAL_NULL_TRANCHE2_KEYS:
        scenario = scenarios[key]
        assert scenario.status == OPTIONAL_NULL_TRANCHE2_EXPECTED_STATUS
        for forbidden_tag in OPTIONAL_NULL_TRANCHE2_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_optional_null_tranche2_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in OPTIONAL_NULL_TRANCHE2_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "optional-match-null-extension"


def test_optional_null_tranche3_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(OPTIONAL_NULL_TRANCHE3_KEYS) - set(scenarios))
    assert missing == []


def test_optional_null_tranche3_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in OPTIONAL_NULL_TRANCHE3_KEYS:
        scenario = scenarios[key]
        assert scenario.status == OPTIONAL_NULL_TRANCHE3_EXPECTED_STATUS
        for forbidden_tag in OPTIONAL_NULL_TRANCHE3_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_optional_null_tranche3_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in OPTIONAL_NULL_TRANCHE3_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "optional-match-null-extension"


def test_optional_null_tranche4_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(OPTIONAL_NULL_TRANCHE4_KEYS) - set(scenarios))
    assert missing == []


def test_optional_null_tranche4_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in OPTIONAL_NULL_TRANCHE4_KEYS:
        scenario = scenarios[key]
        _assert_status_and_tags(
            scenario,
            OPTIONAL_NULL_TRANCHE4_EXPECTED_STATUS,
            OPTIONAL_NULL_TRANCHE4_FORBIDDEN_TAGS,
        )


def test_optional_null_tranche4_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in OPTIONAL_NULL_TRANCHE4_KEYS:
        scenario = scenarios[key]
        _assert_family_or_direct_promoted(scenario, "optional-match-null-extension")


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
    promoted = _DIRECT_CYPHER_PROMOTED_KEYS
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
    promoted = _DIRECT_CYPHER_PROMOTED_KEYS
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


def test_expression_long_tail_tranche4_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(EXPRESSION_LONG_TAIL_TRANCHE4_KEYS) - set(scenarios))
    assert missing == []


def test_expression_long_tail_tranche4_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE4_KEYS:
        scenario = scenarios[key]
        _assert_status_and_tags(
            scenario,
            EXPRESSION_LONG_TAIL_TRANCHE4_EXPECTED_STATUS,
            EXPRESSION_LONG_TAIL_TRANCHE4_FORBIDDEN_TAGS,
        )


def test_expression_long_tail_tranche4_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE4_KEYS:
        scenario = scenarios[key]
        _assert_family_or_direct_promoted(scenario, "expression-long-tail")


def test_expression_long_tail_tranche5_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(EXPRESSION_LONG_TAIL_TRANCHE5_KEYS) - set(scenarios))
    assert missing == []


def test_expression_long_tail_tranche5_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE5_KEYS:
        scenario = scenarios[key]
        _assert_status_and_tags(
            scenario,
            EXPRESSION_LONG_TAIL_TRANCHE5_EXPECTED_STATUS,
            EXPRESSION_LONG_TAIL_TRANCHE5_FORBIDDEN_TAGS,
        )


def test_expression_long_tail_tranche5_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE5_KEYS:
        scenario = scenarios[key]
        _assert_family_or_direct_promoted(scenario, "expression-long-tail")


def test_expression_long_tail_tranche6_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(EXPRESSION_LONG_TAIL_TRANCHE6_KEYS) - set(scenarios))
    assert missing == []


def test_expression_long_tail_tranche6_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE6_KEYS:
        scenario = scenarios[key]
        _assert_status_and_tags(
            scenario,
            EXPRESSION_LONG_TAIL_TRANCHE6_EXPECTED_STATUS,
            EXPRESSION_LONG_TAIL_TRANCHE6_FORBIDDEN_TAGS,
        )


def test_expression_long_tail_tranche6_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE6_KEYS:
        scenario = scenarios[key]
        _assert_family_or_direct_promoted(scenario, "expression-long-tail")


def test_expression_long_tail_tranche7_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(EXPRESSION_LONG_TAIL_TRANCHE7_KEYS) - set(scenarios))
    assert missing == []


def test_expression_long_tail_tranche7_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE7_KEYS:
        scenario = scenarios[key]
        _assert_status_and_tags(
            scenario,
            EXPRESSION_LONG_TAIL_TRANCHE7_EXPECTED_STATUS,
            EXPRESSION_LONG_TAIL_TRANCHE7_FORBIDDEN_TAGS,
        )


def test_expression_long_tail_tranche7_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE7_KEYS:
        scenario = scenarios[key]
        _assert_family_or_direct_promoted(scenario, "expression-long-tail")


def test_expression_long_tail_tranche8_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(EXPRESSION_LONG_TAIL_TRANCHE8_KEYS) - set(scenarios))
    assert missing == []


def test_expression_long_tail_tranche8_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE8_KEYS:
        scenario = scenarios[key]
        _assert_status_and_tags(
            scenario,
            EXPRESSION_LONG_TAIL_TRANCHE8_EXPECTED_STATUS,
            EXPRESSION_LONG_TAIL_TRANCHE8_FORBIDDEN_TAGS,
        )


def test_expression_long_tail_tranche8_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE8_KEYS:
        scenario = scenarios[key]
        _assert_family_or_direct_promoted(scenario, "expression-long-tail")


def test_expression_long_tail_tranche9_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(EXPRESSION_LONG_TAIL_TRANCHE9_KEYS) - set(scenarios))
    assert missing == []


def test_expression_long_tail_tranche9_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE9_KEYS:
        scenario = scenarios[key]
        _assert_status_and_tags(
            scenario,
            EXPRESSION_LONG_TAIL_TRANCHE9_EXPECTED_STATUS,
            EXPRESSION_LONG_TAIL_TRANCHE9_FORBIDDEN_TAGS,
        )


def test_expression_long_tail_tranche9_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in EXPRESSION_LONG_TAIL_TRANCHE9_KEYS:
        scenario = scenarios[key]
        _assert_family_or_direct_promoted(scenario, "expression-long-tail")


def test_row_pipeline_tranches_are_disjoint() -> None:
    tranches = (
        set(ROW_PIPELINE_TRANCHE1_KEYS),
        set(ROW_PIPELINE_TRANCHE2_KEYS),
        set(ROW_PIPELINE_TRANCHE3_KEYS),
        set(ROW_PIPELINE_TRANCHE4_KEYS),
        set(ROW_PIPELINE_TRANCHE5_KEYS),
        set(ROW_PIPELINE_TRANCHE6_KEYS),
        set(ROW_PIPELINE_TRANCHE7_KEYS),
        set(ROW_PIPELINE_TRANCHE8_KEYS),
        set(ROW_PIPELINE_TRANCHE9_KEYS),
        set(ROW_PIPELINE_TRANCHE10_KEYS),
        set(ROW_PIPELINE_TRANCHE11_KEYS),
        set(ROW_PIPELINE_TRANCHE12_KEYS),
        set(ROW_PIPELINE_TRANCHE13_KEYS),
        set(ROW_PIPELINE_TRANCHE14_KEYS),
    )
    for idx, left in enumerate(tranches):
        for right in tranches[idx + 1 :]:
            assert left.isdisjoint(right)


def test_optional_null_tranches_are_disjoint() -> None:
    t1 = set(OPTIONAL_NULL_TRANCHE1_KEYS)
    t2 = set(OPTIONAL_NULL_TRANCHE2_KEYS)
    t3 = set(OPTIONAL_NULL_TRANCHE3_KEYS)
    t4 = set(OPTIONAL_NULL_TRANCHE4_KEYS)
    assert t1.isdisjoint(t2)
    assert t1.isdisjoint(t3)
    assert t1.isdisjoint(t4)
    assert t2.isdisjoint(t3)
    assert t2.isdisjoint(t4)
    assert t3.isdisjoint(t4)


def test_grouped_match_aggregate_tranches_are_disjoint() -> None:
    t1 = set(GROUPED_MATCH_AGG_TRANCHE1_KEYS)
    t2 = set(GROUPED_MATCH_AGG_TRANCHE2_KEYS)
    t3 = set(GROUPED_MATCH_AGG_TRANCHE3_KEYS)
    assert t1.isdisjoint(t2)
    assert t1.isdisjoint(t3)
    assert t2.isdisjoint(t3)


def test_expression_long_tail_tranches_are_disjoint() -> None:
    tranches = (
        set(EXPRESSION_LONG_TAIL_TRANCHE1_KEYS),
        set(EXPRESSION_LONG_TAIL_TRANCHE2_KEYS),
        set(EXPRESSION_LONG_TAIL_TRANCHE3_KEYS),
        set(EXPRESSION_LONG_TAIL_TRANCHE4_KEYS),
        set(EXPRESSION_LONG_TAIL_TRANCHE5_KEYS),
        set(EXPRESSION_LONG_TAIL_TRANCHE6_KEYS),
        set(EXPRESSION_LONG_TAIL_TRANCHE7_KEYS),
        set(EXPRESSION_LONG_TAIL_TRANCHE8_KEYS),
        set(EXPRESSION_LONG_TAIL_TRANCHE9_KEYS),
    )
    for idx, left in enumerate(tranches):
        for right in tranches[idx + 1 :]:
            assert left.isdisjoint(right)


def test_row_pipeline_contract_coverage_floor() -> None:
    # Keep row-pipeline lane coverage non-decreasing across follow-on tranche work.
    coverage_floor = 154  # 6 + 12 + 21 + 20 + 15 + 15 + 15 + 7 + 6 + 5 + 4 + 4 + 4 + 20
    covered = (
        set(ROW_PIPELINE_TRANCHE1_KEYS)
        | set(ROW_PIPELINE_TRANCHE2_KEYS)
        | set(ROW_PIPELINE_TRANCHE3_KEYS)
        | set(ROW_PIPELINE_TRANCHE4_KEYS)
        | set(ROW_PIPELINE_TRANCHE5_KEYS)
        | set(ROW_PIPELINE_TRANCHE6_KEYS)
        | set(ROW_PIPELINE_TRANCHE7_KEYS)
        | set(ROW_PIPELINE_TRANCHE8_KEYS)
        | set(ROW_PIPELINE_TRANCHE9_KEYS)
        | set(ROW_PIPELINE_TRANCHE10_KEYS)
        | set(ROW_PIPELINE_TRANCHE11_KEYS)
        | set(ROW_PIPELINE_TRANCHE12_KEYS)
        | set(ROW_PIPELINE_TRANCHE13_KEYS)
        | set(ROW_PIPELINE_TRANCHE14_KEYS)
    )
    assert len(covered) >= coverage_floor


def test_expression_long_tail_contract_coverage_floor() -> None:
    # Keep expression long-tail lane coverage non-decreasing across tranche expansion.
    coverage_floor = 173  # 42 + 27 + 12 + 15 + 15 + 24 + 20 + 9 + 9
    covered = (
        set(EXPRESSION_LONG_TAIL_TRANCHE1_KEYS)
        | set(EXPRESSION_LONG_TAIL_TRANCHE2_KEYS)
        | set(EXPRESSION_LONG_TAIL_TRANCHE3_KEYS)
        | set(EXPRESSION_LONG_TAIL_TRANCHE4_KEYS)
        | set(EXPRESSION_LONG_TAIL_TRANCHE5_KEYS)
        | set(EXPRESSION_LONG_TAIL_TRANCHE6_KEYS)
        | set(EXPRESSION_LONG_TAIL_TRANCHE7_KEYS)
        | set(EXPRESSION_LONG_TAIL_TRANCHE8_KEYS)
        | set(EXPRESSION_LONG_TAIL_TRANCHE9_KEYS)
    )
    assert len(covered) >= coverage_floor


def test_other_read_gaps_tranche1_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(OTHER_READ_GAPS_TRANCHE1_KEYS) - set(scenarios))
    assert missing == []


def test_other_read_gaps_tranche1_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in OTHER_READ_GAPS_TRANCHE1_KEYS:
        scenario = scenarios[key]
        _assert_status_and_tags(
            scenario,
            OTHER_READ_GAPS_TRANCHE1_EXPECTED_STATUS,
            OTHER_READ_GAPS_TRANCHE1_FORBIDDEN_TAGS,
        )


def test_other_read_gaps_tranche1_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in OTHER_READ_GAPS_TRANCHE1_KEYS:
        scenario = scenarios[key]
        _assert_family_or_direct_promoted(scenario, "other-read-gaps")


def test_other_read_gaps_lane_has_issue_tracker_wired() -> None:
    other_read_gaps = next(
        definition
        for definition in PRIMARY_FAMILY_DEFINITIONS
        if definition.lane_id == "other-read-gaps"
    )
    assert other_read_gaps.tracker_ref == "#52"
    assert other_read_gaps.tracker_url == "https://github.com/graphistry/tck-gfql/issues/52"


def test_write_clauses_tranche1_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(WRITE_CLAUSES_TRANCHE1_KEYS) - set(scenarios))
    assert missing == []


def test_write_clauses_tranche1_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in WRITE_CLAUSES_TRANCHE1_KEYS:
        scenario = scenarios[key]
        assert scenario.status == WRITE_CLAUSES_TRANCHE1_EXPECTED_STATUS
        for forbidden_tag in WRITE_CLAUSES_TRANCHE1_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_write_clauses_tranche1_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in WRITE_CLAUSES_TRANCHE1_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "write-clauses"


def test_write_clauses_lane_has_issue_tracker_wired() -> None:
    write_clauses = next(
        definition
        for definition in PRIMARY_FAMILY_DEFINITIONS
        if definition.lane_id == "write-clauses"
    )
    assert write_clauses.tracker_ref == "#54"
    assert write_clauses.tracker_url == "https://github.com/graphistry/tck-gfql/issues/54"


def test_procedures_call_tranche1_keys_exist() -> None:
    scenarios = _scenario_map()
    missing = sorted(set(PROCEDURES_CALL_TRANCHE1_KEYS) - set(scenarios))
    assert missing == []


def test_procedures_call_tranche1_status_and_tag_contract() -> None:
    scenarios = _scenario_map()
    for key in PROCEDURES_CALL_TRANCHE1_KEYS:
        scenario = scenarios[key]
        assert scenario.status == PROCEDURES_CALL_TRANCHE1_EXPECTED_STATUS
        for forbidden_tag in PROCEDURES_CALL_TRANCHE1_FORBIDDEN_TAGS:
            assert forbidden_tag not in scenario.tags


def test_procedures_call_tranche1_family_classification_contract() -> None:
    scenarios = _scenario_map()
    for key in PROCEDURES_CALL_TRANCHE1_KEYS:
        scenario = scenarios[key]
        assert classify_primary_xfail_family(scenario) == "procedures-and-call"


def test_procedures_call_lane_has_issue_tracker_wired() -> None:
    procedures_call = next(
        definition
        for definition in PRIMARY_FAMILY_DEFINITIONS
        if definition.lane_id == "procedures-and-call"
    )
    assert procedures_call.tracker_ref == "#53"
    assert procedures_call.tracker_url == "https://github.com/graphistry/tck-gfql/issues/53"


def test_all_primary_lanes_have_concrete_issue_tracker_refs() -> None:
    for definition in PRIMARY_FAMILY_DEFINITIONS:
        assert definition.tracker_ref.startswith("#"), definition.lane_id


def test_all_primary_lanes_have_issue_tracker_urls() -> None:
    for definition in PRIMARY_FAMILY_DEFINITIONS:
        assert definition.tracker_url is not None, definition.lane_id
        assert definition.tracker_url.startswith("https://github.com/graphistry/tck-gfql/issues/")
