from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, cast


from tests.cypher_tck.direct_cypher_xfail_contract import (
    DIRECT_CYPHER_NONVALIDATION_XFAIL_COUNTS,
    DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY,
)
from tests.cypher_tck.direct_cypher_support import (
    DIRECT_CYPHER_OVERLAP_KEYS,
    DIRECT_CYPHER_PROMOTION_ERROR_KEYS,
    DIRECT_CYPHER_PROMOTION_ROW_KEYS,
)
from tests.cypher_tck.gap_priority import (
    PRIMARY_FAMILY_DEFINITIONS,
    build_primary_family_summaries,
    build_priority_lane_summaries,
)
from tests.cypher_tck.gfql_plan import PlanStep
from tests.cypher_tck.phase_support import PHASE1_EXECUTOR_PURE_KEYS
from tests.cypher_tck.scenarios import SCENARIOS

SCHEMA_VERSION = 1
DEFAULT_JSON_OUTPUT = Path("build/cypher-tck-report.json")
OPEN_CYPHER_TCK_SOURCE_COMMIT = "59edf2e1c17b845bf97c334ed06b2eb780950c13"

# JSON artifact contract:
# - `schema_version` starts at 1 and must be bumped for incompatible shape changes.
# - Key ordering and list ordering are stable so downstream manifest, snapshot-delta,
#   and handoff tooling can diff artifacts. Only `generated_at` is time-varying.
# - Counts preserve the existing console report semantics; do not reinterpret scenario
#   status or direct-Cypher support categories without a schema bump.


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


def _table_rows(counts: Dict[str, Counter], top_n: Optional[int] = None) -> List[str]:
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


def _live_direct_cypher_snapshot_sets(
    scenarios: Sequence[object],
) -> Tuple[set[str], set[str], set[str]]:
    represented_keys = {getattr(scenario, "key", "") for scenario in scenarios}
    translated_supported_keys = {
        getattr(scenario, "key", "")
        for scenario in scenarios
        if getattr(scenario, "status", None) == "supported"
        and getattr(scenario, "gfql", None) is not None
        and not _is_cypher_string_supported_scenario(scenario)
    }
    overlap_keys = DIRECT_CYPHER_OVERLAP_KEYS & translated_supported_keys
    promotion_row_keys = (
        DIRECT_CYPHER_PROMOTION_ROW_KEYS & represented_keys
    ) - translated_supported_keys
    promotion_error_keys = (
        DIRECT_CYPHER_PROMOTION_ERROR_KEYS & represented_keys
    ) - translated_supported_keys
    return overlap_keys, promotion_row_keys, promotion_error_keys


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _report_metrics(scenarios: Sequence[object]) -> Dict[str, Any]:
    total = len(scenarios)
    status_counts = Counter(getattr(scenario, "status", None) for scenario in scenarios)
    gfql_defined = sum(
        1 for scenario in scenarios if getattr(scenario, "gfql", None) is not None
    )
    missing_gfql = total - gfql_defined
    supported_defined = sum(
        1
        for scenario in scenarios
        if getattr(scenario, "status", None) == "supported"
        and getattr(scenario, "gfql", None) is not None
        and not _is_cypher_string_supported_scenario(scenario)
    )
    cypher_string_supported = sum(
        1 for scenario in scenarios if _is_cypher_string_supported_scenario(scenario)
    )
    cypher_string_supported_rows = sum(
        1
        for scenario in scenarios
        if _is_cypher_string_supported_scenario(scenario)
        and "cypher-string-error" not in getattr(scenario, "tags", ())
    )
    cypher_string_supported_errors = sum(
        1
        for scenario in scenarios
        if _is_cypher_string_supported_scenario(scenario)
        and "cypher-string-error" in getattr(scenario, "tags", ())
    )
    translated_xfail = sum(
        1
        for scenario in scenarios
        if getattr(scenario, "status", None) == "xfail"
        and getattr(scenario, "gfql", None) is not None
    )
    translated_skip = sum(
        1
        for scenario in scenarios
        if getattr(scenario, "status", None) == "skip"
        and getattr(scenario, "gfql", None) is not None
    )
    supported_missing = sum(
        1
        for scenario in scenarios
        if getattr(scenario, "status", None) == "supported"
        and getattr(scenario, "gfql", None) is None
        and not _is_cypher_string_supported_scenario(scenario)
    )

    supported_count = status_counts.get("supported", 0)
    xfail_count = status_counts.get("xfail", 0)
    skip_count = status_counts.get("skip", 0)
    other_count = total - supported_count - xfail_count - skip_count
    supported_pure = sum(
        1 for scenario in scenarios if _is_pure_supported_scenario(scenario)
    )
    supported_impure = supported_count - supported_pure
    direct_cypher_validation_safe_xfails = xfail_count - len(
        DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY
    )
    (
        direct_cypher_overlap_keys,
        direct_cypher_promotion_row_keys,
        direct_cypher_promotion_error_keys,
    ) = _live_direct_cypher_snapshot_sets(scenarios)
    direct_cypher_promotion_keys = (
        direct_cypher_promotion_row_keys | direct_cypher_promotion_error_keys
    )

    group_counts: Dict[str, Counter] = defaultdict(Counter)
    area_counts: Dict[str, Counter] = defaultdict(Counter)
    xfail_tags: Counter[str] = Counter()
    impure_buckets: Counter[str] = Counter()

    for scenario in scenarios:
        group, area = _feature_parts(getattr(scenario, "feature_path", ""))
        for bucket in (group_counts[group], area_counts[area]):
            bucket["total"] += 1
            bucket[getattr(scenario, "status", None)] += 1
        if getattr(scenario, "status", None) == "xfail":
            xfail_tags.update(getattr(scenario, "tags", ()))
        if getattr(
            scenario, "status", None
        ) == "supported" and not _is_pure_supported_scenario(scenario):
            impure_buckets.update([_impure_bucket(scenario)])

    return {
        "total": total,
        "status_counts": status_counts,
        "gfql_defined": gfql_defined,
        "missing_gfql": missing_gfql,
        "supported_defined": supported_defined,
        "cypher_string_supported": cypher_string_supported,
        "cypher_string_supported_rows": cypher_string_supported_rows,
        "cypher_string_supported_errors": cypher_string_supported_errors,
        "translated_xfail": translated_xfail,
        "translated_skip": translated_skip,
        "supported_missing": supported_missing,
        "supported_count": supported_count,
        "xfail_count": xfail_count,
        "skip_count": skip_count,
        "other_count": other_count,
        "supported_pure": supported_pure,
        "supported_impure": supported_impure,
        "direct_cypher_validation_safe_xfails": direct_cypher_validation_safe_xfails,
        "direct_cypher_overlap_keys": direct_cypher_overlap_keys,
        "direct_cypher_promotion_row_keys": direct_cypher_promotion_row_keys,
        "direct_cypher_promotion_error_keys": direct_cypher_promotion_error_keys,
        "direct_cypher_promotion_keys": direct_cypher_promotion_keys,
        "group_counts": group_counts,
        "area_counts": area_counts,
        "xfail_tags": xfail_tags,
        "impure_buckets": impure_buckets,
    }


