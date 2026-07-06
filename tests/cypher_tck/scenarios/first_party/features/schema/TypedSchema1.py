from __future__ import annotations

from tests.cypher_tck.models import Expected, GraphFixture, Scenario


FEATURE_PATH = "first_party/features/schema/TypedSchema1.feature"

TYPED_SCHEMA_GRAPH = GraphFixture(
    nodes=[
        {
            "id": 1,
            "labels": ["Person", "Employee"],
            "name": "alice",
            "age": 30,
        },
        {
            "id": 2,
            "labels": ["Company"],
            "name": "acme",
            "age": None,
        },
        {
            "id": 3,
            "labels": ["Person"],
            "name": "bob",
            "age": 40,
        },
    ],
    edges=[
        {
            "src": 1,
            "dst": 2,
            "edge_id": "works-at",
            "type": "WORKS_AT",
            "since": 2024,
            "fee": None,
            "label__WORKS_AT": True,
            "label__CONTRACTS": False,
        },
        {
            "src": 2,
            "dst": 3,
            "edge_id": "contracts",
            "type": "CONTRACTS",
            "since": None,
            "fee": 100,
            "label__WORKS_AT": False,
            "label__CONTRACTS": True,
        },
    ],
    node_columns=("id", "labels", "name", "age"),
    edge_columns=(
        "src",
        "dst",
        "edge_id",
        "type",
        "since",
        "fee",
        "label__WORKS_AT",
        "label__CONTRACTS",
    ),
)

BASE_TAGS = (
    "first-party",
    "typed-schema",
    "experimental-surface",
    "cypher-string",
    "cypher-string-pure",
    "pygraphistry-1457",
    "pygraphistry-1337",
)

ERROR_TAGS = (*BASE_TAGS, "cypher-string-error")


def _row_scenario(
    *,
    key: str,
    scenario: str,
    cypher: str,
    rows: list[dict[str, object]],
    tags: tuple[str, ...],
    ordered: bool = False,
) -> Scenario:
    return Scenario(
        key=key,
        feature_path=FEATURE_PATH,
        scenario=scenario,
        cypher=cypher,
        graph=TYPED_SCHEMA_GRAPH,
        expected=Expected(rows=rows, ordered=ordered),
        gfql=None,
        status="supported",
        tags=(*BASE_TAGS, *tags),
    )


def _error_scenario(
    *,
    key: str,
    scenario: str,
    cypher: str,
    tags: tuple[str, ...],
) -> Scenario:
    return Scenario(
        key=key,
        feature_path=FEATURE_PATH,
        scenario=scenario,
        cypher=cypher,
        graph=TYPED_SCHEMA_GRAPH,
        expected=Expected(rows=None),
        gfql=None,
        status="supported",
        tags=(*ERROR_TAGS, *tags),
    )


SCENARIOS = [
    _row_scenario(
        key="firstparty-typed-schema1-1",
        scenario="Declare a GraphSchema with NodeType, EdgeType, and EdgeTopology",
        cypher=(
            "MATCH (p:Person) "
            "RETURN p.name AS name "
            "ORDER BY name ASC"
        ),
        rows=[{"name": "alice"}, {"name": "bob"}],
        ordered=True,
        tags=("basic-shape", "node-type", "edge-type", "edge-topology"),
    ),
    _row_scenario(
        key="firstparty-typed-schema1-2",
        scenario="Validate a bind(schema=...) happy path",
        cypher=(
            "MATCH (p:Person)-[:WORKS_AT]->(c:Company) "
            "RETURN p.name AS person, c.name AS company"
        ),
        rows=[{"person": "alice", "company": "acme"}],
        tags=("bind-schema", "validate-happy-path"),
    ),
    _row_scenario(
        key="firstparty-typed-schema1-3",
        scenario="GraphSchema strict false permits undeclared labels by default",
        cypher="MATCH (p:Unknown) RETURN p",
        rows=[],
        tags=("strict-false", "permissive-validation"),
    ),
    _error_scenario(
        key="firstparty-typed-schema1-4",
        scenario="GraphSchema strict true rejects undeclared labels",
        cypher="MATCH (p:Unknown) RETURN p",
        tags=("strict-true", "label-validation"),
    ),
    _row_scenario(
        key="firstparty-typed-schema1-5",
        scenario="NodeType labels admit declared alternate labels",
        cypher="MATCH (p:Employee) RETURN p.name AS name",
        rows=[{"name": "alice"}],
        tags=("label-validation", "node-type-labels"),
    ),
    _error_scenario(
        key="firstparty-typed-schema1-6",
        scenario="NodeType properties reject undeclared node properties",
        cypher=(
            "MATCH (p:Person)-[:WORKS_AT]->(c:Company) "
            "RETURN c.age AS age"
        ),
        tags=("property-validation", "node-properties"),
    ),
    _error_scenario(
        key="firstparty-typed-schema1-7",
        scenario="EdgeType properties reject properties from another edge type",
        cypher=(
            "MATCH (p:Person)-[:WORKS_AT {fee: 10}]->(c:Company) "
            "RETURN p.name AS name"
        ),
        tags=("property-validation", "edge-properties"),
    ),
    _error_scenario(
        key="firstparty-typed-schema1-8",
        scenario="EdgeType relationship names reject undeclared relationship types",
        cypher=(
            "MATCH (p:Person)-[:KNOWS]->(c:Company) "
            "RETURN p.name AS name"
        ),
        tags=("relationship-type-validation",),
    ),
    _error_scenario(
        key="firstparty-typed-schema1-9",
        scenario="EdgeTopology rejects declared edge type with mismatched endpoint labels",
        cypher=(
            "MATCH (p:Person)-[:WORKS_AT]->(other:Person) "
            "RETURN p.name AS name"
        ),
        tags=("topology-validation", "edge-topology"),
    ),
]
