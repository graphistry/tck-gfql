"""Structured and textual queries must restore properties by entity identity."""
import os

import pandas as pd
import pytest

import graphistry
from graphistry.compute import e_forward, n, rows, select
from graphistry.tests.compute.gfql.routes.switch import ROUTES, routes_off


@pytest.mark.parametrize("backend", ["pandas", "polars", "cudf"])
@pytest.mark.parametrize("selected,expected", [(10, "ten"), (20, "twenty"), (30, None), (99, None)])
@pytest.mark.parametrize("disable_routes", [False, True])
def test_structured_and_cypher_alias_properties_follow_entity_keys(backend, selected, expected, disable_routes):
    if backend == "polars" and os.environ.get("TEST_POLARS") != "1":
        pytest.skip("Native Polars conformance requires TEST_POLARS=1")
    if backend == "cudf" and os.environ.get("TEST_CUDF") != "1":
        pytest.skip("cuDF conformance requires TEST_CUDF=1")
    nodes = pd.DataFrame({"id": [20, 10, 30], "value": ["twenty", "ten", None]})
    edges = pd.DataFrame({"s": [10, 20, 30], "d": [20, 30, 20], "eid": [0, 1, 2]})
    if backend == "polars":
        import polars as pl
        nodes, edges = pl.from_pandas(nodes), pl.from_pandas(edges)
    elif backend == "cudf":
        import cudf
        nodes, edges = cudf.from_pandas(nodes), cudf.from_pandas(edges)
    graph = graphistry.nodes(nodes, "id").edges(edges, "s", "d", "eid").gfql_index_all(engine=backend)
    structured = [n({"id": selected}, name="value"), e_forward(name="e"), n(name="b"),
                  rows(source="value"), select([("v", "value.value")])]
    cypher = f"MATCH (value)-[e]->(b) WHERE value.id = {selected} RETURN value.value AS v"
    expected_rows = [] if selected == 99 else [{"v": expected}]
    with routes_off(ROUTES if disable_routes else ()):
        for query in (structured, cypher):
            result = graph.gfql(query, engine=backend)._nodes
            if backend == "polars":
                if isinstance(result, pl.LazyFrame):
                    result = result.collect()
                actual = result.to_dicts()
            else:
                actual = (result.to_pandas() if backend == "cudf" else result).to_dict("records")
            assert actual == expected_rows
