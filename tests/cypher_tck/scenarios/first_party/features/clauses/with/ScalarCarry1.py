"""A carried scalar stays attached to its path through a later MATCH (#2252)."""

from tests.cypher_tck.models import Expected, GraphFixture, Scenario


FEATURE_PATH = "first_party/features/clauses/with/ScalarCarry1.feature"

GRAPH = GraphFixture(
    nodes=[
        {"id": "a1", "labels": ["A"], "score": None},
        {"id": "a2", "labels": ["A"], "score": None},
        {"id": "b1", "labels": ["B"], "score": 10},
        {"id": "b2", "labels": ["B"], "score": 20},
        {"id": "c1", "labels": ["C"], "score": None},
        {"id": "c2", "labels": ["C"], "score": None},
    ],
    edges=[
        {"src": "a1", "dst": "b1", "edge_id": "r1", "type": "R", "weight": None},
        {"src": "a2", "dst": "b2", "edge_id": "r2", "type": "R", "weight": None},
        {"src": "b1", "dst": "c1", "edge_id": "s1", "type": "S", "weight": 10},
        {"src": "b2", "dst": "c1", "edge_id": "s2", "type": "S", "weight": 20},
    ],
    node_columns=("id", "labels", "score"),
    edge_columns=("src", "dst", "edge_id", "type", "weight"),
)

TAGS = (
    "first-party",
    "cypher-string",
    "cypher-string-pure",
    "with-reentry",
    "scalar-carry",
    "pygraphistry-2252",
)

PREFIX = "MATCH (a:A)-[:R]->(b:B) WITH b, b.score AS property "
SUFFIX = "RETURN property, count(DISTINCT c.id) AS n ORDER BY property"

SCENARIOS = [
    Scenario(
        key="firstparty-clauses-with-scalarcarry1-1",
        feature_path=FEATURE_PATH,
        scenario="[1] Convergent destination retains both path-scoped scalar groups",
        cypher=PREFIX + "MATCH (b)-[:S]->(c:C) " + SUFFIX,
        graph=GRAPH,
        expected=Expected(rows=[{"property": 10, "n": 1}, {"property": 20, "n": 1}], ordered=True),
        gfql=None,
        tags=TAGS + ("positive",),
    ),
    Scenario(
        key="firstparty-clauses-with-scalarcarry1-2",
        feature_path=FEATURE_PATH,
        scenario="[2] Edge filter rejects only the other scalar group",
        cypher=PREFIX + "MATCH (b)-[:S {weight: 10}]->(c:C) " + SUFFIX,
        graph=GRAPH,
        expected=Expected(rows=[{"property": 10, "n": 1}], ordered=True),
        gfql=None,
        tags=TAGS + ("partial-rejection",),
    ),
    Scenario(
        key="firstparty-clauses-with-scalarcarry1-3",
        feature_path=FEATURE_PATH,
        scenario="[3] Rejected destination paths yield no scalar groups",
        cypher=PREFIX + "MATCH (b)-[:S {weight: 99}]->(c:C) " + SUFFIX,
        graph=GRAPH,
        expected=Expected(rows=[]),
        gfql=None,
        tags=TAGS + ("empty",),
    ),
]
