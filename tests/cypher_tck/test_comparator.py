from decimal import Decimal

from tests.cypher_tck.comparator import (
    compare_declared_order,
    compare_expected_error,
    compare_null_values,
    compare_numeric_values,
    compare_rows,
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


def test_compare_rows_unordered_multiset_round_trip_allows_reordered_rows() -> None:
    result = compare_rows(
        scenario_key="unit-row-pass",
        expected_rows=[{"x": 1}, {"x": 2}],
        actual_rows=[{"x": 2}, {"x": 1}],
        columns=("x",),
        ordered=False,
        unordered_mode="multiset",
        allow_lossy_numeric=True,
    )

    assert result.matched
    assert result.diagnostic == ""


def test_compare_rows_unordered_set_mode_ignores_duplicate_rows() -> None:
    result = compare_rows(
        scenario_key="unit-row-set-pass",
        expected_rows=[{"x": 1}, {"x": 1}],
        actual_rows=[{"x": 1}],
        columns=("x",),
        ordered=False,
        unordered_mode="set",
        allow_lossy_numeric=True,
    )

    assert result.matched


def test_compare_rows_unordered_set_mode_uses_cell_rules() -> None:
    result = compare_rows(
        scenario_key="unit-row-set-cell-rules",
        expected_rows=[{"x": None}],
        actual_rows=[{"x": None}],
        columns=("x",),
        ordered=False,
        unordered_mode="set",
    )

    assert not result.matched
    assert "context: mode=unordered-rows-set row=0 column='x'" in result.diagnostic


def test_compare_rows_unordered_multiset_mode_tracks_duplicate_rows() -> None:
    result = compare_rows(
        scenario_key="unit-row-multiset-fail",
        expected_rows=[{"x": 1}, {"x": 1}],
        actual_rows=[{"x": 1}],
        columns=("x",),
        ordered=False,
        unordered_mode="multiset",
        allow_lossy_numeric=True,
    )

    assert not result.matched
    assert "context: mode=unordered-rows-multiset row=1" in result.diagnostic
    assert "row cardinality differs" in result.diagnostic


def test_compare_rows_ordered_failure_anchors_cell_context() -> None:
    result = compare_rows(
        scenario_key="unit-row-fail",
        expected_rows=[{"x": 1}, {"x": 2}],
        actual_rows=[{"x": 1}, {"x": 3}],
        columns=("x",),
        ordered=True,
        allow_lossy_numeric=True,
    )

    assert not result.matched
    assert result.diagnostic.startswith("numeric comparison mismatch for scenario unit-row-fail")
    assert "context: mode=ordered-rows row=1 column='x'" in result.diagnostic
    assert "expected: 2" in result.diagnostic
    assert "actual: 3" in result.diagnostic


def test_compare_null_values_round_trip_is_configurable() -> None:
    assert compare_null_values(
        scenario_key="unit-null-pass",
        expected=None,
        actual=float("nan"),
        nulls_equal=True,
        row_index=0,
        column="n",
    ).matched


def test_compare_null_values_default_failure_is_anchored() -> None:
    result = compare_null_values(
        scenario_key="unit-null-fail",
        expected=None,
        actual=None,
        row_index=0,
        column="n",
    )

    assert not result.matched
    assert result.diagnostic.startswith("null comparison mismatch for scenario unit-null-fail")
    assert "context: row=0 column='n' nulls_equal=false" in result.diagnostic


def test_compare_numeric_values_round_trip_with_tolerance() -> None:
    result = compare_numeric_values(
        scenario_key="unit-numeric-pass",
        expected=Decimal("1.00"),
        actual=Decimal("1.01"),
        abs_tolerance=Decimal("0.02"),
        row_index=0,
        column="score",
    )

    assert result.matched


def test_compare_numeric_values_rejects_lossy_type_drift_by_default() -> None:
    result = compare_numeric_values(
        scenario_key="unit-numeric-fail",
        expected=1,
        actual=1.0,
        row_index=0,
        column="score",
    )

    assert not result.matched
    assert result.diagnostic.startswith("numeric comparison mismatch for scenario unit-numeric-fail")
    assert "context: row=0 column='score' allow_lossy=false" in result.diagnostic
    assert "numeric type drift is rejected" in result.diagnostic


def test_compare_declared_order_round_trip_enforces_declared_order() -> None:
    result = compare_declared_order(
        scenario_key="unit-order-pass",
        expected_rows=[{"x": 1}, {"x": 2}],
        actual_rows=[{"x": 1}, {"x": 2}],
        columns=("x",),
        order_declared=True,
        allow_lossy_numeric=True,
    )

    assert result.matched


def test_compare_declared_order_failure_flags_order_drift() -> None:
    result = compare_declared_order(
        scenario_key="unit-order-fail",
        expected_rows=[{"x": 1}, {"x": 2}],
        actual_rows=[{"x": 2}, {"x": 1}],
        columns=("x",),
        order_declared=True,
        allow_lossy_numeric=True,
    )

    assert not result.matched
    assert result.diagnostic.startswith("order comparison mismatch for scenario unit-order-fail")
    assert "context: mode=ordered-rows row=0 declared_order=true" in result.diagnostic
    assert "declared order was not preserved" in result.diagnostic


def test_compare_expected_error_round_trip_ignores_human_text() -> None:
    result = compare_expected_error(
        scenario_key="unit-error-pass",
        expected={
            "code": "E108",
            "category": "direct_cypher_promoted_only",
            "field": "return",
            "value": "b.score",
            "message": "old wording",
        },
        actual={
            "code": "E108",
            "category": "direct_cypher_promoted_only",
            "field": "return",
            "value": "b.score",
            "message": "new wording",
        },
    )

    assert result.matched


def test_compare_expected_error_failure_anchors_structural_field() -> None:
    result = compare_expected_error(
        scenario_key="unit-error-fail",
        expected={
            "code": "E108",
            "category": "direct_cypher_promoted_only",
            "field": "return",
            "value": "b.score",
        },
        actual={
            "code": "E109",
            "category": "direct_cypher_promoted_only",
            "field": "return",
            "value": "b.score",
        },
    )

    assert not result.matched
    assert result.diagnostic.startswith("expected error mismatch for scenario unit-error-fail")
    assert "context: field='code'" in result.diagnostic
    assert "expected: 'E108'" in result.diagnostic
    assert "actual: 'E109'" in result.diagnostic


def test_compare_expected_error_rejects_unstructured_text_inputs() -> None:
    result = compare_expected_error(
        scenario_key="unit-error-unstructured",
        expected="ValueError: old wording",
        actual="ValueError: old wording",
    )

    assert not result.matched
    assert result.diagnostic.startswith("expected error mismatch for scenario unit-error-unstructured")
    assert "context: field='code'" in result.diagnostic
    assert "requires a structured error code" in result.diagnostic
