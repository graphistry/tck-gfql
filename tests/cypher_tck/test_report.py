import json

from tests.cypher_tck import report as report_module
from tests.cypher_tck.capability_debt_manifest import build_manifest
from tests.cypher_tck.direct_cypher_support import DIRECT_CYPHER_PROMOTION_ROW_KEYS
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


def test_match5_8_promotion_bookkeeping_is_resolved() -> None:
    scenario = _scenario("match5-8")
    artifact = report_module.build_json_artifact(generated_at="1970-01-01T00:00:00Z")
    debt_by_key = {entry["key"]: entry for entry in artifact["debt_keys"]}
    manifest_entry = next(
        entry
        for entry in build_manifest()["scenario_entries"]
        if entry["key"] == "match5-8"
    )

    assert scenario.status == "supported"
    assert scenario.gfql is None
    assert "cypher-string" in scenario.tags
    assert "xfail" not in scenario.tags
    assert "match5-8" in DIRECT_CYPHER_PROMOTION_ROW_KEYS
    assert "match5-8" not in DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY
    assert "match5-8" not in debt_by_key
    assert (
        artifact["expected_error_counts"]["direct_cypher_nonvalidation_by_outcome"].get(
            "success_matches_expected", 0
        )
        == 0
    )
    assert manifest_entry == {
        "key": "match5-8",
        "support_status": "supported",
        "implementation_status": "direct_cypher_only",
        "ownership": "direct-cypher-promotion",
        "tags": [
            "cypher-string",
            "cypher-string-pure",
            "match",
            "variable-length",
        ],
    }


