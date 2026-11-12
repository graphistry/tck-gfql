"""Independent complete graph/effect oracles for direct-Cypher write scenarios.

The runner may copy native values to Python for assertions; product execution may
not use this harness as an implementation. Physical identities are matched up to
renaming for poststate, while effect deltas preserve identity within an execution.
"""
from collections import Counter
from dataclasses import dataclass
from typing import Any

import networkx as nx
import pandas as pd

from tests.cypher_tck.models import GraphFixture, MutationEffects, Scenario



class PoststateMismatch(AssertionError):
    pass


class CallerMutation(AssertionError):
    pass


class EffectMismatch(AssertionError):
    pass

def _records(frame: Any) -> list[dict]:
    if frame is None:
        return []
    if hasattr(frame, "to_arrow"):
        return frame.to_arrow().to_pylist()
    return frame.to_dict("records")


def _null(value: Any) -> bool:
    return value is None or not isinstance(value, (list, tuple, dict)) and bool(pd.isna(value))


def _value(value: Any) -> Any:
    if _null(value):
        return None
    if isinstance(value, dict):
        return tuple(sorted((key, _value(item)) for key, item in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_value(item) for item in value)
    if hasattr(value, "item"):
        value = value.item()
    return type(value).__name__, value


def snapshot_input(graph: Any) -> tuple:
    def frame(value: Any) -> tuple:
        if value is None:
            return (None,)
        return tuple(value.columns), tuple(map(str, value.dtypes)), _value(_records(value))
    return (frame(graph._nodes), frame(graph._edges), graph._node, graph._source,
            graph._destination, graph._edge)


def _labels(row: dict) -> frozenset[str]:
    labels = row.get("labels")
    if _null(labels):
        labels = []
    if isinstance(labels, str):
        labels = [labels]
    return frozenset(labels) | frozenset(
        name[len("label__"):] for name, value in row.items()
        if name.startswith("label__") and not _null(value) and bool(value)
    )


def _node_properties(row: dict, node_id: str, *, fixture: bool) -> dict:
    result = {}
    for name, value in row.items():
        if name.startswith(("__", "label__")) or name in {"labels", "type"} or _null(value):
            continue
        if fixture and name == node_id:
            continue
        if name == "id" and not fixture:
            marker = row.get("__gfql_id_property_present__")
            if marker is not None and not bool(marker):
                continue
            if marker is None and isinstance(value, str):
                continue
        result[name] = _value(value)
    return result


@dataclass
class GraphState:
    graph: nx.MultiDiGraph
    node_properties: set
    edge_properties: set
    labels: set[str]
    edge_ids: set


def graph_state(graph: Any) -> GraphState:
    return _state(_records(graph._nodes), _records(graph._edges), graph._node,
                  graph._source, graph._destination, graph._edge, fixture=False)


def fixture_state(fixture: GraphFixture) -> GraphState:
    return _state(list(fixture.nodes), list(fixture.edges), fixture.node_id,
                  fixture.src, fixture.dst, fixture.edge_id, fixture=True)


def _state(nodes: list[dict], edges: list[dict], node_id: str, src: str, dst: str,
           edge_id: str, *, fixture: bool) -> GraphState:
    graph = nx.MultiDiGraph()
    properties, edge_properties, all_labels, edge_ids = set(), set(), set(), set()
    for row in nodes:
        identity = row[node_id]
        assert not _null(identity) and identity not in graph, "Invalid or duplicated physical node identity"
        labels = _labels(row)
        props = _node_properties(row, node_id, fixture=fixture)
        graph.add_node(identity, labels=labels, properties=props)
        properties.update((identity, name, value) for name, value in props.items())
        all_labels.update(labels)
    for index, row in enumerate(edges):
        source, destination = row[src], row[dst]
        assert source in graph and destination in graph, "Edge endpoint is absent from the node table"
        identity = row.get(edge_id, index)
        assert identity not in edge_ids, "Duplicated physical relationship identity"
        edge_ids.add(identity)
        excluded = {src, dst, edge_id, "type", "undirected"}
        props = {name: _value(value) for name, value in row.items()
                 if name not in excluded and not name.startswith("__") and not _null(value)}
        graph.add_edge(source, destination, key=identity, type=row.get("type"), properties=props)
        edge_properties.update((identity, name, value) for name, value in props.items())
    return GraphState(graph, properties, edge_properties, all_labels, edge_ids)


def assert_post_graph(actual: GraphState, expected: GraphFixture) -> None:
    target = fixture_state(expected).graph
    def edge_match(left: dict, right: dict) -> bool:
        return Counter(_value(value) for value in left.values()) == Counter(_value(value) for value in right.values())
    matcher = nx.algorithms.isomorphism.MultiDiGraphMatcher(
        actual.graph, target, node_match=lambda left, right: left == right,
        edge_match=edge_match,
    )
    if not matcher.is_isomorphic():
        raise PoststateMismatch("Mutation full graph poststate differs from the independent fixture")


def effects_between(before: GraphState, after: GraphState) -> MutationEffects:
    before_nodes, after_nodes = set(before.graph), set(after.graph)
    return MutationEffects(
        nodes_created=len(after_nodes - before_nodes), nodes_deleted=len(before_nodes - after_nodes),
        relationships_created=len(after.edge_ids - before.edge_ids),
        relationships_deleted=len(before.edge_ids - after.edge_ids),
        properties_added=len(after.node_properties - before.node_properties) + len(after.edge_properties - before.edge_properties),
        properties_removed=len(before.node_properties - after.node_properties) + len(before.edge_properties - after.edge_properties),
        labels_added=len(after.labels - before.labels), labels_removed=len(before.labels - after.labels),
    )


def execute_and_assert_mutation(source: Any, scenario: Scenario, *, engine: str) -> Any:
    assert scenario.expected.post_graph is not None, "Mutation requires a full poststate oracle"
    assert scenario.expected.effects is not None, "Mutation requires the original side-effect oracle"
    immutable = snapshot_input(source)
    before = graph_state(source)
    result = source.gfql(scenario.cypher, params=scenario.params, engine=engine)
    if snapshot_input(source) != immutable:
        raise CallerMutation("Mutation changed the caller frames or bindings")
    after = graph_state(result.gfql_graph)
    assert_post_graph(after, scenario.expected.post_graph)
    if effects_between(before, after) != scenario.expected.effects:
        raise EffectMismatch("Mutation side effects differ from the original TCK oracle")
    return result
