from __future__ import annotations

import os
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

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


def build_report() -> str:
    total = len(SCENARIOS)
    status_counts = Counter(scenario.status for scenario in SCENARIOS)
    gfql_defined = sum(1 for scenario in SCENARIOS if scenario.gfql is not None)
    missing_gfql = total - gfql_defined
    supported_defined = sum(
        1
        for scenario in SCENARIOS
        if scenario.status == "supported" and scenario.gfql is not None
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
        if scenario.status == "supported" and scenario.gfql is None
    )

    supported_count = status_counts.get("supported", 0)
    xfail_count = status_counts.get("xfail", 0)
    skip_count = status_counts.get("skip", 0)
    other_count = total - supported_count - xfail_count - skip_count

    group_counts: Dict[str, Counter] = defaultdict(Counter)
    area_counts: Dict[str, Counter] = defaultdict(Counter)
    xfail_tags = Counter()

    for scenario in SCENARIOS:
        group, area = _feature_parts(scenario.feature_path)
        for bucket in (group_counts[group], area_counts[area]):
            bucket["total"] += 1
            bucket[scenario.status] += 1
        if scenario.status == "xfail":
            xfail_tags.update(scenario.tags)

    lines = [
        "GFQL conformance report (tck-gfql)",
        "",
        f"Scenarios represented (ported): {total}",
        f"GFQL translated (non-None): {gfql_defined} ({_percent(gfql_defined, total)})",
        f"GFQL missing: {missing_gfql} ({_percent(missing_gfql, total)})",
        f"Translated + expected pass (supported): {supported_defined}",
        f"Translated but xfail: {translated_xfail}",
        f"Translated but skip: {translated_skip}",
        f"Supported but missing GFQL: {supported_missing}",
        f"Status counts: supported {supported_count}, "
        f"xfail {xfail_count}, "
        f"skip {skip_count}, "
        f"other {other_count}",
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
