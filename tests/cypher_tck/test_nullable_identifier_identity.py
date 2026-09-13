"""Nullable integer identifiers retain exact entity identity through indexed queries."""
import os

import numpy as np
import pandas as pd
import pytest

import graphistry
from graphistry.compute import e_forward, n, rows, select
from graphistry.tests.compute.gfql.routes.switch import ROUTES, routes_off
from tests.cypher_tck.comparator import compare_rows


@pytest.mark.parametrize("backend", ["pandas", "polars", "cudf"])
@pytest.mark.parametrize("dtype,big", [("Int64", 2**53), ("UInt64", 2**63)])
@pytest.mark.parametrize("seed_offset", [0, 1, 2])
@pytest.mark.parametrize("disable_routes", [False, True])
def test_nullable_identifier_projection(backend, dtype, big, seed_offset, disable_routes):
    if backend == "polars" and os.environ.get("TEST_POLARS") != "1":
        pytest.skip("Native Polars conformance requires TEST_POLARS=1")
    if backend == "cudf" and os.environ.get("TEST_CUDF") != "1":
        pytest.skip("cuDF conformance requires TEST_CUDF=1")

    def ids(values):
        return pd.array(np.asarray(values, dtype=object), dtype=dtype)

    nodes = pd.DataFrame({"id": ids([None, big + 1, big]), "value": [None, "high", "low"]})
    edges = pd.DataFrame({"s": ids([None, big, big + 1, big]), "d": ids([big, big + 1, big, None])})
    if backend == "polars":
        import polars as pl
        nodes, edges = pl.from_pandas(nodes), pl.from_pandas(edges)
    elif backend == "cudf":
        import cudf
        nodes, edges = cudf.from_pandas(nodes), cudf.from_pandas(edges)
    graph = graphistry.nodes(nodes, "id").edges(edges, "s", "d").create_index("node_id", engine=backend).gfql_index_edges("both", engine=backend)
    query = [n({"id": big + seed_offset}, name="a"), e_forward(), n(name="b"),
             rows(source="b"), select([("identifier", "b.id"), ("value", "b.value")])]
    expected = ([{"identifier": big + 1, "value": "high"}] if seed_offset == 0 else
                [{"identifier": big, "value": "low"}] if seed_offset == 1 else [])
    with routes_off(ROUTES if disable_routes else ()):
        result = graph.gfql(query, engine=backend)._nodes
    if backend == "polars":
        if isinstance(result, pl.LazyFrame):
            result = result.collect()
        actual = result.to_dicts()
    else:
        actual = (result.to_pandas() if backend == "cudf" else result).to_dict("records")
    comparison = compare_rows(
        scenario_key=f"nullable-identifier/{backend}/{dtype}/{seed_offset}/{disable_routes}",
        expected_rows=expected, actual_rows=actual,
        columns=("identifier", "value"), ordered=True, nulls_equal=True,
    )
    assert comparison.matched, comparison.diagnostic
