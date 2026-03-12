from tests.cypher_tck.gap_priority import (
    build_primary_family_summaries,
    build_priority_lane_summaries,
    classify_primary_xfail_family,
)
from tests.cypher_tck.direct_cypher_xfail_contract import (
    DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY,
)
from tests.cypher_tck.report import build_report
from tests.cypher_tck.scenarios import SCENARIOS


def _scenario(key: str):
    return next(scenario for scenario in SCENARIOS if scenario.key == key)


def test_classify_primary_xfail_family_maps_representative_keys() -> None:
    assert classify_primary_xfail_family(_scenario("return6-12")) == "grouped-match-aggregates"
    assert classify_primary_xfail_family(_scenario("with-skip-limit1-2")) == "grouped-match-aggregates"
    assert classify_primary_xfail_family(_scenario("match7-29")) == "optional-match-null-extension"
    assert classify_primary_xfail_family(_scenario("unwind1-12")) == "row-pipeline-read-forms"
    assert classify_primary_xfail_family(_scenario("expr-aggregation3-1")) == "expression-long-tail"
    assert classify_primary_xfail_family(_scenario("create1-1")) == "write-clauses"
    assert classify_primary_xfail_family(_scenario("call1-1")) == "procedures-and-call"


def test_primary_family_counts_cover_all_xfails() -> None:
    summaries = build_primary_family_summaries(SCENARIOS)
    xfail_count = sum(1 for scenario in SCENARIOS if scenario.status == "xfail")

    assert sum(summary.xfail_count for summary in summaries) == xfail_count


def test_priority_lane_summaries_include_tracker_refs_and_samples() -> None:
    summaries = build_priority_lane_summaries(SCENARIOS)
    grouped = next(
        summary
        for summary in summaries
        if summary.definition.lane_id == "grouped-match-aggregates"
    )

    assert grouped.definition.tracker_ref == "TODO(meta-issue): multiplicity carrier PR2-PR4"
    assert "return6-12" in grouped.sample_keys
    assert grouped.signal.startswith("read-only relationship aggregate xfails:")


def test_build_report_includes_gap_priority_sections() -> None:
    report = build_report()

    assert "Primary xfail families (disjoint heuristic):" in report
    assert "Priority candidate lanes:" in report
    assert "Supported-subset correctness / failfast audit" in report
    assert "TODO(meta-issue): multiplicity carrier PR2-PR4" in report
    assert "Representative tracked scenarios:" in report
    assert "Direct local Cypher xfail contract:" in report
    assert "validation-safe xfails:" in report
    assert (
        f"tracked non-validation debt: {len(DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY)}"
        in report
    )
