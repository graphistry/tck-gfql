from tests.cypher_tck.direct_cypher_support import DIRECT_CYPHER_PROMOTION_ERROR_KEYS
from tests.cypher_tck.report import build_report
from tests.cypher_tck.scenarios import SCENARIOS
from tests.cypher_tck import sweep_direct_cypher
from tests.cypher_tck.sweep_direct_cypher import (
    _compute_direct_cypher_nonvalidation_details,
    _compute_direct_cypher_sets,
    _expects_direct_cypher_error_scenario,
    _render_direct_cypher_nonvalidation_details,
)


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


def test_direct_cypher_literal_regressions_are_overlap_supported() -> None:
    literal_keys = {"expr-literals6-11", "expr-literals7-2", "expr-literals7-3"}
    scenarios = [scenario for scenario in SCENARIOS if scenario.key in literal_keys]

    (
        overlap_keys,
        row_keys,
        error_keys,
        overlap_failures,
        promotion_failures,
    ) = _compute_direct_cypher_sets(scenarios)

    assert set(overlap_keys) == literal_keys
    assert row_keys == []
    assert error_keys == []
    assert overlap_failures == []
    assert promotion_failures == []


def test_direct_cypher_with_orderby_scope_regressions_are_overlap_supported() -> None:
    scope_keys = {f"with-orderby1-46-{i}" for i in range(1, 11)}
    scenarios = [scenario for scenario in SCENARIOS if scenario.key in scope_keys]

    (
        overlap_keys,
        row_keys,
        error_keys,
        overlap_failures,
        promotion_failures,
    ) = _compute_direct_cypher_sets(scenarios)

    assert set(overlap_keys) == scope_keys
    assert row_keys == []
    assert error_keys == []
    assert overlap_failures == []
    assert promotion_failures == []


def test_cypher_string_error_tag_is_expected_error_without_legacy_tags(
    monkeypatch,
) -> None:
    scenario = next(
        scenario for scenario in SCENARIOS if scenario.key == "expr-list11-4-1"
    )
    assert scenario.status == "supported"
    assert scenario.reason is None
    assert scenario.expected.rows is None
    assert "cypher-string-error" in scenario.tags
    assert "syntax-error" not in scenario.tags
    assert "runtime-error" not in scenario.tags
    assert _expects_direct_cypher_error_scenario(scenario)

    def fake_run(scenario):
        return True, ""

    monkeypatch.setattr(sweep_direct_cypher, "_run_direct_cypher_scenario", fake_run)

    (
        overlap_keys,
        row_keys,
        error_keys,
        overlap_failures,
        promotion_failures,
    ) = _compute_direct_cypher_sets([scenario])

    assert overlap_keys == []
    assert row_keys == []
    assert error_keys == ["expr-list11-4-1"]
    assert overlap_failures == []
    assert promotion_failures == []


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


def test_compute_direct_cypher_nonvalidation_details_are_sorted_and_focused(
    monkeypatch,
) -> None:
    target_keys = {"expr-quantifier11-3-4", "usecase-countingsubgraphmatches1-1"}
    scenarios = [
        scenario
        for scenario in SCENARIOS
        if scenario.key in target_keys
    ]

    def fake_run(scenario):
        return False, f"detail for {scenario.key}"

    monkeypatch.setattr(sweep_direct_cypher, "_run_direct_cypher_scenario", fake_run)
    monkeypatch.setattr(
        sweep_direct_cypher,
        "DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY",
        {
            "expr-quantifier11-3-4": "unexpected_success_expected_error",
            "usecase-countingsubgraphmatches1-1": "success_wrong_rows",
        },
    )

    details = _compute_direct_cypher_nonvalidation_details(scenarios)

    assert details == [
        (
            "expr-quantifier11-3-4",
            "unexpected_success_expected_error",
            False,
            "detail for expr-quantifier11-3-4",
        ),
        (
            "usecase-countingsubgraphmatches1-1",
            "success_wrong_rows",
            False,
            "detail for usecase-countingsubgraphmatches1-1",
        ),
    ]


def test_render_direct_cypher_nonvalidation_details_supports_limit() -> None:
    lines = _render_direct_cypher_nonvalidation_details(
        [
            ("a", "success_wrong_rows", False, "row mismatch"),
            ("b", "unexpected_success_expected_error", True, ""),
        ],
        limit=1,
    )

    assert lines == [
        "Direct-Cypher non-validation debt details:",
        "- shown: 1 / 2",
        "- a: expected=success_wrong_rows; current=row mismatch",
    ]


def test_direct_cypher_sweep_keeps_promoted_error_scenarios_in_error_bucket() -> None:
    """Regression for cypher-string-error scenarios being swept as row cases."""
    range_error_keys = {
        key
        for key in DIRECT_CYPHER_PROMOTION_ERROR_KEYS
        if key.startswith("expr-list11-4-") or key.startswith("expr-list11-5-")
    }
    scenarios = [scenario for scenario in SCENARIOS if scenario.key in range_error_keys]

    _, _, promotion_error_keys, _, _ = _compute_direct_cypher_sets(scenarios)

    assert set(promotion_error_keys) == range_error_keys
