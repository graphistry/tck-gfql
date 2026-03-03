from __future__ import annotations

from typing import List

from tests.cypher_tck.plan_executor import execute_plan
from tests.cypher_tck.scenarios import SCENARIOS
from tests.cypher_tck.test_tck_runner import _assert_expected_rows, _build_graph


def _scenario(key: str):
    for scenario in SCENARIOS:
        if scenario.key == key:
            return scenario
    raise AssertionError(f"scenario not found: {key}")


def _assert_strict_pure_key(key: str) -> None:
    scenario = _scenario(key)
    assert scenario.gfql is not None
    assert scenario.expected.rows is not None

    impurity_reasons: List[str] = []
    graph = _build_graph(scenario.graph)
    rows_df = execute_plan(
        graph,
        scenario.graph,
        scenario.gfql,
        params=scenario.params,
        strict_pure=True,
        impurity_reasons=impurity_reasons,
    )
    _assert_expected_rows(scenario, rows_df.to_dict("records"))
    assert impurity_reasons == []


def test_strict_pure_list_comparison_projection() -> None:
    _assert_strict_pure_key("expr-list3-1")


def test_strict_pure_unary_neg_parenthesized_projection() -> None:
    _assert_strict_pure_key("expr-precedence2-5-1")


def test_strict_pure_toboolean_projection() -> None:
    _assert_strict_pure_key("expr-typeconversion1-3")
