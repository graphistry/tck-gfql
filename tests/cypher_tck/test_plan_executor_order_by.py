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


def test_order_by_raw_suffix_ascending_delegates_pure() -> None:
    _assert_semantic_and_strict_pure("with-orderby1-25-3")


def test_order_by_raw_suffix_descending_delegates_pure() -> None:
    _assert_semantic_and_strict_pure("with-orderby1-26-2")
