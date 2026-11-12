from dataclasses import replace
from types import SimpleNamespace

import pandas as pd
import pytest

from tests.cypher_tck.models import Expected, GraphFixture, MutationEffects, Scenario
from tests.cypher_tck.mutation_oracle import (
    assert_post_graph, effects_between, execute_and_assert_mutation, fixture_state,
)


def _scenario() -> Scenario:
    return Scenario(
        key="test-mutation", feature_path="test", scenario="no-op guard", cypher="CREATE ()",
        graph=GraphFixture(nodes=[], edges=[]), gfql=None,
        expected=Expected(rows=[], post_graph=GraphFixture(nodes=[{"id": 0}], edges=[]),
                          effects=MutationEffects(nodes_created=1)),
        tags=("mutation", "mutation-no-return"),
    )


def _graph(nodes: list) -> SimpleNamespace:
    graph = SimpleNamespace(_nodes=pd.DataFrame(nodes, columns=["id"]),
                            _edges=pd.DataFrame(columns=["src", "dst", "edge_id", "type"]),
                            _node="id", _source="src", _destination="dst", _edge="edge_id")
    graph.gfql_graph = graph
    return graph


def test_no_op_cannot_pass_empty_rows() -> None:
    source = _graph([])
    source.gfql = lambda *args, **kwargs: source
    with pytest.raises(AssertionError, match="poststate"):
        execute_and_assert_mutation(source, _scenario(), engine="pandas")


def test_input_mutation_is_independently_rejected() -> None:
    source = _graph([])
    def mutate(*args, **kwargs):
        source._nodes = pd.DataFrame({"id": [0]})
        return source
    source.gfql = mutate
    with pytest.raises(AssertionError, match="caller"):
        execute_and_assert_mutation(source, _scenario(), engine="pandas")


def test_effect_oracle_rejects_wrong_counts() -> None:
    source = _graph([])
    source.gfql = lambda *args, **kwargs: _graph([{"id": 0}])
    scenario = _scenario()
    # A public numeric id is a property on a legacy graph. The graph matches
    # structurally after fixture identity is removed, but the effect must fail.
    scenario = replace(scenario, expected=replace(
        scenario.expected,
        post_graph=GraphFixture(nodes=[{"__fixture_id__": 0, "id": 0}], edges=[], node_id="__fixture_id__"),
        effects=MutationEffects(nodes_created=2),
    ))
    with pytest.raises(AssertionError, match="side effects"):
        execute_and_assert_mutation(source, scenario, engine="pandas")


def test_complete_graph_compares_parallel_edges_direction_and_properties() -> None:
    fixture = GraphFixture(nodes=[{"id": "a"}, {"id": "b"}], edges=[
        {"src": "a", "dst": "b", "edge_id": 0, "type": "R", "weight": 2},
        {"src": "a", "dst": "b", "edge_id": 1, "type": "R", "weight": 3},
    ])
    assert_post_graph(fixture_state(fixture), fixture)
    for edges in [fixture.edges[:1], [dict(edge, src=edge["dst"], dst=edge["src"]) for edge in fixture.edges]]:
        with pytest.raises(AssertionError, match="poststate"):
            assert_post_graph(fixture_state(replace(fixture, edges=edges)), fixture)


def test_label_effects_count_distinct_names_not_memberships() -> None:
    before = fixture_state(GraphFixture(nodes=[], edges=[]))
    after = fixture_state(GraphFixture(nodes=[{"id": 1, "labels": ["L"]}, {"id": 2, "labels": ["L"]}], edges=[]))
    assert effects_between(before, after) == MutationEffects(nodes_created=2, labels_added=1)
