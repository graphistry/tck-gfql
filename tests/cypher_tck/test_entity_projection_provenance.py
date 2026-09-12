"""Entity reconstruction uses projection provenance, not dotted-column guesses."""
import pandas as pd
import pytest

import graphistry
from tests.cypher_tck.test_tck_runner import _rows_from_result


@pytest.mark.parametrize("values", [[], ["same", "same"], [None, "same"]])
def test_explicit_unlabeled_entity_kind_renders_rows(values):
    g = graphistry.nodes(pd.DataFrame({"x.name": pd.Series(values, dtype="object")}), "id")
    g._cypher_entity_projection_kinds = {"x": "nodes"}
    out = _rows_from_result(g)
    assert len(out) == len(values)
    assert all(set(row) == {"x"} for row in out)
    if values == ["same", "same"]:
        assert out == [{"x": "({name: 'same'})"}, {"x": "({name: 'same'})"}]


def test_explicit_property_projection_does_not_use_stale_entity_metadata():
    g = graphistry.nodes(pd.DataFrame({"x.name": ["Alice"]}), "id")
    g._cypher_entity_projection_kinds = {}
    g._cypher_entity_projection_meta = {"x": {"table": "nodes"}}
    assert _rows_from_result(g) == [{"x.name": "Alice"}]


def test_older_product_entity_metadata_remains_supported():
    g = graphistry.nodes(pd.DataFrame({"x.name": ["Alice"]}), "id")
    g._cypher_entity_projection_meta = {"x": {"table": "nodes"}}
    assert _rows_from_result(g) == [{"x": "({name: 'Alice'})"}]
