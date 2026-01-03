from __future__ import annotations

import os
import sys
from collections import Counter
from typing import Iterable, List

from tests.cypher_tck.gfql_plan import is_placeholder
from tests.cypher_tck.models import Scenario

_PYGRAPHISTRY_PATH = os.environ.get("PYGRAPHISTRY_PATH")
if _PYGRAPHISTRY_PATH and _PYGRAPHISTRY_PATH not in sys.path:
    sys.path.insert(0, _PYGRAPHISTRY_PATH)

try:
    from tests.cypher_tck.scenarios import SCENARIOS
except ModuleNotFoundError as exc:  # pragma: no cover - import-time guard
    if exc.name == "graphistry":
        raise SystemExit(
            "graphistry is required to import scenario modules. "
            "Set PYGRAPHISTRY_PATH=/path/to/pygraphistry or install graphistry."
        ) from exc
    raise


TARGET_TAGS = (
    "target-table-ops",
    "target-expr-dsl",
)

DEFER_TAGS = (
    "defer-quantifier",
    "defer-path-enum",
    "defer-expr-advanced",
    "defer-unwind",
    "defer-union",
)


def _is_missing_gfql(scenario: Scenario) -> bool:
    return scenario.gfql is None or is_placeholder(scenario.gfql)


def _filter_target(scenarios: Iterable[Scenario], tag: str) -> List[Scenario]:
    return [
        scenario
        for scenario in scenarios
        if scenario.status == "xfail"
        and _is_missing_gfql(scenario)
        and tag in scenario.tags
    ]


def _print_bucket(title: str, scenarios: List[Scenario], limit: int) -> None:
    print(f"{title}: {len(scenarios)}")
    for scenario in scenarios[:limit]:
        print(f"- {scenario.key} | {scenario.feature_path} | {scenario.scenario}")
    if len(scenarios) > limit:
        print(f"- ... {len(scenarios) - limit} more")


def main() -> None:
    limit = int(os.environ.get("BACKLOG_LIMIT", "40"))
    scenarios = list(SCENARIOS)

    print("GFQL porting backlog (xfail + gfql missing)")
    print("Target tags:", ", ".join(TARGET_TAGS))
    print("Defer tags:", ", ".join(DEFER_TAGS))
    print()

    tag_counts = Counter()
    for scenario in scenarios:
        if scenario.status != "xfail" or not _is_missing_gfql(scenario):
            continue
        tag_counts.update(scenario.tags)

    print("Top tag counts (xfail + gfql missing):")
    for tag, count in tag_counts.most_common(12):
        print(f"- {tag}: {count}")
    print()

    for tag in TARGET_TAGS:
        tagged = _filter_target(scenarios, tag)
        tagged.sort(key=lambda s: (s.feature_path, s.key))
        _print_bucket(f"Backlog for {tag}", tagged, limit)
        print()


if __name__ == "__main__":
    main()
