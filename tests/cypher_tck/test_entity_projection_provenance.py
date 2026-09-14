"""Entity reconstruction uses projection provenance, not dotted-column guesses."""
import pandas as pd
import pytest

import graphistry
from tests.cypher_tck.test_tck_runner import _normalize_rows, _rows_from_result


@pytest.mark.parametrize("values,expected", [
    ([], []),
    (["same", "same"], [{"x": "({name: 'same'})"}, {"x": "({name: 'same'})"}]),
    ([None, "same"], [{"x": None}, {"x": "({name: 'same'})"}]),
])
def test_explicit_unlabeled_entity_kind_renders_rows(values, expected):
    g = graphistry.nodes(pd.DataFrame({"x.name": pd.Series(values, dtype="object")}), "id")
    g._cypher_entity_projection_kinds = {"x": "nodes"}
    out = _rows_from_result(g)
    assert all(set(row) == {"x"} for row in out)
    assert _normalize_rows(out, ["x"]) == _normalize_rows(expected, ["x"])


def test_explicit_property_projection_does_not_use_stale_entity_metadata():
    g = graphistry.nodes(pd.DataFrame({"x.name": ["Alice"]}), "id")
    g._cypher_entity_projection_kinds = {}
    g._cypher_entity_projection_meta = {"x": {"table": "nodes"}}
    assert _rows_from_result(g) == [{"x.name": "Alice"}]


def test_older_product_entity_metadata_remains_supported():
    g = graphistry.nodes(pd.DataFrame({"x.name": ["Alice"]}), "id")
    g._cypher_entity_projection_meta = {"x": {"table": "nodes"}}
    assert _rows_from_result(g) == [{"x": "({name: 'Alice'})"}]


@pytest.mark.parametrize("engine", ["pandas", "polars"])
def test_present_entity_with_null_properties_is_not_an_absent_entity(engine):
    from graphistry.compute.gfql.cypher.lowering import ResultProjectionColumn, ResultProjectionPlan
    from graphistry.compute.gfql.cypher.result_postprocess import apply_result_projection

    frame = pd.DataFrame({"x": [True, None], "x.name": [None, None]})
    if engine == "polars":
        pl = pytest.importorskip("polars")
        frame = pl.from_pandas(frame)
    g = graphistry.nodes(frame, "id")
    plan = ResultProjectionPlan(
        alias="x", table="nodes",
        columns=(ResultProjectionColumn("renamed", "whole_row"),),
    )
    out = apply_result_projection(g, plan)
    actual = _rows_from_result(out)
    expected = [{"renamed": "()"}, {"renamed": None}]
    assert all(set(row) == {"renamed"} for row in actual)
    assert _normalize_rows(actual, ["renamed"]) == _normalize_rows(expected, ["renamed"])
