from __future__ import annotations

import graphistry
import pytest

from graphistry.compute.exceptions import ErrorCode, GFQLValidationError
from graphistry.schema import EdgeTopology, EdgeType, GraphSchema, NodeType

from tests.cypher_tck.models import Scenario
from tests.cypher_tck.scenarios import SCENARIOS
from tests.cypher_tck.test_tck_runner import _build_graph
from tests.cypher_tck.typed_schema_support import (
    bind_schema_for_scenario,
    is_typed_schema_scenario,
    make_typed_schema,
    schema_strict_for_scenario,
    validate_typed_schema_scenario,
)


TYPED_SCHEMA_CASE_TAG_BY_KEY = {
    "firstparty-typed-schema1-1": "basic-shape",
    "firstparty-typed-schema1-2": "bind-schema",
    "firstparty-typed-schema1-3": "strict-false",
    "firstparty-typed-schema1-4": "strict-true",
    "firstparty-typed-schema1-5": "node-type-labels",
    "firstparty-typed-schema1-6": "node-properties",
    "firstparty-typed-schema1-7": "edge-properties",
    "firstparty-typed-schema1-8": "relationship-type-validation",
    "firstparty-typed-schema1-9": "topology-validation",
}

ERROR_CONTEXT_BY_KEY = {
    "firstparty-typed-schema1-4": {"label": "Unknown"},
    "firstparty-typed-schema1-6": {"property": "age", "entity_kind": "node"},
    "firstparty-typed-schema1-7": {"property": "fee", "entity_kind": "edge"},
    "firstparty-typed-schema1-8": {"relationship_type": "KNOWS"},
    "firstparty-typed-schema1-9": {
        "relationship_types": ("WORKS_AT",),
        "source_labels": ("Person",),
        "destination_labels": ("Person",),
    },
}


def _typed_schema_scenarios() -> dict[str, Scenario]:
    return {
        scenario.key: scenario
        for scenario in SCENARIOS
        if scenario.key in TYPED_SCHEMA_CASE_TAG_BY_KEY
    }


def test_typed_schema_public_imports_are_available() -> None:
    assert graphistry.NodeType is NodeType
    assert graphistry.EdgeType is EdgeType
    assert graphistry.GraphSchema is GraphSchema
    assert graphistry.EdgeTopology is EdgeTopology


def test_typed_schema_first_party_smoke_inventory() -> None:
    scenarios = _typed_schema_scenarios()

    assert set(scenarios) == set(TYPED_SCHEMA_CASE_TAG_BY_KEY)

    for key, case_tag in TYPED_SCHEMA_CASE_TAG_BY_KEY.items():
        scenario = scenarios[key]
        assert scenario.status == "supported"
        assert scenario.gfql is None
        assert scenario.reason is None
        assert scenario.feature_path == "first_party/features/schema/TypedSchema1.feature"
        assert "first-party" in scenario.tags
        assert "typed-schema" in scenario.tags
        assert "experimental-surface" in scenario.tags
        assert "cypher-string" in scenario.tags
        assert "pygraphistry-1457" in scenario.tags
        assert "pygraphistry-1337" in scenario.tags
        assert case_tag in scenario.tags
        assert is_typed_schema_scenario(scenario)


def test_typed_schema_basic_shape_exports_catalog_metadata() -> None:
    schema = make_typed_schema(strict=False)
    catalog = schema.to_catalog()
    topology = schema.edge_types[0].topology

    assert isinstance(schema.node_types[0], NodeType)
    assert isinstance(schema.edge_types[0], EdgeType)
    assert isinstance(topology, EdgeTopology)
    assert topology.relationship_type == "WORKS_AT"
    assert topology.source_labels == frozenset({"Person", "Employee"})
    assert topology.destination_labels == frozenset({"Company"})
    assert catalog.metadata["strict"] is False
    assert catalog.metadata["node_types"] == ("Person", "Company")
    assert catalog.metadata["edge_types"] == ("WORKS_AT", "CONTRACTS")
    assert catalog.metadata["edge_topologies"][0] == {
        "relationship_type": "WORKS_AT",
        "source_labels": ("Employee", "Person"),
        "destination_labels": ("Company",),
    }
    assert catalog.metadata["node_columns_by_label"]["Employee"] == (
        "age",
        "id",
        "label__Employee",
        "label__Person",
        "name",
    )


def test_typed_schema_success_scenarios_validate_and_execute() -> None:
    scenarios = _typed_schema_scenarios()

    for key in (
        "firstparty-typed-schema1-1",
        "firstparty-typed-schema1-2",
        "firstparty-typed-schema1-3",
        "firstparty-typed-schema1-5",
    ):
        scenario = scenarios[key]
        graph = bind_schema_for_scenario(_build_graph(scenario.graph), scenario)
        report = validate_typed_schema_scenario(graph, scenario)
        result = graph.gfql(scenario.cypher, params=scenario.params, engine="pandas")

        assert report["ok"] is True
        assert result._nodes is not None
        assert schema_strict_for_scenario(scenario) is (key != "firstparty-typed-schema1-3")


@pytest.mark.parametrize("key", sorted(ERROR_CONTEXT_BY_KEY))
def test_typed_schema_error_scenarios_raise_structured_validation(key: str) -> None:
    scenario = _typed_schema_scenarios()[key]
    graph = bind_schema_for_scenario(_build_graph(scenario.graph), scenario)

    with pytest.raises(GFQLValidationError) as exc_info:
        validate_typed_schema_scenario(graph, scenario)

    err = exc_info.value
    assert err.code == ErrorCode.E301
    for field, value in ERROR_CONTEXT_BY_KEY[key].items():
        assert err.context[field] == value
