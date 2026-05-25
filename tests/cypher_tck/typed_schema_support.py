from __future__ import annotations

from typing import Any

from tests.cypher_tck.models import Scenario


TYPED_SCHEMA_TAG = "typed-schema"
STRICT_FALSE_SCHEMA_KEYS = frozenset({"firstparty-typed-schema1-3"})


def is_typed_schema_scenario(scenario: Scenario) -> bool:
    return TYPED_SCHEMA_TAG in scenario.tags


def make_typed_schema(*, strict: bool = True) -> Any:
    from graphistry.schema import EdgeType, GraphSchema, NodeType

    person = NodeType(
        "Person",
        {"id": int, "name": str, "age": int},
        labels=("Person", "Employee"),
    )
    company = NodeType("Company", {"id": int, "name": str})
    works_at = EdgeType(
        "WORKS_AT",
        source=person,
        destination=company,
        properties={"since": int},
    )
    contracts = EdgeType(
        "CONTRACTS",
        source=company,
        destination=person,
        properties={"fee": int},
    )
    return GraphSchema(
        node_types=[person, company],
        edge_types=[works_at, contracts],
        strict=strict,
        node_id_column="id",
        edge_source_column="src",
        edge_destination_column="dst",
    )


def schema_strict_for_scenario(scenario: Scenario) -> bool:
    return scenario.key not in STRICT_FALSE_SCHEMA_KEYS


def bind_schema_for_scenario(graph: Any, scenario: Scenario) -> Any:
    return graph.bind(schema=make_typed_schema(strict=schema_strict_for_scenario(scenario)))


def validate_typed_schema_scenario(graph: Any, scenario: Scenario) -> dict[str, Any]:
    return graph.gfql_validate(
        scenario.cypher,
        params=scenario.params,
        strict=None,
    )
