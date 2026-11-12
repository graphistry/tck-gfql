from graphistry.compute import e_forward, e_undirected, n

from dataclasses import replace

from tests.cypher_tck.models import Expected, GraphFixture, MutationEffects, Scenario
from tests.cypher_tck.parse_cypher import graph_fixture_from_create

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
        key='expr-graph3-1',
        feature_path='tck/features/expressions/graph/Graph3.feature',
        scenario='[1] Creating node without label',
        cypher='CREATE (node)\n      RETURN labels(node)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(
            rows=[
            {'labels(node)': '[]'}
            ],
        ),
        gfql=None,
        status="supported",
        reason=None,
        tags=('expr', 'graph', 'cypher-string'),
    ),

    Scenario(
        key='expr-graph3-2',
        feature_path='tck/features/expressions/graph/Graph3.feature',
        scenario='[2] Creating node with two labels',
        cypher="CREATE (node:Foo:Bar {name: 'Mattias'})\n      RETURN labels(node)",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(
            rows=[
            {'labels(node)': "['Foo', 'Bar']"}
            ],
        ),
        gfql=None,
        status="supported",
        reason=None,
        tags=('expr', 'graph', 'cypher-string'),
    ),

    Scenario(
        key='expr-graph3-3',
        feature_path='tck/features/expressions/graph/Graph3.feature',
        scenario='[3] Ignore space when creating node with labels',
        cypher='CREATE (node :Foo:Bar)\n      RETURN labels(node)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(
            rows=[
            {'labels(node)': "['Foo', 'Bar']"}
            ],
        ),
        gfql=None,
        status="supported",
        reason=None,
        tags=('expr', 'graph', 'cypher-string'),
    ),

    Scenario(
        key='expr-graph3-4',
        feature_path='tck/features/expressions/graph/Graph3.feature',
        scenario='[4] Create node with label in pattern',
        cypher='CREATE (n:Person)-[:OWNS]->(:Dog)\n      RETURN labels(n)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(
            rows=[
            {'labels(n)': "['Person']"}
            ],
        ),
        gfql=None,
        status="supported",
        reason=None,
        tags=('expr', 'graph', 'cypher-string'),
    ),

    Scenario(
        key='expr-graph3-5',
        feature_path='tck/features/expressions/graph/Graph3.feature',
        scenario='[5] Using `labels()` in return clauses',
        cypher='MATCH (n)\n      RETURN labels(n)',
        graph=graph_fixture_from_create(
            """
            CREATE ()
            """
        ),
        expected=Expected(
            rows=[
            {'labels(n)': '[]'}
            ],
        ),
        gfql=None,
        status="xfail",
        reason='Expression evaluation is not supported',
        tags=('expr', 'graph', 'meta-xfail', 'xfail'),
    ),

    Scenario(
        key='expr-graph3-6',
        feature_path='tck/features/expressions/graph/Graph3.feature',
        scenario='[6] `labels()` should accept type Any',
        cypher='MATCH (a)\n      WITH [a, 1] AS list\n      RETURN labels(list[0]) AS l',
        graph=graph_fixture_from_create(
            """
            CREATE (:Foo), (:Foo:Bar)
            """
        ),
        expected=Expected(
            rows=[
            {'l': "['Foo']"},
            {'l': "['Foo', 'Bar']"}
            ],
        ),
        gfql=None,
        status="xfail",
        reason='Expression evaluation is not supported',
        tags=('expr', 'graph', 'meta-xfail', 'xfail'),
    ),

    Scenario(
        key='expr-graph3-7',
        feature_path='tck/features/expressions/graph/Graph3.feature',
        scenario='[7] `labels()` on null node',
        cypher='OPTIONAL MATCH (n:DoesNotExist)\n      RETURN labels(n), labels(null)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(
            rows=[
            {'labels(n)': 'null', 'labels(null)': 'null'}
            ],
        ),
        gfql=None,
        status="xfail",
        reason='Expression evaluation is not supported',
        tags=('expr', 'graph', 'meta-xfail', 'xfail'),
    ),

    Scenario(
        key='expr-graph3-8',
        feature_path='tck/features/expressions/graph/Graph3.feature',
        scenario='[8] `labels()` failing on a path',
        cypher='MATCH p = (a)\n      RETURN labels(p) AS l',
        graph=graph_fixture_from_create(
            """
            CREATE (:Foo), (:Foo:Bar)
            """
        ),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('expr', 'graph', 'meta-xfail', 'syntax-error', 'xfail'),
    ),

    Scenario(
        key='expr-graph3-9',
        feature_path='tck/features/expressions/graph/Graph3.feature',
        scenario='[9] `labels()` failing on invalid arguments',
        cypher='MATCH (a)\n      WITH [a, 1] AS list\n      RETURN labels(list[1]) AS l',
        graph=graph_fixture_from_create(
            """
            CREATE (:Foo), (:Foo:Bar)
            """
        ),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Runtime error semantics are not supported',
        tags=('expr', 'graph', 'meta-xfail', 'runtime-error', 'xfail'),
    ),
]

_CREATE3_POST_NODES = [
    [{"__fixture_id__": 0}],
    [{"__fixture_id__": 0, "labels": ["Foo", "Bar"], "name": "Mattias"}],
    [{"__fixture_id__": 0, "labels": ["Foo", "Bar"]}],
    [
        {"__fixture_id__": 0, "labels": ["Person"]},
        {"__fixture_id__": 1, "labels": ["Dog"]},
    ],
]
_CREATE3_POST_EDGES = [[], [], [], [{"__fixture_src__": 0, "__fixture_dst__": 1, "type": "OWNS"}]]
_CREATE3_POST_EFFECTS = [
    MutationEffects(nodes_created=1),
    MutationEffects(nodes_created=1, properties_added=1, labels_added=2),
    MutationEffects(nodes_created=1, labels_added=2),
    MutationEffects(nodes_created=2, relationships_created=1, labels_added=2),
]
for _index, _scenario in enumerate(SCENARIOS):
    if _scenario.key not in {"expr-graph3-1", "expr-graph3-2", "expr-graph3-3", "expr-graph3-4"}:
        continue
    _offset = int(_scenario.key.rsplit("-", 1)[1]) - 1
    _post = GraphFixture(
        nodes=_CREATE3_POST_NODES[_offset],
        edges=_CREATE3_POST_EDGES[_offset],
        node_id="__fixture_id__",
        src="__fixture_src__",
        dst="__fixture_dst__",
        node_columns=("__fixture_id__",),
        edge_columns=("__fixture_src__", "__fixture_dst__"),
    )
    SCENARIOS[_index] = replace(
        _scenario,
        expected=replace(
            _scenario.expected,
            post_graph=_post,
            effects=_CREATE3_POST_EFFECTS[_offset],
        ),
        tags=_scenario.tags + ("mutation",),
    )
