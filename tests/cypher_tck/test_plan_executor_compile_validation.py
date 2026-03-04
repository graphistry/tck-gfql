from __future__ import annotations

import pytest

from tests.cypher_tck.plan_executor import PlanExecutionError, execute_plan
from tests.cypher_tck.scenarios import SCENARIOS
from tests.cypher_tck.test_tck_runner import _build_graph


def _scenario(key: str):
    for scenario in SCENARIOS:
        if scenario.key == key:
            return scenario
    raise AssertionError(f"scenario not found: {key}")


def _assert_plan_raises(key: str) -> None:
    scenario = _scenario(key)
    assert scenario.gfql is not None
    graph = _build_graph(scenario.graph)
    with pytest.raises(PlanExecutionError):
        execute_plan(
            graph,
            scenario.graph,
            scenario.gfql,
            params=scenario.params,
            strict_pure=False,
        )


def _assert_plan_executes(key: str) -> None:
    scenario = _scenario(key)
    assert scenario.gfql is not None
    graph = _build_graph(scenario.graph)
    execute_plan(
        graph,
        scenario.graph,
        scenario.gfql,
        params=scenario.params,
        strict_pure=False,
    )


def test_boolean_or_non_boolean_literal_is_compile_error() -> None:
    _assert_plan_raises("expr-boolean2-8-1")


def test_boolean_not_non_boolean_literal_is_compile_error() -> None:
    _assert_plan_raises("expr-boolean4-4-1")


def test_with_order_by_out_of_scope_variable_is_compile_error() -> None:
    _assert_plan_raises("with-orderby1-46-1")


def test_with_order_by_aggregation_expression_is_compile_error() -> None:
    _assert_plan_raises("with-orderby2-25-1")


def test_return_duplicate_alias_is_compile_error() -> None:
    _assert_plan_raises("return4-10")


def test_return_unknown_function_is_compile_error() -> None:
    _assert_plan_raises("return2-18")


def test_with_order_by_can_use_pre_projection_scope_variable() -> None:
    _assert_plan_executes("with-orderby2-21-1")


def test_with_order_by_can_use_previous_with_alias_before_projection() -> None:
    _assert_plan_executes("with-orderby4-8")
