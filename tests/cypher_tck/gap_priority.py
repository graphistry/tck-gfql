from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from tests.cypher_tck.models import Scenario


SUPPORTED_SUBSET_AUDIT_KEYS: Tuple[str, ...] = (
    "return6-6",
    "return6-18",
    "return6-19",
    "return-orderby6-2",
)


@dataclass(frozen=True)
class PriorityLaneDefinition:
    lane_id: str
    title: str
    class_name: str
    priority: str
    user_value: str
    implementation_cost: str
    architecture_risk: str
    tracker_ref: str
    tracker_url: Optional[str]
    rationale: str
    curated_sample_keys: Tuple[str, ...] = ()


@dataclass(frozen=True)
class PriorityLaneSummary:
    definition: PriorityLaneDefinition
    signal: str
    sample_keys: Tuple[str, ...]


@dataclass(frozen=True)
class PrimaryFamilySummary:
    definition: PriorityLaneDefinition
    xfail_count: int
    sample_keys: Tuple[str, ...]
    top_reason: Optional[str]


PRIMARY_FAMILY_DEFINITIONS: Tuple[PriorityLaneDefinition, ...] = (
    PriorityLaneDefinition(
        lane_id="grouped-match-aggregates",
        title="Grouped aggregates over expanded MATCH",
        class_name="common-read-form",
        priority="P1",
        user_value="high",
        implementation_cost="medium",
        architecture_risk="medium-high",
        tracker_ref="TODO(meta-issue): multiplicity carrier PR2-PR4",
        tracker_url=None,
        rationale="Grouped counts and rollups over matched neighbors are common read-only analytics.",
        curated_sample_keys=(
            "return6-12",
            "with-skip-limit1-2",
            "with-skip-limit2-4",
            "with7-2",
        ),
    ),
    PriorityLaneDefinition(
        lane_id="row-pipeline-read-forms",
        title="Row-pipeline read forms",
        class_name="common-read-form",
        priority="P1",
        user_value="high",
        implementation_cost="medium",
        architecture_risk="medium",
        tracker_ref="TODO(candidate): row-pipeline read-form follow-up",
        tracker_url=None,
        rationale="WITH / ORDER BY / LIMIT / SKIP / UNWIND drive day-to-day query ergonomics.",
        curated_sample_keys=(
            "unwind1-12",
            "with4-6",
            "with6-2",
            "with6-3",
            "with6-4",
        ),
    ),
    PriorityLaneDefinition(
        lane_id="optional-match-null-extension",
        title="OPTIONAL MATCH / collect / null extension",
        class_name="common-read-form",
        priority="P2",
        user_value="medium-high",
        implementation_cost="high",
        architecture_risk="high",
        tracker_ref="TODO(candidate): optional/null-extension follow-up",
        tracker_url=None,
        rationale="OPTIONAL MATCH and null extension are common, but the carrier/null semantics are broader.",
        curated_sample_keys=(
            "match7-29",
            "match7-30",
            "match7-31",
            "return-orderby2-12",
        ),
    ),
    PriorityLaneDefinition(
        lane_id="expression-long-tail",
        title="Expression long tail",
        class_name="big-swath",
        priority="P3",
        user_value="mixed",
        implementation_cost="high",
        architecture_risk="high",
        tracker_ref="TODO(backlog): expression long-tail tranche selection",
        tracker_url=None,
        rationale="The expression backlog is large, but the raw count mixes common cases with low-ROI corners.",
        curated_sample_keys=("expr-aggregation2-7",),
    ),
    PriorityLaneDefinition(
        lane_id="write-clauses",
        title="Write clauses",
        class_name="big-swath",
        priority="P3",
        user_value="product-dependent",
        implementation_cost="high",
        architecture_risk="high",
        tracker_ref="TODO(backlog): write-clause roadmap",
        tracker_url=None,
        rationale="Large TCK coverage lift, but weaker fit for the current local read-only product lane.",
        curated_sample_keys=("create1-1",),
    ),
    PriorityLaneDefinition(
        lane_id="procedures-and-call",
        title="Procedures / CALL",
        class_name="niche-tck",
        priority="P4",
        user_value="low",
        implementation_cost="high",
        architecture_risk="high",
        tracker_ref="TODO(backlog): procedure registry investigation",
        tracker_url=None,
        rationale="Specialized semantics with their own registry and YIELD surface.",
        curated_sample_keys=("call1-1",),
    ),
    PriorityLaneDefinition(
        lane_id="other-read-gaps",
        title="Other read-only gaps",
        class_name="big-swath",
        priority="P3",
        user_value="mixed",
        implementation_cost="medium",
        architecture_risk="medium",
        tracker_ref="TODO(backlog): remaining read-only triage",
        tracker_url=None,
        rationale="Residual read-only scenarios that do not fit the main tracked workstreams yet.",
    ),
)

