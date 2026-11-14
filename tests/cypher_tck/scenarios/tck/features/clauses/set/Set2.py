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
        key='set2-1',
        feature_path='tck/features/clauses/set/Set2.feature',
        scenario='[1] Setting a node property to null removes the existing property',
        cypher='MATCH (n:A)\n      SET n.property1 = null\n      RETURN n',
        graph=graph_fixture_from_create(
            """
            CREATE (:A {property1: 23, property2: 46})
            """
        ),
        expected=Expected(
            rows=[
            {'n': '(:A {property2: 46})'}
            ],
        ),
        gfql=None,
        status="xfail",
        reason='SET clause semantics are not supported',
        tags=('set', 'xfail'),
    ),

    Scenario(
        key='set2-2',
        feature_path='tck/features/clauses/set/Set2.feature',
        scenario='[2] Setting a node property to null removes the existing property, but not before SET',
        cypher="MATCH (n)\n      WHERE n.name = 'Michael'\n      SET n.name = null\n      RETURN n",
        graph=graph_fixture_from_create(
            """
            CREATE (:A {name: 'Michael', age: 35})
            """
        ),
        expected=Expected(
            rows=[
            {'n': '(:A {age: 35})'}
            ],
        ),
        gfql=None,
        status="xfail",
        reason='SET clause semantics are not supported',
        tags=('set', 'xfail'),
    ),

    Scenario(
        key='set2-3',
        feature_path='tck/features/clauses/set/Set2.feature',
        scenario='[3] Setting a relationship property to null removes the existing property',
        cypher='MATCH ()-[r]->()\n      SET r.property1 = null\n      RETURN r',
        graph=graph_fixture_from_create(
            """
            CREATE ()-[:REL {property1: 12, property2: 24}]->()
            """
        ),
        expected=Expected(
            rows=[
            {'r': '[:REL {property2: 24}]'}
            ],
        ),
        gfql=None,
        status="xfail",
        reason='SET clause semantics are not supported',
        tags=('set', 'xfail'),
    ),
]

# Original Set2.feature @59edf2e1c17b845bf97c334ed06b2eb780950c13.
# SET p = null removes the matched node's property; the old value is read before it is removed.
# The postgraph keeps the setup's physical identity and drops only that property.
_SET2_REMOVED = {"set2-1": "property1", "set2-2": "name"}
for _index, _scenario in enumerate(SCENARIOS):
    if _scenario.key not in _SET2_REMOVED:
        continue
    _removed = _SET2_REMOVED[_scenario.key]
    _post = replace(
        _scenario.graph,
        nodes=[{k: v for k, v in node.items() if k != _removed} for node in _scenario.graph.nodes],
    )
    SCENARIOS[_index] = replace(
        _scenario,
        status="supported",
        reason=None,
        tags=("set", "cypher-string", "cypher-string-pure", "mutation"),
        expected=replace(
            _scenario.expected,
            post_graph=_post,
            effects=MutationEffects(properties_added=0, properties_removed=1),
        ),
    )