def _scenario_inventory_revision(scenarios: Sequence[object]) -> str:
    payload = {
        "direct_cypher_nonvalidation_outcomes": sorted(
            DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY.items()
        ),
        "direct_cypher_overlap_keys": sorted(DIRECT_CYPHER_OVERLAP_KEYS),
        "direct_cypher_promotion_error_keys": sorted(
            DIRECT_CYPHER_PROMOTION_ERROR_KEYS
        ),
        "direct_cypher_promotion_row_keys": sorted(DIRECT_CYPHER_PROMOTION_ROW_KEYS),
        "scenarios": [
            {
                "feature_path": getattr(scenario, "feature_path", ""),
                "gfql_defined": getattr(scenario, "gfql", None) is not None,
                "key": getattr(scenario, "key", ""),
                "scenario": getattr(scenario, "scenario", ""),
                "status": getattr(scenario, "status", None),
                "tags": sorted(getattr(scenario, "tags", ())),
            }
            for scenario in sorted(scenarios, key=lambda item: getattr(item, "key", ""))
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _runtime_profile() -> Optional[Dict[str, Any]]:
    profile: Dict[str, Any] = {}
    try:
        import graphistry

        version = getattr(graphistry, "__version__", None)
        if version:
            profile["pygraphistry_version"] = str(version)
    except Exception:
        pass
    if os.environ.get("PYGRAPHISTRY_REF"):
        profile["pygraphistry_ref"] = os.environ["PYGRAPHISTRY_REF"]
    if os.environ.get("TEST_CUDF"):
        profile["test_cudf"] = os.environ["TEST_CUDF"]
    if os.environ.get("CUDA_VISIBLE_DEVICES"):
        profile["cuda_visible_devices"] = os.environ["CUDA_VISIBLE_DEVICES"]
    return profile or None


def build_json_artifact(*, generated_at: Optional[str] = None) -> Dict[str, Any]:
    metrics = _report_metrics(SCENARIOS)
    total = metrics["total"]
    supported_defined = metrics["supported_defined"]
    direct_cypher_overlap_keys = metrics["direct_cypher_overlap_keys"]
    direct_cypher_promotion_row_keys = metrics["direct_cypher_promotion_row_keys"]
    direct_cypher_promotion_error_keys = metrics["direct_cypher_promotion_error_keys"]
    direct_cypher_promotion_keys = metrics["direct_cypher_promotion_keys"]
    artifact: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at or _utc_now_iso(),
        "source_refs": {
            "open_cypher_tck": {
                "repo": "https://github.com/opencypher/openCypher",
                "path": "tck",
                "commit": OPEN_CYPHER_TCK_SOURCE_COMMIT,
            },
            "local_fixtures": {
                "module": "tests.cypher_tck.scenarios",
                "scenario_inventory_sha256": _scenario_inventory_revision(SCENARIOS),
            },
        },
        "scenario_counts": {
            "total": total,
            "supported": metrics["supported_count"],
            "xfail": metrics["xfail_count"],
            "skip": metrics["skip_count"],
            "other": metrics["other_count"],
            "gfql_defined": metrics["gfql_defined"],
            "gfql_missing": metrics["missing_gfql"],
        },
        "gfql_counts": {
            "translated_non_none": metrics["gfql_defined"],
            "translated_supported": supported_defined,
            "translated_xfail": metrics["translated_xfail"],
            "translated_skip": metrics["translated_skip"],
            "supported_missing_gfql": metrics["supported_missing"],
            "supported_pure": metrics["supported_pure"],
            "supported_impure": metrics["supported_impure"],
        },
        "direct_cypher_counts": {
            "overlap_translated_supported": len(direct_cypher_overlap_keys),
            "translated_supported_total": supported_defined,
            "promoted_only": len(direct_cypher_promotion_keys),
            "promoted_only_rows": len(direct_cypher_promotion_row_keys),
            "promoted_only_expected_errors": len(direct_cypher_promotion_error_keys),
            "total_snapshot": len(direct_cypher_overlap_keys)
            + len(direct_cypher_promotion_keys),
            "represented_total": total,
        },
        "expected_error_counts": {
            "cypher_string_supported": metrics["cypher_string_supported_errors"],
            "direct_cypher_promoted_only": len(direct_cypher_promotion_error_keys),
            "direct_cypher_nonvalidation_debt": len(
                DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY
            ),
            "direct_cypher_nonvalidation_by_outcome": dict(
                sorted(DIRECT_CYPHER_NONVALIDATION_XFAIL_COUNTS.items())
            ),
        },
        "debt_keys": [
            {
                "key": key,
                "outcome": outcome,
                "reason": f"direct_cypher_nonvalidation:{outcome}",
            }
            for key, outcome in sorted(
                DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY.items()
            )
        ],
    }
    runtime_profile = _runtime_profile()
    if runtime_profile:
        artifact["runtime_profile"] = runtime_profile
    return artifact


def write_json_artifact(path: Path, artifact: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _direct_cypher_nonvalidation_samples(
    scenarios: Sequence[object],
    *,
    per_outcome: int = 8,
) -> Dict[str, List[str]]:
    scenarios_by_key = {
        getattr(scenario, "key", ""): scenario for scenario in scenarios
    }
    samples: Dict[str, List[str]] = {}
    for outcome in sorted(DIRECT_CYPHER_NONVALIDATION_XFAIL_COUNTS):
        keys = sorted(
            key
            for key, key_outcome in DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY.items()
            if key_outcome == outcome
        )
        rendered: List[str] = []
        for key in keys[:per_outcome]:
            scenario = scenarios_by_key.get(key)
            if scenario is None:
                rendered.append(f"{key} (missing scenario)")
                continue
            _, area = _feature_parts(getattr(scenario, "feature_path", ""))
            rendered.append(f"{key} ({area})")
        remaining = len(keys) - len(rendered)
        if remaining > 0:
            rendered.append(f"... {remaining} more")
        samples[outcome] = rendered
    return samples


def build_report() -> str:
    metrics = _report_metrics(SCENARIOS)
    total = metrics["total"]
    gfql_defined = metrics["gfql_defined"]
    missing_gfql = metrics["missing_gfql"]
    supported_defined = metrics["supported_defined"]
    cypher_string_supported = metrics["cypher_string_supported"]
    cypher_string_supported_rows = metrics["cypher_string_supported_rows"]
    cypher_string_supported_errors = metrics["cypher_string_supported_errors"]
    translated_xfail = metrics["translated_xfail"]
    translated_skip = metrics["translated_skip"]
    supported_missing = metrics["supported_missing"]
    supported_count = metrics["supported_count"]
    xfail_count = metrics["xfail_count"]
    skip_count = metrics["skip_count"]
    other_count = metrics["other_count"]
    supported_pure = metrics["supported_pure"]
    supported_impure = metrics["supported_impure"]
    direct_cypher_validation_safe_xfails = metrics[
        "direct_cypher_validation_safe_xfails"
    ]
    direct_cypher_overlap_keys = metrics["direct_cypher_overlap_keys"]
    direct_cypher_promotion_row_keys = metrics["direct_cypher_promotion_row_keys"]
    direct_cypher_promotion_error_keys = metrics["direct_cypher_promotion_error_keys"]
    direct_cypher_promotion_keys = metrics["direct_cypher_promotion_keys"]
    group_counts = metrics["group_counts"]
    area_counts = metrics["area_counts"]
    xfail_tags = metrics["xfail_tags"]
    impure_buckets = metrics["impure_buckets"]

    lines = [
        "GFQL conformance report (tck-gfql)",
        "",
        f"Scenarios represented (ported): {total}",
        f"GFQL translated (non-None): {gfql_defined} ({_percent(gfql_defined, total)})",
        f"Translated + expected pass (supported via translated GFQL): {supported_defined}",
        f"Promoted via direct Cypher string only (status/tagged): {cypher_string_supported} "
        f"(rows {cypher_string_supported_rows}, errors {cypher_string_supported_errors})",
        f"GFQL missing: {missing_gfql} ({_percent(missing_gfql, total)})",
        f"Direct Cypher overlap on translated-supported scenarios: {len(direct_cypher_overlap_keys)} / {supported_defined} "
        f"({_percent(len(direct_cypher_overlap_keys), supported_defined)})",
        f"Direct Cypher promoted-only snapshot: {len(direct_cypher_promotion_keys)} "
        f"(rows {len(direct_cypher_promotion_row_keys)}, errors {len(direct_cypher_promotion_error_keys)})",
        f"Direct Cypher total snapshot across represented scenarios: "
        f"{len(direct_cypher_overlap_keys) + len(direct_cypher_promotion_keys)} / {total} "
        f"({_percent(len(direct_cypher_overlap_keys) + len(direct_cypher_promotion_keys), total)})",
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

    lines.extend(
        [
            "",
            "Direct local Cypher xfail contract:",
            f"- validation-safe xfails: {direct_cypher_validation_safe_xfails} "
            f"({_percent(direct_cypher_validation_safe_xfails, xfail_count)})",
            f"- tracked non-validation debt: {len(DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY)} "
            f"({_percent(len(DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY), xfail_count)})",
        ]
    )
    for outcome, count in DIRECT_CYPHER_NONVALIDATION_XFAIL_COUNTS.items():
        lines.append(f"- {outcome}: {count}")

    lines.append("")
    lines.append("Direct local Cypher non-validation triage samples:")
    for outcome, samples in _direct_cypher_nonvalidation_samples(SCENARIOS).items():
        lines.append(f"- {outcome}:")
        for sample in samples:
            lines.append(f"  - {sample}")

    priority_lanes = build_priority_lane_summaries(SCENARIOS)
    primary_families = build_primary_family_summaries(SCENARIOS)
    issue_backed_lane_count = sum(
        1
        for definition in PRIMARY_FAMILY_DEFINITIONS
        if definition.tracker_ref.startswith("#")
    )
    todo_lane_count = sum(
        1
        for definition in PRIMARY_FAMILY_DEFINITIONS
        if definition.tracker_ref.startswith("TODO(")
    )
    issue_backed_family_xfails = sum(
        family.xfail_count
        for family in primary_families
        if family.definition.tracker_ref.startswith("#")
    )
    todo_family_xfails = sum(
        family.xfail_count
        for family in primary_families
        if family.definition.tracker_ref.startswith("TODO(")
    )

    lines.extend(
        [
            "",
            "Ownership split (heuristic):",
            f"- tck-governance lanes with concrete issue trackers: {issue_backed_lane_count}",
            f"- tck-governance lanes still TODO-tracked: {todo_lane_count}",
            f"- xfails in issue-backed lanes (implementation follow-up): {issue_backed_family_xfails}",
            f"- xfails in TODO-tracked lanes (planning/backlog follow-up): {todo_family_xfails}",
        ]
    )

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
    parser = argparse.ArgumentParser(
        description="Emit the tck-gfql conformance report and JSON artifact."
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
        help=f"Path for the stable JSON artifact (default: {DEFAULT_JSON_OUTPUT})",
    )
    args = parser.parse_args()

    report = build_report()
    print(report)
    write_json_artifact(args.json_output, build_json_artifact())
    print(f"JSON artifact written: {args.json_output}")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(report)
            summary.write(f"\nJSON artifact written: `{args.json_output}`\n")


if __name__ == "__main__":
    main()
