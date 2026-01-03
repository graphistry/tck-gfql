from __future__ import annotations

from dataclasses import replace
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
from typing import Iterable, Tuple

from tests.cypher_tck.gfql_plan import distinct, limit, order_by, plan, select, skip, step
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


_CLAUSE_RE = re.compile(
    r"(?im)^(OPTIONAL MATCH|ORDER BY|MATCH|WHERE|WITH|RETURN|UNWIND|SKIP|LIMIT|CREATE|MERGE|DELETE|SET|REMOVE|CALL)\\b"
)


def _split_clauses(cypher: str) -> Tuple[Tuple[str, str], ...]:
    text = cypher.strip()
    if not text:
        return ()
    matches = list(_CLAUSE_RE.finditer(text))
    if not matches:
        return (("RAW", text),)
    clauses = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        clause = match.group(1).upper()
        body = text[start:end].strip()
        clauses.append((clause, body))
    return tuple(clauses)


def _split_top_level(expr: str) -> Tuple[str, ...]:
    items = []
    buf = []
    depth = 0
    in_single = False
    in_double = False
    idx = 0
    while idx < len(expr):
        ch = expr[idx]
        if ch == "'" and not in_double:
            in_single = not in_single
            buf.append(ch)
        elif ch == '"' and not in_single:
            in_double = not in_double
            buf.append(ch)
        elif not in_single and not in_double:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth = max(0, depth - 1)
            if ch == "," and depth == 0:
                item = "".join(buf).strip()
                if item:
                    items.append(item)
                buf = []
                idx += 1
                continue
            buf.append(ch)
        else:
            buf.append(ch)
        idx += 1
    tail = "".join(buf).strip()
    if tail:
        items.append(tail)
    return tuple(items)


def _strip_distinct(body: str) -> Tuple[bool, str]:
    if body.upper().startswith("DISTINCT "):
        return True, body[len("DISTINCT ") :].strip()
    return False, body


def _parse_return_items(body: str) -> Tuple[Tuple[str, str], ...]:
    items = []
    for item in _split_top_level(body):
        parts = re.split(r"(?i)\\s+AS\\s+", item, maxsplit=1)
        if len(parts) == 2:
            expr, alias = parts[0].strip(), parts[1].strip()
        else:
            expr = item.strip()
            alias = expr
        items.append((alias, expr))
    return tuple(items)


def _parse_order_by(body: str) -> Tuple[Tuple[str, str], ...]:
    items = []
    for item in _split_top_level(body):
        match = re.match(r"(?is)(.+?)\\s+(ASC|DESC)$", item.strip())
        if match:
            expr = match.group(1).strip()
            direction = match.group(2).lower()
        else:
            expr = item.strip()
            direction = "asc"
        items.append((expr, direction))
    return tuple(items)


def _parse_value(token: str):
    value = token.strip()
    if re.fullmatch(r"-?\\d+", value):
        return int(value)
    if re.fullmatch(r"-?\\d+\\.\\d+", value):
        return float(value)
    return value


def _plan_from_cypher(cypher: str) -> Tuple:
    steps = []
    for clause, body in _split_clauses(cypher):
        if clause in ("MATCH", "OPTIONAL MATCH"):
            steps.append(step("match", pattern=body, optional=(clause == "OPTIONAL MATCH")))
        elif clause == "WHERE":
            steps.append(step("where", expr=body))
        elif clause == "UNWIND":
            parts = re.split(r"(?i)\\s+AS\\s+", body, maxsplit=1)
            payload = {"expr": parts[0].strip()}
            if len(parts) == 2:
                payload["as_"] = parts[1].strip()
            steps.append(step("unwind", **payload))
        elif clause == "WITH":
            distinct_flag, content = _strip_distinct(body)
            steps.append(step("with", items=_parse_return_items(content)))
            if distinct_flag:
                steps.append(distinct())
        elif clause == "RETURN":
            distinct_flag, content = _strip_distinct(body)
            steps.append(select(_parse_return_items(content)))
            if distinct_flag:
                steps.append(distinct())
        elif clause == "ORDER BY":
            steps.append(order_by(_parse_order_by(body)))
        elif clause == "SKIP":
            steps.append(skip(_parse_value(body)))
        elif clause == "LIMIT":
            steps.append(limit(_parse_value(body)))
        else:
            steps.append(step(clause.lower().replace(" ", "_"), expr=body))
    if not steps:
        steps.append(step("raw", expr=cypher))
    return plan(*steps)


def _apply_translation(scenario: Scenario) -> Scenario:
    if scenario.status != "xfail":
        return scenario
    if scenario.gfql is not None:
        return scenario
    if "target-table-ops" in scenario.tags or "target-expr-dsl" in scenario.tags:
        return replace(scenario, gfql=_plan_from_cypher(scenario.cypher))
    return scenario


for path in sorted(_SCENARIO_ROOT.rglob("*.py"), key=lambda p: p.as_posix()):
    module_name = "tests.cypher_tck.scenarios." + path.relative_to(Path(__file__).resolve().parent).with_suffix("").as_posix().replace("/", ".")
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        continue
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    SCENARIOS.extend(getattr(module, "SCENARIOS", []))

SCENARIOS = [_apply_translation(_tag_scenario(scenario)) for scenario in SCENARIOS]
