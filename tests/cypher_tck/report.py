from __future__ import annotations

import os
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple, cast


from tests.cypher_tck.direct_cypher_support import (
    DIRECT_CYPHER_OVERLAP_KEYS,
    DIRECT_CYPHER_PROMOTION_ERROR_KEYS,
    DIRECT_CYPHER_PROMOTION_KEYS,
    DIRECT_CYPHER_PROMOTION_ROW_KEYS,
)
from tests.cypher_tck.gap_priority import (
    build_primary_family_summaries,
    build_priority_lane_summaries,
)
from tests.cypher_tck.gfql_plan import PlanStep
from tests.cypher_tck.phase_support import PHASE1_EXECUTOR_PURE_KEYS
from tests.cypher_tck.scenarios import SCENARIOS


def _feature_parts(feature_path: str) -> Tuple[str, str]:
    parts = feature_path.split("/")
    if "features" in parts:
        idx = parts.index("features")
        group = parts[idx + 1] if idx + 1 < len(parts) else "unknown"
        area = parts[idx + 2] if idx + 2 < len(parts) else "unknown"
        return group, f"{group}/{area}"
    return "unknown", "unknown"


def _percent(value: int, total: int) -> str:
    if total == 0:
        return "n/a"
    return f"{(value / total) * 100:.1f}%"


def _table_rows(
    counts: Dict[str, Counter], top_n: Optional[int] = None
) -> List[str]:
    items = sorted(
        counts.items(),
        key=lambda item: item[1].get("total", 0),
        reverse=True,
    )
    if top_n is not None:
        items = items[:top_n]
    rows = []
    for name, counter in items:
        rows.append(
            f"| {name} | {counter.get('total', 0)} | "
            f"{counter.get('supported', 0)} | {counter.get('xfail', 0)} | "
            f"{counter.get('skip', 0)} |"
        )
    return rows


def _is_executable_plan(gfql: object) -> bool:
    if not isinstance(gfql, tuple) or not gfql:
        return False
    if not all(isinstance(step, PlanStep) for step in gfql):
        return False
    return not any(step.op in {"raw", "invalid"} for step in gfql)




def _is_cypher_string_supported_scenario(scenario: object) -> bool:
    status = getattr(scenario, "status", None)
    tags = getattr(scenario, "tags", ())
    return status == "supported" and "cypher-string" in tags

def _is_pure_supported_scenario(scenario: object) -> bool:
    status = getattr(scenario, "status", None)
    gfql = getattr(scenario, "gfql", None)
    key = getattr(scenario, "key", "")
    if _is_cypher_string_supported_scenario(scenario):
        return True
    if status != "supported" or gfql is None:
        return False
    if _is_executable_plan(gfql):
        return key in PHASE1_EXECUTOR_PURE_KEYS
    return True


def _impure_bucket(scenario: object) -> str:
    gfql = getattr(scenario, "gfql", None)
    tags = getattr(scenario, "tags", ())
    if "cypher-string" in tags:
        return "cypher-string"
    if not _is_executable_plan(gfql):
        return "non-plan-supported"
    plan = cast(Tuple[PlanStep, ...], gfql)
    ops = [step.op for step in plan]
    if "unwind" in ops:
        return "plan-unwind"
    if "group_by" in ops:
        return "plan-group-by"
    if "where" in ops:
        return "plan-where"
    if "with" in ops:
        return "plan-with"
    if "select" in ops:
        return "plan-select"
    if "order_by" in ops:
        return "plan-order-by"
    return "plan-other"


