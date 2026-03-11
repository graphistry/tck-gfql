
from tests.cypher_tck.report import build_report
from tests.cypher_tck.scenarios import SCENARIOS
from tests.cypher_tck.sweep_direct_cypher import _compute_direct_cypher_sets


def test_compute_direct_cypher_sets_tracks_overlap_row_and_error_promotions() -> None:
    scenarios = [
        scenario
        for scenario in SCENARIOS
        if scenario.key in {"return-orderby2-1", "with-orderby1-45-8", "call1-7"}
    ]

    overlap_keys, row_keys, error_keys, overlap_failures, promotion_failures = _compute_direct_cypher_sets(scenarios)

    assert overlap_failures == []
    assert promotion_failures == []
    assert overlap_keys == ["return-orderby2-1"]
    assert row_keys == ["with-orderby1-45-8"]
    assert error_keys == ["call1-7"]


def test_compute_direct_cypher_sets_uses_entity_projection_meta_for_graph_oracle_rows() -> None:
    scenarios = [
        scenario
        for scenario in SCENARIOS
        if scenario.key in {"match1-3", "match-where1-4"}
    ]

    overlap_keys, row_keys, error_keys, overlap_failures, promotion_failures = _compute_direct_cypher_sets(scenarios)

    assert overlap_keys == ["match-where1-4", "match1-3"]
    assert row_keys == []
    assert error_keys == []
    assert overlap_failures == []
    assert promotion_failures == []


def test_build_report_includes_direct_cypher_metrics() -> None:
    report = build_report()

    assert "Direct Cypher overlap on translated-supported scenarios:" in report
    assert "Direct Cypher promoted-only snapshot:" in report
