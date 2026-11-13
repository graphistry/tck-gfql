import graphistry
from dataclasses import replace
from types import SimpleNamespace

import pandas as pd
import pytest

from tests.cypher_tck.models import Expected, GraphFixture, MutationEffects, Scenario
from tests.cypher_tck.mutation_oracle import (
    CallerMutation, EffectMismatch, ExistingIdentityMismatch, PoststateMismatch,
    assert_post_graph, effects_between, execute_and_assert_mutation, fixture_state,
)
from tests.cypher_tck import test_tck_runner
from tests.cypher_tck.test_tck_runner import (
    _assert_expected_rows,
    _classify_xfail_mutation_oracle,
    _returned_rows_for_mutation,
    _rows_from_result,
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
    with pytest.raises(PoststateMismatch):
        execute_and_assert_mutation(source, _scenario(), engine="pandas")


def test_input_mutation_is_independently_rejected() -> None:
    source = _graph([])
    def mutate(*args, **kwargs):
        source._nodes = pd.DataFrame({"id": [0]})
        return source
    source.gfql = mutate
    with pytest.raises(CallerMutation):
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
    with pytest.raises(EffectMismatch):
        execute_and_assert_mutation(source, scenario, engine="pandas")


def test_complete_graph_compares_parallel_edges_direction_and_properties() -> None:
    fixture = GraphFixture(nodes=[{"id": "a", "labels": ["A"]}, {"id": "b", "labels": ["B"]}], edges=[
        {"src": "a", "dst": "b", "edge_id": 0, "type": "R", "weight": 2},
        {"src": "a", "dst": "b", "edge_id": 1, "type": "R", "weight": 3},
    ])
    assert_post_graph(fixture_state(fixture), fixture)
    for edges in [fixture.edges[:1], [dict(edge, src=edge["dst"], dst=edge["src"]) for edge in fixture.edges]]:
        with pytest.raises(PoststateMismatch):
            assert_post_graph(fixture_state(replace(fixture, edges=edges)), fixture)


def test_label_effects_count_distinct_names_not_memberships() -> None:
    before = fixture_state(GraphFixture(nodes=[], edges=[]))
    after = fixture_state(GraphFixture(nodes=[{"id": 1, "labels": ["L"]}, {"id": 2, "labels": ["L"]}], edges=[]))
    assert effects_between(before, after) == MutationEffects(nodes_created=2, labels_added=1)


def seeded_graph(reverse):
    source=graphistry.nodes(pd.DataFrame({"id":["a","b"]}),"id").edges(pd.DataFrame({"src":["a"],"dst":["b"],"edge_id":["r"],"type":["R"]}),"src","dst",edge="edge_id")
    after=graphistry.nodes(pd.DataFrame({"id":["a","b","actual_fresh"]}),"id").edges(pd.DataFrame({"src":["b" if reverse else "a"],"dst":["a" if reverse else "b"],"edge_id":["r"],"type":["R"]}),"src","dst",edge="edge_id")
    before_fixture=GraphFixture(nodes=[{"id":"a"},{"id":"b"}],edges=[{"src":"a","dst":"b","edge_id":"r","type":"R"}])
    post_fixture=GraphFixture(nodes=[{"id":"a"},{"id":"b"},{"id":"expected_fresh"}],edges=before_fixture.edges)
    item=Scenario(key="seeded-create",feature_path="test",scenario="retained endpoints",cypher="CREATE ()",graph=before_fixture,expected=Expected(rows=[],post_graph=post_fixture,effects=MutationEffects(nodes_created=1)),gfql=None,tags=("mutation-no-return",))
    return source,after,item

def test_retained_edge_cannot_be_rewired_by_existing_identity_permutation(monkeypatch):
    source,after,item=seeded_graph(True)
    monkeypatch.setattr(source,"gfql",lambda *args,**kwargs:after)
    with pytest.raises(ExistingIdentityMismatch):
        execute_and_assert_mutation(source,item,engine="pandas")

def test_fresh_identity_renaming_remains_valid_with_existing_anchors(monkeypatch):
    source,after,item=seeded_graph(False)
    monkeypatch.setattr(source,"gfql",lambda *args,**kwargs:after)
    result=execute_and_assert_mutation(source,item,engine="pandas")
    assert result is after


def test_existing_node_labels_cannot_be_permuted_between_physical_ids(monkeypatch):
    source = graphistry.nodes(pd.DataFrame({"id": ["a", "b"], "label__A": [True, False], "label__B": [False, True]}), "id")
    after = graphistry.nodes(pd.DataFrame({"id": ["a", "b", "actual_fresh"], "label__A": [False, True, False], "label__B": [True, False, False]}), "id")
    pre = GraphFixture(nodes=[{"id": "a", "labels": ["A"]}, {"id": "b", "labels": ["B"]}], edges=[])
    post = GraphFixture(nodes=[*pre.nodes, {"id": "expected_fresh"}], edges=[])
    item = Scenario(key="existing-node-anchor", feature_path="test", scenario="physical node anchors", cypher="CREATE ()", graph=pre, expected=Expected(rows=[], post_graph=post, effects=MutationEffects(nodes_created=1)), gfql=None)
    monkeypatch.setattr(source, "gfql", lambda *args, **kwargs: after)
    with pytest.raises(PoststateMismatch):
        execute_and_assert_mutation(source, item, engine="pandas")


def _returned_graph() -> object:
    return _graph([{"id": "n0"}])


def test_returned_rows_are_compared_after_mutation_oracle() -> None:
    source = _graph([])
    source.gfql = lambda *args, **kwargs: _returned_graph()
    scenario = replace(
        _scenario(),
        tags=("mutation",),
        expected=replace(
            _scenario().expected,
            rows=[{"id": "n0"}],
            post_graph=GraphFixture(nodes=[{"id": "n0"}], edges=[]),
        ),
    )
    result = execute_and_assert_mutation(source, scenario, engine="pandas")

    assert _rows_from_result(result) == [{"id": "n0"}]
    assert _returned_rows_for_mutation(scenario, result) == [{"id": "n0"}]


def test_xfail_classifier_confirms_real_row_debt() -> None:
    source = _graph([])
    source.gfql = lambda *args, **kwargs: _returned_graph()
    scenario = replace(
        _scenario(),
        tags=("mutation",),
        expected=replace(
            _scenario().expected,
            rows=[{"id": "wrong"}],
            post_graph=GraphFixture(nodes=[{"id": "n0"}], edges=[]),
        ),
    )

    assert _classify_xfail_mutation_oracle(source, scenario, "pandas") == "debt"


def test_xfail_classifier_fails_stale_row_debt() -> None:
    source = _graph([])
    source.gfql = lambda *args, **kwargs: _returned_graph()
    scenario = replace(
        _scenario(),
        tags=("mutation",),
        expected=replace(
            _scenario().expected,
            rows=[{"id": "n0"}],
            post_graph=GraphFixture(nodes=[{"id": "n0"}], edges=[]),
        ),
    )

    assert _classify_xfail_mutation_oracle(source, scenario, "pandas") == "stale"


@pytest.mark.parametrize(
    "error",
    [
        PoststateMismatch,
        EffectMismatch,
        CallerMutation,
        ExistingIdentityMismatch,
    ],
)
def test_xfail_consumer_does_not_mask_mutation_assertions(
    monkeypatch, error
) -> None:
    scenario = replace(
        _scenario(),
        status="xfail",
        reason="historical row debt",
        tags=("mutation", "mutation-no-return"),
    )
    monkeypatch.setattr(
        "tests.cypher_tck.mutation_oracle.execute_and_assert_mutation",
        lambda *args, **kwargs: raise_error(error("mutation oracle rejected no-op")),
    )

    with pytest.raises(error):
        test_tck_runner.test_cypher_tck_scenario(scenario)


def raise_error(error):
    raise error


def test_wrong_returned_rows_fail_even_with_correct_poststate_and_effects() -> None:
    source = _graph([])
    source.gfql = lambda *args, **kwargs: _returned_graph()
    scenario = replace(
        _scenario(),
        tags=("mutation",),
        expected=replace(
            _scenario().expected,
            rows=[],
            post_graph=GraphFixture(nodes=[{"id": "n0"}], edges=[]),
        ),
    )

    result = execute_and_assert_mutation(source, scenario, engine="pandas")
    with pytest.raises(AssertionError):
        _assert_expected_rows(scenario, _returned_rows_for_mutation(scenario, result))


def test_genuine_mutation_no_return_normalizes_to_empty_rows() -> None:
    source = _graph([])
    source.gfql = lambda *args, **kwargs: _returned_graph()
    scenario = replace(
        _scenario(),
        expected=replace(
            _scenario().expected,
            post_graph=GraphFixture(nodes=[{"id": "n0"}], edges=[]),
        ),
    )

    result = execute_and_assert_mutation(source, scenario, engine="pandas")
    assert _returned_rows_for_mutation(scenario, result) == []


def test_xfail_runner_fails_before_masking_stale_row_debt(
    monkeypatch,
) -> None:
    scenario = replace(
        _scenario(),
        status="xfail",
        reason="historical row debt",
        tags=("mutation",),
        expected=replace(
            _scenario().expected,
            rows=[{"id": "n0"}],
            post_graph=GraphFixture(nodes=[{"id": "n0"}], edges=[]),
        ),
    )
    fail_calls = []

    def fail(message):
        fail_calls.append(message)
        raise RuntimeError(message)

    monkeypatch.setattr(
        "tests.cypher_tck.test_tck_runner._classify_xfail_mutation_oracle",
        lambda *args: "stale",
    )
    monkeypatch.setattr("pytest.fail", fail)
    monkeypatch.setattr(
        "pytest.xfail",
        lambda reason: fail_calls.append(("xfail", reason)),
    )

    with pytest.raises(RuntimeError):
        test_tck_runner.test_cypher_tck_scenario(scenario)

    assert fail_calls == [
        "test-mutation: mutation scenario passed expected rows; row debt is stale"
    ]


def test_node_companion_mutation_scope_excludes_relationship_promotions() -> None:
    from tests.cypher_tck.scenarios import SCENARIOS

    by_key = {scenario.key: scenario for scenario in SCENARIOS}
    node_keys = {f"create1-{number}" for number in range(1, 13)} | {
        "create6-1", "create6-2", "expr-graph3-1", "expr-graph3-2", "expr-graph3-3",
    }
    admitted = {
        scenario.key for scenario in SCENARIOS
        if scenario.status == "supported" and scenario.expected.post_graph is not None
    }
    assert admitted == node_keys
    for key in node_keys:
        expected = by_key[key].expected
        assert expected.effects is not None
        assert expected.post_graph.edges == []
        assert expected.effects.relationships_created == 0
    for key in ("create2-1", "create2-2", "create2-4", "create2-7", "create2-8",
                "create2-13", "create2-15", "expr-graph3-4", "expr-graph7-2", "expr-graph7-3"):
        assert by_key[key].status == "xfail"
        assert by_key[key].expected.post_graph is None
