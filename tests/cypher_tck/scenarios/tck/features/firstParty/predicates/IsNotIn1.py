from tests.cypher_tck.models import Expected, GraphFixture, Scenario


IS_NOT_IN_GRAPH = GraphFixture(
    nodes=[
        {
            "id": "keep",
            "labels": ["Account"],
            "kind": "human",
            "nullable": "set",
            "mixed": "one",
        },
        {
            "id": "drop",
            "labels": ["Account"],
            "kind": "bot",
            "nullable": None,
            "mixed": 2,
        },
        {
            "id": "other",
            "labels": ["Account"],
            "kind": "admin",
            "nullable": "other",
            "mixed": True,
        },
    ],
    edges=[],
    node_columns=("id", "labels", "kind", "nullable", "mixed"),
)

PENDING_REASON = (
    "pygraphistry#966 is still open; is_not_in() is not available on current "
    "pygraphistry master"
)

COMMON_TAGS = (
    "first-party",
    "predicate",
    "is-not-in",
    "pygraphistry-966",
    "not-yet-implemented",
)


SCENARIOS = [
    Scenario(
        key="firstparty-predicates-isnotin1-1",
        feature_path="tck/features/firstParty/predicates/IsNotIn1.feature",
        scenario="[1] is_not_in keeps values outside the rejected list",
        cypher="MATCH (n)\nWHERE n.kind NOT IN ['bot']\nRETURN n",
        graph=IS_NOT_IN_GRAPH,
        expected=Expected(node_ids=["keep", "other"]),
        gfql=None,
        status="skip",
        reason=PENDING_REASON,
        return_alias="n",
        tags=COMMON_TAGS + ("positive-match",),
    ),
    Scenario(
        key="firstparty-predicates-isnotin1-2",
        feature_path="tck/features/firstParty/predicates/IsNotIn1.feature",
        scenario="[2] is_not_in filters values inside the rejected list",
        cypher="MATCH (n)\nWHERE n.kind NOT IN ['human', 'admin']\nRETURN n",
        graph=IS_NOT_IN_GRAPH,
        expected=Expected(node_ids=["drop"]),
        gfql=None,
        status="skip",
        reason=PENDING_REASON,
        return_alias="n",
        tags=COMMON_TAGS + ("negative-match",),
    ),
    Scenario(
        key="firstparty-predicates-isnotin1-3",
        feature_path="tck/features/firstParty/predicates/IsNotIn1.feature",
        scenario="[3] is_not_in with an empty list keeps every value",
        cypher="MATCH (n)\nWHERE n.kind NOT IN []\nRETURN n",
        graph=IS_NOT_IN_GRAPH,
        expected=Expected(node_ids=["keep", "drop", "other"]),
        gfql=None,
        status="skip",
        reason=PENDING_REASON,
        return_alias="n",
        tags=COMMON_TAGS + ("empty-list",),
    ),
    Scenario(
        key="firstparty-predicates-isnotin1-4",
        feature_path="tck/features/firstParty/predicates/IsNotIn1.feature",
        scenario="[4] is_not_in mirrors is_in None handling",
        cypher="MATCH (n)\nWHERE n.nullable NOT IN [null]\nRETURN n",
        graph=IS_NOT_IN_GRAPH,
        expected=Expected(node_ids=["keep", "other"]),
        gfql=None,
        status="skip",
        reason=PENDING_REASON,
        return_alias="n",
        tags=COMMON_TAGS + ("none-handling",),
    ),
    Scenario(
        key="firstparty-predicates-isnotin1-5",
        feature_path="tck/features/firstParty/predicates/IsNotIn1.feature",
        scenario="[5] is_not_in accepts a mixed scalar list",
        cypher="MATCH (n)\nWHERE n.mixed NOT IN ['one', 2]\nRETURN n",
        graph=IS_NOT_IN_GRAPH,
        expected=Expected(node_ids=["other"]),
        gfql=None,
        status="skip",
        reason=PENDING_REASON,
        return_alias="n",
        tags=COMMON_TAGS + ("mixed-types",),
    ),
]
