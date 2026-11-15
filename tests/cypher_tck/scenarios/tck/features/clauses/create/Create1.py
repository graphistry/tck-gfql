from dataclasses import replace
from graphistry.compute import e_forward, e_undirected, n

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
        key='create1-1',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[1] Create a single node',
        cypher='CREATE ()',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create1-2',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[2] Create two nodes',
        cypher='CREATE (), ()',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create1-3',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[3] Create a single node with a label',
        cypher='CREATE (:Label)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create1-4',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[4] Create two nodes with same label',
        cypher='CREATE (:Label), (:Label)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create1-5',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[5] Create a single node with multiple labels',
        cypher='CREATE (:A:B:C:D)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create1-6',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[6] Create three nodes with multiple labels',
        cypher='CREATE (:B:A:D), (:B:C), (:D:E:B)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create1-7',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[7] Create a single node with a property',
        cypher='CREATE ({created: true})',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create1-8',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[8] Create a single node with a property and return it',
        cypher="CREATE (n {name: 'foo'})\n      RETURN n.name AS p",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(
            rows=[
            {'p': "'foo'"}
            ],
        ),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create1-9',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[9] Create a single node with two properties',
        cypher="CREATE (n {id: 12, name: 'foo'})",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create1-10',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[10] Create a single node with two properties and return them',
        cypher="CREATE (n {id: 12, name: 'foo'})\n      RETURN n.id AS id, n.name AS p",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(
            rows=[
            {'id': 12, 'p': "'foo'"}
            ],
        ),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create1-11',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[11] Create a single node with null properties should not return those properties',
        cypher='CREATE (n {id: 12, name: null})\n      RETURN n.id AS id, n.name AS p',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(
            rows=[
            {'id': 12, 'p': 'null'}
            ],
        ),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create1-12',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[12] CREATE does not lose precision on large integers',
        cypher='CREATE (p:TheLabel {id: 4611686018427387905})\n      RETURN p.id',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(
            rows=[
            {'p.id': 4611686018427387905}
            ],
        ),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create1-13',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[13] Fail when creating a node that is already bound',
        cypher='MATCH (a)\n      CREATE (a)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),

    Scenario(
        key='create1-14',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[14] Fail when creating a node with properties that is already bound',
        cypher="MATCH (a)\n      CREATE (a {name: 'foo'})\n      RETURN a",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),

    Scenario(
        key='create1-15',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[15] Fail when adding a new label predicate on a node that is already bound 1',
        cypher='CREATE (n:Foo)-[:T1]->(),\n             (n:Bar)-[:T2]->()',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),

    Scenario(
        key='create1-16',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[16] Fail when adding new label predicate on a node that is already bound 2',
        cypher='CREATE ()<-[:T2]-(n:Foo),\n             (n:Bar)<-[:T1]-()',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),

    Scenario(
        key='create1-17',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[17] Fail when adding new label predicate on a node that is already bound 3',
        cypher='CREATE (n:Foo)\n      CREATE (n:Bar)-[:OWNS]->(:Dog)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),

    Scenario(
        key='create1-18',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[18] Fail when adding new label predicate on a node that is already bound 4',
        cypher='CREATE (n {})\n      CREATE (n:Bar)-[:OWNS]->(:Dog)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),

    Scenario(
        key='create1-19',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[19] Fail when adding new label predicate on a node that is already bound 5',
        cypher='CREATE (n:Foo)\n      CREATE (n {})-[:OWNS]->(:Dog)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),

    Scenario(
        key='create1-20',
        feature_path='tck/features/clauses/create/Create1.feature',
        scenario='[20] Fail when creating a node using undefined variable in pattern',
        cypher='CREATE (b {name: missing})\n      RETURN b',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),
]

# Exact positive poststates/side effects from openCypher Create1.feature,
# source 59edf2e1c17b845bf97c334ed06b2eb780950c13. Physical fixture identity
# deliberately differs from the user property `id`.
_CREATE_POST_NODES = {
    1: [{}],
    2: [{}, {}],
    3: [{"labels": ["Label"]}],
    4: [{"labels": ["Label"]}, {"labels": ["Label"]}],
    5: [{"labels": ["A", "B", "C", "D"]}],
    6: [{"labels": ["B", "A", "D"]}, {"labels": ["B", "C"]}, {"labels": ["D", "E", "B"]}],
    7: [{"created": True}],
    8: [{"name": "foo"}],
    9: [{"id": 12, "name": "foo"}],
    10: [{"id": 12, "name": "foo"}],
    11: [{"id": 12}],
    12: [{"id": 4611686018427387905, "labels": ["TheLabel"]}],
}
# These are original TCK +labels counters (distinct label names, not node memberships).
_CREATE_EFFECTS = {
    1: MutationEffects(nodes_created=1),
    2: MutationEffects(nodes_created=2),
    3: MutationEffects(nodes_created=1, labels_added=1),
    4: MutationEffects(nodes_created=2, labels_added=1),
    5: MutationEffects(nodes_created=1, labels_added=4),
    6: MutationEffects(nodes_created=3, labels_added=5),
    7: MutationEffects(nodes_created=1, properties_added=1),
    8: MutationEffects(nodes_created=1, properties_added=1),
    9: MutationEffects(nodes_created=1, properties_added=2),
    10: MutationEffects(nodes_created=1, properties_added=2),
    11: MutationEffects(nodes_created=1, properties_added=1),
    12: MutationEffects(nodes_created=1, properties_added=1, labels_added=1),
}
for _index, _scenario in enumerate(SCENARIOS):
    _number = int(_scenario.key.split("-")[1])
    if _number not in _CREATE_POST_NODES:
        continue
    _post = GraphFixture(
        nodes=[{"__fixture_id__": i, **node} for i, node in enumerate(_CREATE_POST_NODES[_number])],
        edges=[], node_id="__fixture_id__", node_columns=("__fixture_id__",),
    )
    _tags = tuple(tag for tag in _scenario.tags if tag != "xfail") + ("cypher-string", "cypher-string-pure", "mutation")
    if _number in {1, 2, 3, 4, 5, 6, 7, 9}:
        _tags += ("mutation-no-return",)
    SCENARIOS[_index] = replace(
        _scenario, status="supported", reason=None, tags=_tags,
        expected=replace(_scenario.expected, post_graph=_post, effects=_CREATE_EFFECTS[_number]),
    )
