from tests.cypher_tck import report as report_module
from tests.cypher_tck.gap_priority import (
    build_primary_family_summaries,
    build_priority_lane_summaries,
    classify_primary_xfail_family,
)
from tests.cypher_tck.models import Expected, GraphFixture, Scenario
from tests.cypher_tck.direct_cypher_xfail_contract import (
    DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY,
)
from tests.cypher_tck.report import build_report
from tests.cypher_tck.scenarios import SCENARIOS


def _scenario(key: str):
    return next(scenario for scenario in SCENARIOS if scenario.key == key)


def _dummy_scenario(
    key: str,
    *,
    gfql: object,
    status: str,
    tags: tuple[str, ...] = (),
) -> Scenario:
    return Scenario(
        key=key,
        feature_path="features/test/Area.feature",
        scenario=key,
        cypher="RETURN 1",
        graph=GraphFixture(nodes=(), edges=()),
        expected=Expected(rows=[{"value": 1}]),
        gfql=gfql,
        status=status,
        tags=tags,
    )


def test_classify_primary_xfail_family_maps_representative_keys() -> None:
    assert classify_primary_xfail_family(_scenario("return6-12")) == "grouped-match-aggregates"
    assert classify_primary_xfail_family(_scenario("with-skip-limit1-2")) == "grouped-match-aggregates"
    assert classify_primary_xfail_family(_scenario("match7-29")) == "optional-match-null-extension"
    assert classify_primary_xfail_family(_scenario("unwind1-12")) == "row-pipeline-read-forms"
    assert classify_primary_xfail_family(_scenario("expr-aggregation6-1-1")) == "expression-long-tail"
    assert classify_primary_xfail_family(_scenario("create1-1")) == "write-clauses"
    assert classify_primary_xfail_family(_scenario("call1-1")) == "procedures-and-call"


def test_primary_family_counts_cover_all_xfails() -> None:
    summaries = build_primary_family_summaries(SCENARIOS)
    xfail_count = sum(1 for scenario in SCENARIOS if scenario.status == "xfail")

    assert sum(summary.xfail_count for summary in summaries) == xfail_count


def test_primary_family_counts_stable_for_priority_lanes() -> None:
    summaries = build_primary_family_summaries(SCENARIOS)
    by_lane = {summary.definition.lane_id: summary.xfail_count for summary in summaries}

    assert by_lane["row-pipeline-read-forms"] == 153
    assert by_lane["optional-match-null-extension"] == 61
    assert by_lane["grouped-match-aggregates"] == 26
    assert by_lane["expression-long-tail"] == 128


def test_priority_lane_summaries_include_tracker_refs_and_samples() -> None:
    summaries = build_priority_lane_summaries(SCENARIOS)
    grouped = next(
        summary
        for summary in summaries
        if summary.definition.lane_id == "grouped-match-aggregates"
    )

    assert grouped.definition.tracker_ref == "#45"
    assert grouped.definition.tracker_url == "https://github.com/graphistry/tck-gfql/issues/45"
    assert "return6-12" in grouped.sample_keys
    assert grouped.signal.startswith("read-only relationship aggregate xfails:")


def test_build_report_includes_gap_priority_sections() -> None:
    report = build_report()

    assert "Primary xfail families (disjoint heuristic):" in report
    assert "Priority candidate lanes:" in report
    assert "Supported-subset correctness / failfast audit" in report
    assert (
        "Promoted via direct Cypher string only (status/tagged): "
        "887 (rows 774, errors 113)"
    ) in report
    assert "#45" in report
    assert "Representative tracked scenarios:" in report
    assert "Direct local Cypher xfail contract:" in report
    assert "validation-safe xfails:" in report
    assert "Ownership split (heuristic):" in report
    assert "tck-governance lanes with concrete issue trackers:" in report
    assert "tck-governance lanes still TODO-tracked: 0" in report
    assert (
        f"tracked non-validation debt: {len(DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY)}"
        in report
    )
    assert "Direct local Cypher non-validation triage samples:" in report
    assert "- success_wrong_rows:" in report
    assert "expr-pattern1-10 (expressions/pattern)" in report
    assert "match5-25 (clauses/match)" in report
    assert "- unexpected_success_expected_error:" not in report


def test_direct_cypher_nonvalidation_samples_are_stable_and_bounded() -> None:
    samples = report_module._direct_cypher_nonvalidation_samples(SCENARIOS, per_outcome=2)

    assert samples["success_wrong_rows"] == [
        "expr-pattern1-10 (expressions/pattern)",
        "expr-pattern1-13 (expressions/pattern)",
        "... 5 more",
    ]
    assert "unexpected_success_expected_error" not in samples


def test_live_direct_cypher_snapshot_sets_filter_stale_keys(monkeypatch) -> None:
    scenarios = [
        _dummy_scenario("translated", gfql=("match",), status="supported"),
        _dummy_scenario(
            "direct-row-only",
            gfql=None,
            status="supported",
            tags=("cypher-string",),
        ),
        _dummy_scenario("direct-error-only", gfql=None, status="xfail"),
    ]

    monkeypatch.setattr(
        report_module,
        "DIRECT_CYPHER_OVERLAP_KEYS",
        {"translated", "stale-overlap"},
    )
    monkeypatch.setattr(
        report_module,
        "DIRECT_CYPHER_PROMOTION_ROW_KEYS",
        {"direct-row-only", "stale-promotion", "translated"},
    )
    monkeypatch.setattr(
        report_module,
        "DIRECT_CYPHER_PROMOTION_ERROR_KEYS",
        {"direct-error-only", "stale-error"},
    )

    overlap_keys, promotion_row_keys, promotion_error_keys = (
        report_module._live_direct_cypher_snapshot_sets(scenarios)
    )

    assert overlap_keys == {"translated"}
    assert promotion_row_keys == {"direct-row-only"}
    assert promotion_error_keys == {"direct-error-only"}