_PRIMARY_FAMILY_BY_ID = {lane.lane_id: lane for lane in PRIMARY_FAMILY_DEFINITIONS}


def _cypher_upper(scenario: Scenario) -> str:
    return scenario.cypher.upper()


def _cypher_lower(scenario: Scenario) -> str:
    return scenario.cypher.lower()


def _has_write_clause(scenario: Scenario) -> bool:
    text = _cypher_upper(scenario)
    return any(
        token in text for token in ("CREATE ", "MERGE ", " SET ", "DELETE ", "REMOVE ")
    )


def _has_call_clause(scenario: Scenario) -> bool:
    return "CALL " in _cypher_upper(scenario)


def _has_optional_match(scenario: Scenario) -> bool:
    return "OPTIONAL MATCH" in _cypher_upper(scenario)


def _has_collect(scenario: Scenario) -> bool:
    return "collect(" in _cypher_lower(scenario)


def _has_row_pipeline_clause(scenario: Scenario) -> bool:
    text = _cypher_upper(scenario)
    return any(token in text for token in ("WITH ", "ORDER BY", "SKIP ", "LIMIT ", "UNWIND "))


def _is_expression_tail(scenario: Scenario) -> bool:
    return "expr" in scenario.tags or "target-expr-dsl" in scenario.tags


def _is_read_only(scenario: Scenario) -> bool:
    return not _has_write_clause(scenario) and not _has_call_clause(scenario)


def _is_grouped_match_aggregate(scenario: Scenario) -> bool:
    text_upper = _cypher_upper(scenario)
    text_lower = _cypher_lower(scenario)
    if scenario.status != "xfail" or not _is_read_only(scenario):
        return False
    if _has_optional_match(scenario):
        return False
    if "MATCH" not in text_upper:
        return False
    if "->" not in scenario.cypher and "<-" not in scenario.cypher:
        return False
    if _has_collect(scenario):
        return False
    return any(fn in text_lower for fn in ("count(", "sum(", "avg("))


def classify_primary_xfail_family(scenario: Scenario) -> str:
    if scenario.status != "xfail":
        raise ValueError(f"expected xfail scenario, got {scenario.key}={scenario.status}")
    if _has_write_clause(scenario):
        return "write-clauses"
    if _has_call_clause(scenario):
        return "procedures-and-call"
    if _is_grouped_match_aggregate(scenario):
        return "grouped-match-aggregates"
    if _has_optional_match(scenario):
        return "optional-match-null-extension"
    if _has_row_pipeline_clause(scenario):
        return "row-pipeline-read-forms"
    if _is_expression_tail(scenario):
        return "expression-long-tail"
    return "other-read-gaps"


def _sorted_xfails_for_family(
    scenarios: Sequence[Scenario], family_id: str
) -> Tuple[Scenario, ...]:
    return tuple(
        sorted(
            (
                scenario
                for scenario in scenarios
                if scenario.status == "xfail"
                and classify_primary_xfail_family(scenario) == family_id
            ),
            key=lambda scenario: scenario.key,
        )
    )


def _sample_keys(
    scenarios: Sequence[Scenario],
    curated_keys: Tuple[str, ...],
    limit: int = 6,
) -> Tuple[str, ...]:
    available = {scenario.key for scenario in scenarios}
    samples = [key for key in curated_keys if key in available]
    if samples:
        return tuple(samples[:limit])
    if len(samples) >= limit:
        return tuple(samples[:limit])
    for key in sorted(available):
        if key not in samples:
            samples.append(key)
        if len(samples) >= limit:
            break
    return tuple(samples)


def _top_reason(scenarios: Sequence[Scenario]) -> Optional[str]:
    counts = Counter(scenario.reason for scenario in scenarios if scenario.reason)
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def build_primary_family_summaries(
    scenarios: Sequence[Scenario],
) -> Tuple[PrimaryFamilySummary, ...]:
    summaries = []
    for definition in PRIMARY_FAMILY_DEFINITIONS:
        matches = _sorted_xfails_for_family(scenarios, definition.lane_id)
        summaries.append(
            PrimaryFamilySummary(
                definition=definition,
                xfail_count=len(matches),
                sample_keys=_sample_keys(matches, definition.curated_sample_keys),
                top_reason=_top_reason(matches),
            )
        )
    return tuple(sorted(summaries, key=lambda summary: summary.xfail_count, reverse=True))


def _count_xfails(
    scenarios: Sequence[Scenario], predicate
) -> int:
    return sum(1 for scenario in scenarios if scenario.status == "xfail" and predicate(scenario))


