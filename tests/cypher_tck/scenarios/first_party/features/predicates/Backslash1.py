from tests.cypher_tck.models import Expected, GraphFixture, Scenario


FEATURE_PATH = "first_party/features/predicates/Backslash1.feature"

BACKSLASH_GRAPH = GraphFixture(
    nodes=[
        {"id": "slash", "path": "a\\slash"},
        {"id": "plain", "path": "plain"},
        {"id": "other", "path": "different"},
    ],
    edges=[],
    node_columns=("id", "path"),
)

COMMON_TAGS = (
    "first-party",
    "predicate",
    "backslash",
    "cypher-string",
    "cypher-string-pure",
)


SCENARIOS = [
    Scenario(
        key="firstparty-predicates-backslash1-1",
        feature_path=FEATURE_PATH,
        scenario="[1] A decoded backslash literal matches the stored value",
        cypher="""MATCH (n)
WHERE n.path = 'a\\\\slash'
RETURN n.id AS id ORDER BY id""",
        graph=BACKSLASH_GRAPH,
        expected=Expected(rows=[{"id": "slash"}]),
        gfql=None,
        status="supported",
        tags=COMMON_TAGS + ("direct",),
    ),
    Scenario(
        key="firstparty-predicates-backslash1-2",
        feature_path=FEATURE_PATH,
        scenario="[2] NOT keeps only rows rejected by the backslash predicate",
        cypher="""MATCH (n)
WHERE NOT n.path = 'a\\\\slash'
RETURN n.id AS id ORDER BY id""",
        graph=BACKSLASH_GRAPH,
        expected=Expected(rows=[{"id": "other"}, {"id": "plain"}]),
        gfql=None,
        status="supported",
        tags=COMMON_TAGS + ("not",),
    ),
    Scenario(
        key="firstparty-predicates-backslash1-3",
        feature_path=FEATURE_PATH,
        scenario="[3] OR selects a backslash match and a nonmatching fallback",
        cypher="""MATCH (n)
WHERE n.path = 'no\\\\match' OR n.id = 'other'
RETURN n.id AS id ORDER BY id""",
        graph=BACKSLASH_GRAPH,
        expected=Expected(rows=[{"id": "other"}]),
        gfql=None,
        status="supported",
        tags=COMMON_TAGS + ("or",),
    ),
    Scenario(
        key="firstparty-predicates-backslash1-4",
        feature_path=FEATURE_PATH,
        scenario="[4] NOT over OR rejects the decoded backslash match",
        cypher="""MATCH (n)
WHERE NOT (n.path = 'a\\\\slash' OR n.id = 'missing')
RETURN n.id AS id ORDER BY id""",
        graph=BACKSLASH_GRAPH,
        expected=Expected(rows=[{"id": "other"}, {"id": "plain"}]),
        gfql=None,
        status="supported",
        tags=COMMON_TAGS + ("not-or",),
    ),
]
