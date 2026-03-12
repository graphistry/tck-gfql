from __future__ import annotations

from typing import List

import pandas as pd
import pytest

from tests.cypher_tck.plan_executor import (
    PlanPurityError,
    _to_pandas_for_state,
    execute_plan,
)
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


def test_strict_pure_map_index_projection() -> None:
    _assert_strict_pure_key("expr-map2-5-1")


def test_strict_pure_temporal_tostring_projection() -> None:
    _assert_strict_pure_key("expr-temporal6-7")


def test_strict_pure_allows_empty_select_projection_plan() -> None:
    _assert_strict_pure_key("return-orderby6-2")


def test_strict_pure_allows_empty_with_projection_plan() -> None:
    _assert_strict_pure_key("return6-18")


def test_strict_pure_dynamic_subscript_unwind_plan() -> None:
    _assert_strict_pure_key("return-orderby4-1")


def test_strict_pure_missing_property_count_distinct_plan() -> None:
    _assert_strict_pure_key("expr-aggregation8-2")


def test_strict_pure_boolean_where_delegates_without_local_eval() -> None:
    _assert_strict_pure_key("expr-boolean4-3")


def test_strict_pure_quantifier_where_size_filter_delegates() -> None:
    _assert_strict_pure_key("expr-quantifier9-1")


class _FakeFrameWithToPandas:
    def __init__(self, pdf: pd.DataFrame):
        self._pdf = pdf

    def to_pandas(self) -> pd.DataFrame:
        return self._pdf.copy()


def test_strict_pure_rejects_state_materialization_to_pandas() -> None:
    reasons: List[str] = []
    with pytest.raises(PlanPurityError, match="delegate_materialize_to_pandas"):
        _to_pandas_for_state(
            _FakeFrameWithToPandas(pd.DataFrame({"x": [1]})),
            strict_pure=True,
            impurity_reasons=reasons,
            reason="select_delegate_materialize_to_pandas",
        )
    assert reasons == ["select_delegate_materialize_to_pandas"]


def test_non_strict_tracks_state_materialization_reason() -> None:
    reasons: List[str] = []
    out = _to_pandas_for_state(
        _FakeFrameWithToPandas(pd.DataFrame({"x": [1]})),
        strict_pure=False,
        impurity_reasons=reasons,
        reason="select_delegate_materialize_to_pandas",
    )
    assert out.to_dict("records") == [{"x": 1}]
    assert reasons == ["select_delegate_materialize_to_pandas"]


@pytest.mark.parametrize("key", ["expr-list1-6-1", "expr-list1-8-1"])
def test_strict_pure_expected_select_error_not_preempted_by_impurity(key: str) -> None:
    scenario = _scenario(key)
    assert scenario.gfql is not None
    graph = _build_graph(scenario.graph)
    with pytest.raises(Exception) as exc:
        execute_plan(
            graph,
            scenario.graph,
            scenario.gfql,
            params=scenario.params,
            strict_pure=True,
        )
    assert not isinstance(exc.value, PlanPurityError)


def test_strict_pure_expected_where_error_not_preempted_by_impurity() -> None:
    scenario = _scenario("expr-comparison1-17")
    assert scenario.gfql is not None
    graph = _build_graph(scenario.graph)
    with pytest.raises(Exception) as exc:
        execute_plan(
            graph,
            scenario.graph,
            scenario.gfql,
            params=scenario.params,
            strict_pure=True,
        )
    assert not isinstance(exc.value, PlanPurityError)
