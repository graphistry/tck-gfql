from decimal import Decimal

from tests.cypher_tck.comparator import (
    normalize_diagnostic_value,
    render_expected_error_mismatch,
    render_row_mismatch,
)


def test_normalize_diagnostic_value_renders_nulls_and_numeric_values() -> None:
    assert normalize_diagnostic_value(None) == "null"
    assert normalize_diagnostic_value(float("nan")) == "null"
    assert normalize_diagnostic_value(1.0) == "1"
    assert normalize_diagnostic_value(1000.0) == "1000"
    assert normalize_diagnostic_value(Decimal("1.2300")) == "1.23"
    assert normalize_diagnostic_value({"b": [2.0], "a": None}) == {
        "a": "null",
        "b": ["2"],
    }


def test_render_unordered_row_mismatch_summarizes_row_deltas() -> None:
    message = render_row_mismatch(
        scenario_key="unit-unordered",
        expected_rows=[{"x": 1, "y": None}, {"x": 2, "y": "a"}],
        actual_rows=[{"x": 2.0, "y": "a"}, {"x": 3, "y": None}],
        expected_columns=("x", "y"),
        ordered=False,
    )

    assert message.startswith("unordered row mismatch for scenario unit-unordered")
    assert "row_count: expected=2 actual=2" in message
    assert "x=1|y=null" in message
    assert "x=3|y=null" in message


def test_render_ordered_row_mismatch_reports_first_order_drift() -> None:
    message = render_row_mismatch(
        scenario_key="unit-ordered",
        expected_rows=[{"x": 1}, {"x": 2}],
        actual_rows=[{"x": 2}, {"x": 1}],
        expected_columns=("x",),
        ordered=True,
    )

    assert message.startswith("ordered row mismatch for scenario unit-ordered")
    assert "first_ordered_mismatch_index: 0" in message
    assert "expected_only:" in message
    assert "actual_only:" in message


def test_render_expected_error_mismatch_includes_expected_and_actual_text() -> None:
    message = render_expected_error_mismatch(
        scenario_key="unit-error",
        expected="GFQLValidationError",
        actual="ValueError: bad literal",
    )

    assert message == (
        "expected error mismatch for scenario unit-error\n"
        "expected: 'GFQLValidationError'\n"
        "actual: 'ValueError: bad literal'"
    )