def build_report() -> str:
    total = len(SCENARIOS)
    status_counts = Counter(scenario.status for scenario in SCENARIOS)
    gfql_defined = sum(1 for scenario in SCENARIOS if scenario.gfql is not None)
    missing_gfql = total - gfql_defined
    supported_defined = sum(
        1
        for scenario in SCENARIOS
        if scenario.status == "supported"
        and scenario.gfql is not None
        and not _is_cypher_string_supported_scenario(scenario)
    )
    cypher_string_supported = sum(
        1
        for scenario in SCENARIOS
        if _is_cypher_string_supported_scenario(scenario)
    )
    cypher_string_supported_rows = sum(
        1
        for scenario in SCENARIOS
        if _is_cypher_string_supported_scenario(scenario)
        and getattr(getattr(scenario, "expected", None), "rows", None) is not None
    )
    cypher_string_supported_errors = sum(
        1
        for scenario in SCENARIOS
        if _is_cypher_string_supported_scenario(scenario)
        and getattr(getattr(scenario, "expected", None), "rows", None) is None
    )
    translated_xfail = sum(
        1
        for scenario in SCENARIOS
        if scenario.status == "xfail" and scenario.gfql is not None
    )
    translated_skip = sum(
        1
        for scenario in SCENARIOS
        if scenario.status == "skip" and scenario.gfql is not None
    )
    supported_missing = sum(
        1
        for scenario in SCENARIOS
        if scenario.status == "supported"
        and scenario.gfql is None
        and not _is_cypher_string_supported_scenario(scenario)
    )

    supported_count = status_counts.get("supported", 0)
    xfail_count = status_counts.get("xfail", 0)
    skip_count = status_counts.get("skip", 0)
    other_count = total - supported_count - xfail_count - skip_count
    supported_pure = sum(1 for scenario in SCENARIOS if _is_pure_supported_scenario(scenario))
    supported_impure = supported_count - supported_pure

    group_counts: Dict[str, Counter] = defaultdict(Counter)
    area_counts: Dict[str, Counter] = defaultdict(Counter)
    xfail_tags: Counter[str] = Counter()
    impure_buckets: Counter[str] = Counter()

    for scenario in SCENARIOS:
        group, area = _feature_parts(scenario.feature_path)
        for bucket in (group_counts[group], area_counts[area]):
            bucket["total"] += 1
            bucket[scenario.status] += 1
        if scenario.status == "xfail":
            xfail_tags.update(scenario.tags)
        if scenario.status == "supported" and not _is_pure_supported_scenario(scenario):
            impure_buckets.update([_impure_bucket(scenario)])

    lines = [
        "GFQL conformance report (tck-gfql)",
        "",
        f"Scenarios represented (ported): {total}",
        f"GFQL translated (non-None): {gfql_defined} ({_percent(gfql_defined, total)})",
        f"Translated + expected pass (supported via translated GFQL): {supported_defined}",
        f"Promoted via direct Cypher string only (status/tagged): {cypher_string_supported} "
        f"(rows {cypher_string_supported_rows}, errors {cypher_string_supported_errors})",
        f"GFQL missing: {missing_gfql} ({_percent(missing_gfql, total)})",
        f"Direct Cypher overlap on translated-supported scenarios: {len(DIRECT_CYPHER_OVERLAP_KEYS)} / {supported_defined} "
        f"({_percent(len(DIRECT_CYPHER_OVERLAP_KEYS), supported_defined)})",
        f"Direct Cypher promoted-only snapshot: {len(DIRECT_CYPHER_PROMOTION_KEYS)} "
        f"(rows {len(DIRECT_CYPHER_PROMOTION_ROW_KEYS)}, errors {len(DIRECT_CYPHER_PROMOTION_ERROR_KEYS)})",
        f"Direct Cypher total snapshot across represented scenarios: "
        f"{len(DIRECT_CYPHER_OVERLAP_KEYS) + len(DIRECT_CYPHER_PROMOTION_KEYS)} / {total} "
        f"({_percent(len(DIRECT_CYPHER_OVERLAP_KEYS) + len(DIRECT_CYPHER_PROMOTION_KEYS), total)})",
        f"Translated but xfail: {translated_xfail}",
        f"Translated but skip: {translated_skip}",
        f"Supported but missing GFQL: {supported_missing}",
        f"Status counts: supported {supported_count}, "
        f"xfail {xfail_count}, "
        f"skip {skip_count}, "
        f"other {other_count}",
        f"Purity split: supported_semantic {supported_count}, "
        f"supported_pure {supported_pure}, "
        f"supported_impure {supported_impure}",
        f"Pure share (of supported): {_percent(supported_pure, supported_count)}",
        "",
        "By feature group:",
        "| group | total | supported | xfail | skip |",
        "|---|---:|---:|---:|---:|",
    ]

    lines.extend(_table_rows(group_counts))

    lines.extend(
        [
            "",
            "Top feature areas (by scenario count):",
            "| feature | total | supported | xfail | skip |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    lines.extend(_table_rows(area_counts, top_n=10))

    lines.append("")
    lines.append("Top xfail tags:")
    if xfail_tags:
        for tag, count in xfail_tags.most_common(10):
            lines.append(f"- {tag}: {count}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Top impure-supported buckets:")
    if impure_buckets:
        for tag, count in impure_buckets.most_common(10):
            lines.append(f"- {tag}: {count}")
    else:
        lines.append("- none")

    priority_lanes = build_priority_lane_summaries(SCENARIOS)
    primary_families = build_primary_family_summaries(SCENARIOS)

    lines.extend(
        [
            "",
            "Primary xfail families (disjoint heuristic):",
            "| family | xfail | priority | class | top reason | tracker |",
            "|---|---:|---|---|---|---|",
        ]
    )
    for family in primary_families:
        lines.append(
            f"| {family.definition.title} | {family.xfail_count} | "
            f"{family.definition.priority} | {family.definition.class_name} | "
            f"{family.top_reason or 'n/a'} | {family.definition.tracker_ref} |"
        )

    lines.extend(
        [
            "",
            "Priority candidate lanes:",
            "| lane | class | priority | signal | user value | cost | architecture risk | tracker |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for lane in priority_lanes:
        lines.append(
            f"| {lane.definition.title} | {lane.definition.class_name} | "
            f"{lane.definition.priority} | {lane.signal} | {lane.definition.user_value} | "
            f"{lane.definition.implementation_cost} | {lane.definition.architecture_risk} | "
            f"{lane.definition.tracker_ref} |"
        )

    lines.append("")
    lines.append("Representative tracked scenarios:")
    if priority_lanes:
        for lane in priority_lanes:
            lines.append(
                f"- {lane.definition.title} [{lane.definition.tracker_ref}]: "
                + (", ".join(lane.sample_keys) if lane.sample_keys else "none")
            )
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def main() -> None:
    report = build_report()
    print(report)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(report)


if __name__ == "__main__":
    main()
