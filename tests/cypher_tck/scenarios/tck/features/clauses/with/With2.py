from graphistry.compute import e_forward, e_undirected, n

from tests.cypher_tck.models import Expected, GraphFixture, Scenario

from tests.cypher_tck.scenarios.fixtures import (
    MATCH5_GRAPH,
    MATCH7_GRAPH_SINGLE,
    MATCH7_GRAPH_AB,
    MATCH7_GRAPH_ABC,
    MATCH7_GRAPH_REL,
    MATCH7_GRAPH_X,
    MATCH7_GRAPH_AB_X,
    MATCH7_GRAPH_LABELS,
    MATCH7_GRAPH_PLAYER_TEAM_BOTH,
    MATCH7_GRAPH_PLAYER_TEAM_SINGLE,
    MATCH7_GRAPH_PLAYER_TEAM_DIFF,
    WITH_ORDERBY4_GRAPH,
    BINARY_TREE_1_GRAPH,
    BINARY_TREE_2_GRAPH,
)


SCENARIOS = [
    Scenario(
        key="with2-1",
        feature_path="tck/features/clauses/with/With2.feature",
        scenario="[1] Forwarding a property to express a join",
        cypher="MATCH (a:Begin)\nWITH a.num AS property\nMATCH (b)\nWHERE b.id = property\nRETURN b",
        # Explicit fixture (issue #115). graph_fixture_from_create mis-modelled
        # the TCK setup `CREATE (a:End {num: 42, id: 0}), (:End {num: 3}),
        # (:Begin {num: a.id})` twice: it stringified the `a.id` property
        # reference instead of resolving it to 0, and it conflated the Cypher
        # `id` property with the synthetic node-identity column. Materialize
        # `num: 0` on the Begin node and keep `id` a real property; the
        # `__node__` identity column is `__`-prefixed so the direct-Cypher
        # node renderer treats it as internal and excludes it from output.
        graph=GraphFixture(
            nodes=[
                {"__node__": 1, "labels": ["End"], "num": 42, "id": 0},
                {"__node__": 2, "labels": ["End"], "num": 3},
                {"__node__": 3, "labels": ["Begin"], "num": 0},
            ],
            edges=[],
            node_id="__node__",
            node_columns=("__node__", "labels"),
        ),
        expected=Expected(
            rows=[
                {"b": "(:End {num: 42, id: 0})"},
            ],
        ),
        gfql=None,
        status="xfail",
        reason="WITH pipelines, joins, and row projections are not supported",
        tags=("with", "join", "xfail"),
    ),

    Scenario(
        key="with2-2",
        feature_path="tck/features/clauses/with/With2.feature",
        scenario="[2] Forwarding a nested map literal",
        cypher="WITH {name: {name2: 'baz'}} AS nestedMap\nRETURN nestedMap.name.name2",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(
            rows=[
                {"nestedMap.name.name2": "'baz'"},
            ],
        ),
        gfql=None,
        status="xfail",
        reason="WITH pipelines and map projections are not supported",
        tags=("with", "map", "projection", "xfail"),
    ),
]
