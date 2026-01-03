from __future__ import annotations

from dataclasses import replace
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Iterable, Tuple

from tests.cypher_tck.gfql_plan import placeholder, plan
from tests.cypher_tck.models import Scenario

_SCENARIO_ROOT = Path(__file__).resolve().parent / "tck" / "features"
SCENARIOS = []

_TARGET_TABLE_PREFIXES = (
    "clauses/return",
    "clauses/with",
)

_TARGET_EXPR_PREFIXES = (
    "expressions/aggregation",
    "expressions/boolean",
    "expressions/comparison",
    "expressions/list",
    "expressions/literals",
    "expressions/mathematical",
    "expressions/null",
    "expressions/precedence",
    "expressions/string",
    "expressions/temporal",
)

_DEFER_EXPR_PREFIXES = (
    "expressions/conditional",
    "expressions/existentialSubqueries",
    "expressions/graph",
    "expressions/map",
    "expressions/pattern",
    "expressions/typeConversion",
)


def _merge_tags(existing: Tuple[str, ...], extra: Iterable[str]) -> Tuple[str, ...]:
    tags = list(existing)
    for tag in extra:
        if tag not in tags:
            tags.append(tag)
    return tuple(tags)


def _extension_tags(feature_path: str) -> Tuple[str, ...]:
    tags = []
    if any(prefix in feature_path for prefix in _TARGET_TABLE_PREFIXES):
        tags.append("target-table-ops")
    if any(prefix in feature_path for prefix in _TARGET_EXPR_PREFIXES):
        tags.append("target-expr-dsl")
    if "expressions/quantifier" in feature_path:
        tags.append("defer-quantifier")
    if "expressions/path" in feature_path:
        tags.append("defer-path-enum")
    if any(prefix in feature_path for prefix in _DEFER_EXPR_PREFIXES):
        tags.append("defer-expr-advanced")
    if "clauses/unwind" in feature_path:
        tags.append("defer-unwind")
    if "clauses/union" in feature_path:
        tags.append("defer-union")
    return tuple(tags)


def _tag_scenario(scenario: Scenario) -> Scenario:
    if scenario.status != "xfail":
        return scenario
    extra_tags = _extension_tags(scenario.feature_path)
    if not extra_tags:
        return scenario
    return replace(scenario, tags=_merge_tags(scenario.tags, extra_tags))


def _placeholder_plan(scenario: Scenario) -> Tuple:
    return plan(
        placeholder(
            "auto placeholder for target-table-ops/target-expr-dsl",
            feature_path=scenario.feature_path,
            scenario_key=scenario.key,
        )
    )


def _apply_placeholder(scenario: Scenario) -> Scenario:
    if scenario.status != "xfail":
        return scenario
    if scenario.gfql is not None:
        return scenario
    if "target-table-ops" in scenario.tags or "target-expr-dsl" in scenario.tags:
        return replace(scenario, gfql=_placeholder_plan(scenario))
    return scenario


for path in sorted(_SCENARIO_ROOT.rglob("*.py"), key=lambda p: p.as_posix()):
    module_name = "tests.cypher_tck.scenarios." + path.relative_to(Path(__file__).resolve().parent).with_suffix("").as_posix().replace("/", ".")
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        continue
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    SCENARIOS.extend(getattr(module, "SCENARIOS", []))

SCENARIOS = [_apply_placeholder(_tag_scenario(scenario)) for scenario in SCENARIOS]
