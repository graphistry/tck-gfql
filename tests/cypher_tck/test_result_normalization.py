"""Preserve Cypher list/scalar distinctions across dataframe adapters."""
from types import SimpleNamespace

import numpy as np
import pytest

from tests.cypher_tck.test_tck_runner import (
    _normalize_row_value, _normalize_numeric_container_row_value, _rows_from_result,
)


@pytest.mark.parametrize("value, expected", [
    (np.array([], dtype=object), "[]"),
    (np.array([1]), "[1]"),
    (np.array([1, 2, 3]), "[1, 2, 3]"),
    (np.array([[1], [2]]), "[[1], [2]]"),
    (np.array([None], dtype=object), "[null]"),
    (np.array([True]), "[true]"),
    (np.array(["x"]), "['x']"),
    (np.array(1), 1),
    (np.int64(1), 1),
])
def test_numpy_list_and_scalar_distinction(value, expected):
    assert _normalize_row_value(value) == expected


@pytest.mark.parametrize("values, expected", [
    ([], "[]"),
    ([1], "[1]"),
    ([1, 2, 3], "[1, 2, 3]"),
    ([None, 1], "[null, 1]"),
    ([[1], [], [2, 3]], "[[1], [], [2, 3]]"),
])
def test_polars_list_cell_result_adapter(values, expected):
    pl = pytest.importorskip("polars")
    frame = pl.DataFrame({"value": [values]})
    native = frame.to_dicts()[0]["value"]
    adapted = _rows_from_result(SimpleNamespace(_nodes=frame))[0]["value"]
    assert _normalize_row_value(native) == expected
    assert _normalize_row_value(adapted) == expected


def test_nullable_large_integer_list_preserves_precision():
    pl = pytest.importorskip("polars")
    values = [None, 2**63 + 1, 2**63 + 2]
    frame = pl.DataFrame({"value": pl.Series([values], dtype=pl.List(pl.UInt64))})
    assert _rows_from_result(SimpleNamespace(_nodes=frame)) == [{"value": values}]


def test_numeric_container_equivalence_preserves_array_shape():
    normalized = _normalize_numeric_container_row_value(np.array([-0.000001]))
    assert normalized == ["__tck_numeric__:-0.000001"]
    assert _normalize_numeric_container_row_value(np.array([])) == []