def _sample_keys_by_predicate(
    scenarios: Sequence[Scenario],
    predicate,
    curated_keys: Tuple[str, ...],
) -> Tuple[str, ...]:
    matches = tuple(
        sorted(
            (
                scenario
                for scenario in scenarios
                if scenario.status == "xfail" and predicate(scenario)
            ),
            key=lambda scenario: scenario.key,
        )
    )
    return _sample_keys(matches, curated_keys)


def build_priority_lane_summaries(
    scenarios: Sequence[Scenario],
) -> Tuple[PriorityLaneSummary, ...]:
    xfail_count = sum(1 for scenario in scenarios if scenario.status == "xfail")
    summaries = [
        PriorityLaneSummary(
            definition=PriorityLaneDefinition(
                lane_id="supported-subset-audit",
                title="Supported-subset correctness / failfast audit",
                class_name="supported-subset-audit",
                priority="P0",
                user_value="highest",
                implementation_cost="medium",
                architecture_risk="medium",
                tracker_ref="standing-gate",
                tracker_url=None,
                rationale="Keep adjacent scenarios honest even when they are already supported.",
                curated_sample_keys=SUPPORTED_SUBSET_AUDIT_KEYS,
            ),
            signal=(
                f"adjacent supported scenarios under watch: "
                f"{sum(1 for scenario in scenarios if scenario.key in SUPPORTED_SUBSET_AUDIT_KEYS)}"
            ),
            sample_keys=tuple(SUPPORTED_SUBSET_AUDIT_KEYS),
        ),
        PriorityLaneSummary(
            definition=_PRIMARY_FAMILY_BY_ID["grouped-match-aggregates"],
            signal=(
                f"read-only relationship aggregate xfails: "
                f"{_count_xfails(scenarios, _is_grouped_match_aggregate)}"
            ),
            sample_keys=_sample_keys_by_predicate(
                scenarios,
                _is_grouped_match_aggregate,
                _PRIMARY_FAMILY_BY_ID["grouped-match-aggregates"].curated_sample_keys,
            ),
        ),
        PriorityLaneSummary(
            definition=_PRIMARY_FAMILY_BY_ID["row-pipeline-read-forms"],
            signal=(
                f"primary-family xfails: "
                f"{next(summary.xfail_count for summary in build_primary_family_summaries(scenarios) if summary.definition.lane_id == 'row-pipeline-read-forms')}; "
                f"with-clause: {_count_xfails(scenarios, lambda scenario: 'WITH ' in _cypher_upper(scenario))}; "
                f"unwind-clause: {_count_xfails(scenarios, lambda scenario: 'UNWIND ' in _cypher_upper(scenario))}"
            ),
            sample_keys=next(
                summary.sample_keys
                for summary in build_primary_family_summaries(scenarios)
                if summary.definition.lane_id == "row-pipeline-read-forms"
            ),
        ),
        PriorityLaneSummary(
            definition=_PRIMARY_FAMILY_BY_ID["optional-match-null-extension"],
            signal=(
                f"optional-match: {_count_xfails(scenarios, _has_optional_match)}; "
                f"collect: {_count_xfails(scenarios, _has_collect)}"
            ),
            sample_keys=_sample_keys_by_predicate(
                scenarios,
                lambda scenario: _has_optional_match(scenario) or _has_collect(scenario),
                _PRIMARY_FAMILY_BY_ID["optional-match-null-extension"].curated_sample_keys,
            ),
        ),
        PriorityLaneSummary(
            definition=_PRIMARY_FAMILY_BY_ID["expression-long-tail"],
            signal=(
                f"expr-tag: {_count_xfails(scenarios, lambda scenario: 'expr' in scenario.tags)}; "
                f"target-expr-dsl: {_count_xfails(scenarios, lambda scenario: 'target-expr-dsl' in scenario.tags)}"
            ),
            sample_keys=next(
                summary.sample_keys
                for summary in build_primary_family_summaries(scenarios)
                if summary.definition.lane_id == "expression-long-tail"
            ),
        ),
        PriorityLaneSummary(
            definition=_PRIMARY_FAMILY_BY_ID["write-clauses"],
            signal=f"write-clause xfails: {_count_xfails(scenarios, _has_write_clause)}",
            sample_keys=next(
                summary.sample_keys
                for summary in build_primary_family_summaries(scenarios)
                if summary.definition.lane_id == "write-clauses"
            ),
        ),
        PriorityLaneSummary(
            definition=_PRIMARY_FAMILY_BY_ID["procedures-and-call"],
            signal=f"CALL xfails: {_count_xfails(scenarios, _has_call_clause)}",
            sample_keys=next(
                summary.sample_keys
                for summary in build_primary_family_summaries(scenarios)
                if summary.definition.lane_id == "procedures-and-call"
            ),
        ),
    ]
    if xfail_count == 0:
        return tuple()
    return tuple(summaries)
