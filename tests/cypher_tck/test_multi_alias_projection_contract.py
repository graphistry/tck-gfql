"""Multi-alias returns preserve values and multiplicity around endpoint joins."""
import os

import pandas as pd
import pytest

import graphistry
from graphistry.tests.compute.gfql.routes.switch import ROUTES, routes_off
from tests.cypher_tck.comparator import compare_rows


CASES = [
    ("forward", "MATCH (a:Message {id: 10})-[e:REL]->(b:Person) "
     "RETURN a.value AS source, b.value AS target, e.weight AS weight", [
         {"source": "seed", "target": "tail", "weight": 5},
         {"source": "seed", "target": "tail", "weight": 6},
         {"source": "seed", "target": None, "weight": 7},
     ]),
    ("repeat", "MATCH (a:Message {id: 10})-[:REL]->(b:Person) "
     "RETURN a.value AS first, a.value AS again, b.value AS target", [
         {"first": "seed", "again": "seed", "target": "tail"},
         {"first": "seed", "again": "seed", "target": "tail"},
         {"first": "seed", "again": "seed", "target": None},
     ]),
    ("reverse", "MATCH (b:Person {id: 20})<-[e:REL]-(a:Message) "
     "RETURN a.value AS source, b.value AS target, e.weight AS weight", [
         {"source": "seed", "target": "tail", "weight": 5},
         {"source": "seed", "target": "tail", "weight": 6},
     ]),
    ("empty", "MATCH (a:Message {id: 99})-[e:REL]->(b:Person) "
     "RETURN a.value AS source, b.value AS target, e.weight AS weight", []),
]


@pytest.mark.parametrize("backend", ["pandas", "polars", "cudf"])
@pytest.mark.parametrize("disable_routes", [False, True])
@pytest.mark.parametrize("case,query,expected", CASES, ids=[case[0] for case in CASES])
def test_multi_alias_projection_contract(backend, disable_routes, case, query, expected):
    if backend == "polars" and os.environ.get("TEST_POLARS") != "1":
        pytest.skip("Native Polars conformance requires TEST_POLARS=1")
    if backend == "cudf" and os.environ.get("TEST_CUDF") != "1":
        pytest.skip("cuDF conformance requires TEST_CUDF=1")
    nodes = pd.DataFrame({"id": [30, 10, 20], "type": ["Person", "Message", "Person"],
                          "value": [None, "seed", "tail"]})
    edges = pd.DataFrame({"src": [10, 10, 10, 30], "dst": [20, 20, 30, 20],
                          "type": ["REL"] * 4, "weight": [5, 6, 7, 8], "eid": [0, 1, 2, 3]})
    if backend == "polars":
        import polars as pl
        nodes, edges = pl.from_pandas(nodes), pl.from_pandas(edges)
    elif backend == "cudf":
        import cudf
        nodes, edges = cudf.from_pandas(nodes), cudf.from_pandas(edges)
    graph = graphistry.nodes(nodes, "id").edges(edges, "src", "dst", "eid").gfql_index_all(engine=backend)
    with routes_off(ROUTES if disable_routes else ()):
        result = graph.gfql(query, engine=backend)._nodes
    if backend == "polars":
        actual = result.to_dicts()
    else:
        actual = (result.to_pandas() if backend == "cudf" else result).to_dict("records")
    columns = ("first", "again", "target") if case == "repeat" else ("source", "target", "weight")
    assert tuple(result.columns) == columns
    comparison = compare_rows(
        scenario_key=f"multi-alias-projection/{case}/{backend}/{disable_routes}",
        expected_rows=expected, actual_rows=actual, columns=columns,
        ordered=False, nulls_equal=True,
    )
    assert comparison.matched, comparison.diagnostic
