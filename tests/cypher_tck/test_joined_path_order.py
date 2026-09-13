"""Joined path order follows input node and edge positions across execution routes."""
import os

import pandas as pd
import pytest
import graphistry
from graphistry.compute import n, e_forward, e_reverse, rows, select
from graphistry.tests.compute.gfql.routes.registry import to_engine
from graphistry.tests.compute.gfql.routes.switch import ROUTES, routes_off


@pytest.mark.parametrize("engine", ["pandas", "polars", "cudf"])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("reverse_nodes", [False, True])
@pytest.mark.parametrize("reverse_edges", [False, True])
@pytest.mark.parametrize("hops", [1, 2])
@pytest.mark.parametrize("property_index", [False, True])
def test_joined_path_order_matches_input_positions(engine, reverse, reverse_nodes, reverse_edges, hops, property_index):
    if engine == "polars" and os.environ.get("TEST_POLARS") != "1":
        pytest.skip("Native Polars conformance requires TEST_POLARS=1")
    if engine == "cudf" and os.environ.get("TEST_CUDF") != "1":
        pytest.skip("cuDF lane runs with TEST_CUDF=1")
    node_ids = [20, 10, 30, 40][::-1 if reverse_nodes else 1]
    edge_rows = [(10, 30, 0), (20, 30, 1), (10, 40, 2),
                 (30, 40, 3), (20, 40, 4), (10, 30, 5)][::-1 if reverse_edges else 1]
    seeds = {30, 40} if reverse else {10, 20}
    nodes = pd.DataFrame({"id": node_ids, "seed": [int(node in seeds) for node in node_ids]})
    edges = pd.DataFrame(edge_rows, columns=["s", "d", "eid"])
    graph = graphistry.nodes(to_engine(nodes, engine), "id").edges(
        to_engine(edges, engine), "s", "d", "eid").gfql_index_all(engine=engine)
    if property_index:
        graph = graph.gfql_index_node_props(["seed"], engine=engine)
    paths = [(node, node, ()) for node in node_ids if node in seeds]
    ops = [n({"seed": 1}, name="a0")]
    for step in range(hops):
        expanded = []
        for seed, current, used in paths:
            for src, dst, eid in edge_rows:
                before, after = (dst, src) if reverse else (src, dst)
                if before == current and eid not in used:
                    expanded.append((seed, after, (*used, eid)))
        paths = expanded
        ops += [(e_reverse if reverse else e_forward)(name=f"e{step}"), n(name=f"a{step + 1}")]
    projection = [("seed", "a0.id"), ("target", f"a{hops}.id")]
    projection += [(f"edge_{step}", f"e{step}.eid") for step in range(hops)]
    ops += [rows(), select(projection)]
    expected = [{"seed": seed, "target": target, **{f"edge_{step}": eid for step, eid in enumerate(used)}}
                for seed, target, used in paths]
    for disabled in ((), ROUTES):
        with routes_off(disabled):
            result = graph.gfql(ops, engine=engine, index_policy="force")._nodes
        assert list(result.columns) == [name for name, _ in projection]
        if engine == "polars":
            actual = result.to_dicts()
        else:
            actual = (result.to_pandas() if engine == "cudf" else result).to_dict("records")
        assert actual == expected, (engine, disabled, property_index)
