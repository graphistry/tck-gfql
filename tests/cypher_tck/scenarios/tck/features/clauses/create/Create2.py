from dataclasses import replace

from tests.cypher_tck.models import Expected, GraphFixture, MutationEffects, Scenario
from tests.cypher_tck.parse_cypher import graph_fixture_from_create


SCENARIOS = [
    Scenario(
        key='create2-1',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[1] Create two nodes and a single relationship in a single pattern',
        cypher='CREATE ()-[:R]->()',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-2',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[2] Create two nodes and a single relationship in separate patterns',
        cypher='CREATE (a), (b),\n             (a)-[:R]->(b)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-3',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[3] Create two nodes and a single relationship in separate clauses',
        cypher='CREATE (a)\n      CREATE (b)\n      CREATE (a)-[:R]->(b)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-4',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[4] Create two nodes and a single relationship in the reverse direction',
        cypher='CREATE (:A)<-[:R]-(:B)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-5',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[5] Create a single relationship between two existing nodes',
        cypher='MATCH (x:X), (y:Y)\n      CREATE (x)-[:R]->(y)',
        graph=graph_fixture_from_create(
            """
            CREATE (:X)
                  CREATE (:Y)
            """
        ),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-6',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[6] Create a single relationship between two existing nodes in the reverse direction',
        cypher='MATCH (x:X), (y:Y)\n      CREATE (x)<-[:R]-(y)',
        graph=graph_fixture_from_create(
            """
            CREATE (:X)
                  CREATE (:Y)
            """
        ),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-7',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[7] Create a single node and a single self loop in a single pattern',
        cypher='CREATE (root)-[:LINK]->(root)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-8',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[8] Create a single node and a single self loop in separate patterns',
        cypher='CREATE (root),\n             (root)-[:LINK]->(root)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-9',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[9] Create a single node and a single self loop in separate clauses',
        cypher='CREATE (root)\n      CREATE (root)-[:LINK]->(root)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-10',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[10] Create a single self loop on an existing node',
        cypher='MATCH (root:Root)\n      CREATE (root)-[:LINK]->(root)',
        graph=graph_fixture_from_create(
            """
            CREATE (:Root)
            """
        ),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-11',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[11] Create a single relationship and an end node on an existing starting node',
        cypher='MATCH (x:Begin)\n      CREATE (x)-[:TYPE]->(:End)',
        graph=graph_fixture_from_create(
            """
            CREATE (:Begin)
            """
        ),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-12',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[12] Create a single relationship and a starting node on an existing end node',
        cypher='MATCH (x:End)\n      CREATE (:Begin)-[:TYPE]->(x)',
        graph=graph_fixture_from_create(
            """
            CREATE (:End)
            """
        ),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-13',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[13] Create a single relationship with a property',
        cypher='CREATE ()-[:R {num: 42}]->()',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-14',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[14] Create a single relationship with a property and return it',
        cypher='CREATE ()-[r:R {num: 42}]->()\n      RETURN r.num AS num',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(
            rows=[
            {'num': 42}
            ],
        ),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-15',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[15] Create a single relationship with two properties',
        cypher="CREATE ()-[:R {id: 12, name: 'foo'}]->()",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-16',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[16] Create a single relationship with two properties and return them',
        cypher="CREATE ()-[r:R {id: 12, name: 'foo'}]->()\n      RETURN r.id AS id, r.name AS name",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(
            rows=[
            {'id': 12, 'name': "'foo'"}
            ],
        ),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-17',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[17] Create a single relationship with null properties should not return those properties',
        cypher='CREATE ()-[r:X {id: 12, name: null}]->()\n      RETURN r.id, r.name AS name',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(
            rows=[
            {'r.id': 12, 'name': 'null'}
            ],
        ),
        gfql=None,
        status="xfail",
        reason='CREATE clause semantics are not supported',
        tags=('create', 'xfail'),
    ),

    Scenario(
        key='create2-18',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[18] Fail when creating a relationship without a type',
        cypher='CREATE ()-->()',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),

    Scenario(
        key='create2-19',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[19] Fail when creating a relationship without a direction',
        cypher='CREATE (a)-[:FOO]-(b)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),

    Scenario(
        key='create2-20',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[20] Fail when creating a relationship with two directions',
        cypher='CREATE (a)<-[:FOO]->(b)',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),

    Scenario(
        key='create2-21',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[21] Fail when creating a relationship with more than one type',
        cypher='CREATE ()-[:A|:B]->()',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),

    Scenario(
        key='create2-22',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[22] Fail when creating a variable-length relationship',
        cypher='CREATE ()-[:FOO*2]->()',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),

    Scenario(
        key='create2-23',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[23] Fail when creating a relationship that is already bound',
        cypher='MATCH ()-[r]->()\n      CREATE ()-[r]->()',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),

    Scenario(
        key='create2-24',
        feature_path='tck/features/clauses/create/Create2.feature',
        scenario='[24] Fail when creating a relationship using undefined variable in pattern',
        cypher='MATCH (a)\n      CREATE (a)-[:KNOWS]->(b {name: missing})\n      RETURN b',
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason='Compile-time validation is not supported',
        tags=('create', 'syntax-error', 'xfail'),
    ),
]


def _relationship_post(
    nodes: list[dict[str, object]], edges: list[dict[str, object]]
) -> GraphFixture:
    return GraphFixture(
        nodes=[{"__fixture_id__": index, **node} for index, node in enumerate(nodes)],
        edges=[{
            "__fixture_id_src__": edge.pop("src"),
            "__fixture_id_dst__": edge.pop("dst"),
            **edge,
        } for edge in edges],
        node_id="__fixture_id__",
        src="__fixture_id_src__",
        dst="__fixture_id_dst__",
        node_columns=("__fixture_id__",),
        edge_columns=("__fixture_id_src__", "__fixture_id_dst__", "type"),
    )


_CREATE2_POSTS = {
    "create2-1": _relationship_post(
        [{}, {}], [{"src": 0, "dst": 1, "type": "R"}],
    ),
    "create2-2": _relationship_post(
        [{}, {}], [{"src": 0, "dst": 1, "type": "R"}],
    ),
    "create2-4": _relationship_post(
        [{"labels": ["A"]}, {"labels": ["B"]}],
        [{"src": 1, "dst": 0, "type": "R"}],
    ),
    "create2-7": _relationship_post(
        [{}], [{"src": 0, "dst": 0, "type": "LINK"}],
    ),
    "create2-8": _relationship_post(
        [{}], [{"src": 0, "dst": 0, "type": "LINK"}],
    ),
    "create2-13": _relationship_post(
        [{}, {}], [{"src": 0, "dst": 1, "type": "R", "num": 42}],
    ),
    "create2-15": _relationship_post(
        [{}, {}], [{"src": 0, "dst": 1, "type": "R", "id": 12, "name": "foo"}],
    ),
}
_CREATE2_EFFECTS = {
    "create2-1": MutationEffects(nodes_created=2, relationships_created=1),
    "create2-2": MutationEffects(nodes_created=2, relationships_created=1),
    "create2-4": MutationEffects(nodes_created=2, relationships_created=1, labels_added=2),
    "create2-7": MutationEffects(nodes_created=1, relationships_created=1),
    "create2-8": MutationEffects(nodes_created=1, relationships_created=1),
    "create2-13": MutationEffects(nodes_created=2, relationships_created=1, properties_added=1),
    "create2-15": MutationEffects(nodes_created=2, relationships_created=1, properties_added=2),
}
for _index, _scenario in enumerate(SCENARIOS):
    if _scenario.key not in _CREATE2_POSTS:
        continue
    _tags = tuple(tag for tag in _scenario.tags if tag != "xfail") + (
        "cypher-string", "cypher-string-pure", "mutation", "mutation-no-return",
    )
    SCENARIOS[_index] = replace(
        _scenario, status="supported", reason=None, tags=_tags,
        expected=replace(
            _scenario.expected,
            post_graph=_CREATE2_POSTS[_scenario.key],
            effects=_CREATE2_EFFECTS[_scenario.key],
        ),
    )
