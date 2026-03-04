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


def _assert_semantic_and_strict_pure(key: str) -> None:
    scenario = _scenario(key)
    assert scenario.gfql is not None
    assert scenario.expected.rows is not None

    graph = _build_graph(scenario.graph)
    semantic_rows = execute_plan(
        graph,
        scenario.graph,
        scenario.gfql,
        params=scenario.params,
        strict_pure=False,
    )
    _assert_expected_rows(scenario, semantic_rows.to_dict("records"))

    impurity_reasons: List[str] = []
    strict_rows = execute_plan(
        graph,
        scenario.graph,
        scenario.gfql,
        params=scenario.params,
        strict_pure=True,
        impurity_reasons=impurity_reasons,
    )
    _assert_expected_rows(scenario, strict_rows.to_dict("records"))
    assert impurity_reasons == []


def test_where_starts_with_delegates_pure() -> None:
    _assert_semantic_and_strict_pure("expr-string8-1")


def test_where_ends_with_delegates_pure() -> None:
    _assert_semantic_and_strict_pure("expr-string9-1")


def test_where_contains_delegates_pure() -> None:
    _assert_semantic_and_strict_pure("expr-string10-1")


def test_where_starts_with_and_ends_with_same_column_delegates_pure() -> None:
    _assert_semantic_and_strict_pure("expr-string11-1")


def test_select_in_expression_delegates_pure() -> None:
    _assert_semantic_and_strict_pure("expr-list5-1")


def test_select_xor_expression_delegates_pure() -> None:
    _assert_semantic_and_strict_pure("expr-boolean3-4")