def _dummy_scenario(
    key: str,
    *,
    gfql: tuple[object, ...] | None,
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
    assert (
        classify_primary_xfail_family(_scenario("return6-12"))
        == "grouped-match-aggregates"
    )
    assert (
        classify_primary_xfail_family(_scenario("with-skip-limit1-2"))
        == "grouped-match-aggregates"
    )
    assert (
        classify_primary_xfail_family(_scenario("match7-27"))
        == "optional-match-null-extension"
    )
    assert (
        classify_primary_xfail_family(_scenario("unwind1-12"))
        == "row-pipeline-read-forms"
    )
    assert (
        classify_primary_xfail_family(_scenario("expr-aggregation6-1-1"))
        == "expression-long-tail"
    )
    assert classify_primary_xfail_family(_scenario("create1-1")) == "write-clauses"
    assert classify_primary_xfail_family(_scenario("call1-1")) == "procedures-and-call"


def test_primary_family_counts_cover_all_xfails() -> None:
    summaries = build_primary_family_summaries(SCENARIOS)
    xfail_count = sum(1 for scenario in SCENARIOS if scenario.status == "xfail")

    assert sum(summary.xfail_count for summary in summaries) == xfail_count


def test_primary_family_counts_stable_for_priority_lanes() -> None:
    summaries = build_primary_family_summaries(SCENARIOS)
    by_lane = {summary.definition.lane_id: summary.xfail_count for summary in summaries}

    assert by_lane["row-pipeline-read-forms"] == 145
    assert by_lane["optional-match-null-extension"] == 57
    assert by_lane["grouped-match-aggregates"] == 25
    assert by_lane["expression-long-tail"] == 77


def test_priority_lane_summaries_include_tracker_refs_and_samples() -> None:
    summaries = build_priority_lane_summaries(SCENARIOS)
    grouped = next(
        summary
        for summary in summaries
        if summary.definition.lane_id == "grouped-match-aggregates"
    )

    assert grouped.definition.tracker_ref == "#45"
    assert (
        grouped.definition.tracker_url
        == "https://github.com/graphistry/tck-gfql/issues/45"
    )
    assert "return6-12" in grouped.sample_keys
    assert grouped.signal.startswith("read-only relationship aggregate xfails:")


def test_build_report_includes_gap_priority_sections() -> None:
    report = build_report()

    assert "Primary xfail families (disjoint heuristic):" in report
    assert "Priority candidate lanes:" in report
    assert "Supported-subset correctness / failfast audit" in report
    assert (
        "Direct Cypher string-only scenarios (status/tagged): "
        "984 (rows 829, errors 155)"
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
    assert "- success_matches_expected:" not in report
    assert "expr-comparison2-5-1 (expressions/comparison)" not in report
    assert "expr-comparison2-6-2 (expressions/comparison)" not in report
    assert "expr-graph3-5 (expressions/graph)" not in report
    assert "expr-quantifier7-3-1 (expressions/quantifier)" not in report
    assert "- success_wrong_rows:" in report
    assert "expr-comparison2-6-3 (expressions/comparison)" in report
    assert "expr-comparison2-6-4 (expressions/comparison)" in report
    # usecase-countingsubgraphmatches1-2 was promoted (pygraphistry #1903
    # trail semantics) and no longer appears as wrong-row debt.
    assert (
        "usecase-countingsubgraphmatches1-2 (useCases/countingSubgraphMatches)"
    ) not in report
    # with2-1 was promoted (tck-gfql#115); the current wrong-row bucket is
    # limited to branch-paired pygraphistry#1490 drift.
    assert "match5-8 (clauses/match)" not in report
    assert "with5-2 (clauses/with)" not in report
    assert "with2-1 (clauses/with)" not in report
    assert "- unexpected_success_expected_error:" not in report
    assert "expr-list1-6-4 (expressions/list)" not in report


def test_direct_cypher_nonvalidation_samples_are_stable_and_bounded() -> None:
    samples = report_module._direct_cypher_nonvalidation_samples(
        SCENARIOS, per_outcome=2
    )

    assert "success_matches_expected" not in samples
    assert samples["success_wrong_rows"] == [
        "expr-comparison2-6-3 (expressions/comparison)",
        "expr-comparison2-6-4 (expressions/comparison)",
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


def test_json_artifact_schema_and_counts(tmp_path) -> None:
    artifact = report_module.build_json_artifact(generated_at="2026-05-20T00:00:00Z")
    output_path = tmp_path / "cypher-tck-report.json"

    report_module.write_json_artifact(output_path, artifact)
    parsed = json.loads(output_path.read_text(encoding="utf-8"))

    assert parsed["schema_version"] == 1
    assert parsed["generated_at"] == "2026-05-20T00:00:00Z"
    assert parsed["source_refs"]["open_cypher_tck"]["commit"] == (
        "59edf2e1c17b845bf97c334ed06b2eb780950c13"
    )
    assert parsed["scenario_counts"]["total"] == len(SCENARIOS)
    assert parsed["gfql_counts"]["translated_supported"] > 0
    assert parsed["direct_cypher_counts"]["total_snapshot"] > 0
    assert parsed["expected_error_counts"]["direct_cypher_promoted_only"] == 142
    assert parsed["debt_keys"] == [
        {
            "key": key,
            "outcome": outcome,
            "reason": f"direct_cypher_nonvalidation:{outcome}",
        }
        for key, outcome in sorted(
            DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY.items()
        )
    ]


def test_json_artifact_is_stable_modulo_generated_at() -> None:
    first = report_module.build_json_artifact(generated_at="2026-05-20T00:00:00Z")
    second = report_module.build_json_artifact(generated_at="2026-05-20T00:00:01Z")

    first["generated_at"] = "<time>"
    second["generated_at"] = "<time>"

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_conformance_ref_pair_prefers_workflow_fields() -> None:
    ref_pair = report_module.build_conformance_ref_pair(
        env={
            "TCK_GFQL_REF": "feature/tck",
            "TCK_GFQL_SHA": "1" * 40,
            "PYGRAPHISTRY_REF": "feature/pygraphistry",
            "PYGRAPHISTRY_SHA": "2" * 40,
            "EXECUTION_PROFILE": "cpu-polars",
        }
    )

    assert ref_pair == {
        "tck_gfql_ref": "feature/tck",
        "tck_gfql_sha": "1" * 40,
        "pygraphistry_ref": "feature/pygraphistry",
        "pygraphistry_sha": "2" * 40,
        "execution_profile": "cpu-polars",
    }


def test_conformance_ref_pair_uses_github_fallbacks() -> None:
    ref_pair = report_module.build_conformance_ref_pair(
        env={
            "GITHUB_HEAD_REF": "pull-head",
            "GITHUB_REF_NAME": "main",
            "GITHUB_SHA": "3" * 40,
            "PYGRAPHISTRY_REF_INPUT": "master",
        }
    )

    assert ref_pair["tck_gfql_ref"] == "pull-head"
    assert ref_pair["tck_gfql_sha"] == "3" * 40
    assert ref_pair["pygraphistry_ref"] == "master"
    assert ref_pair["pygraphistry_sha"] == "unknown"
    assert ref_pair["execution_profile"] == "cpu-pandas"


def test_conformance_ref_pair_derives_gpu_profile() -> None:
    ref_pair = report_module.build_conformance_ref_pair(
        env={"TEST_CUDF": "1", "CUDA_VISIBLE_DEVICES": "0"}
    )

    assert ref_pair["execution_profile"] == "gpu-cudf"


def test_render_conformance_ref_pair_markdown_uses_standard_field_names() -> None:
    markdown = report_module.render_conformance_ref_pair_markdown(
        {
            "tck_gfql_ref": "main",
            "tck_gfql_sha": "a" * 40,
            "pygraphistry_ref": "master",
            "pygraphistry_sha": "b" * 40,
            "execution_profile": "cpu-pandas",
        }
    )

    assert markdown.startswith("### Conformance ref pair")
    for field in report_module.REF_PAIR_FIELDS:
        assert f"| `{field}` |" in markdown
