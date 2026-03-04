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
