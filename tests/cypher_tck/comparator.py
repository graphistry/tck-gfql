from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from math import isfinite, isnan
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class ComparisonResult:
    matched: bool
    diagnostic: str = ""


def _is_nullish(value: object) -> bool:
    if value is None:
        return True
    if type(value).__name__ in {"NAType", "NaTType"}:
        return True
    if isinstance(value, float):
        return isnan(value)
    return False


def _is_numeric(value: object) -> bool:
    return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)


def _decimal_from_numeric(value: object) -> Decimal:
    if isinstance(value, float) and not isfinite(value):
        raise InvalidOperation
    return Decimal(str(value))


def normalize_diagnostic_value(value: object) -> object:
    if hasattr(value, "item") and not isinstance(value, (str, bytes, list, tuple, dict)):
        try:
            value = value.item()
        except Exception:
            pass

    if _is_nullish(value):
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if _is_numeric(value):
        try:
            return format(_decimal_from_numeric(value).normalize(), "f")
        except InvalidOperation:
            return repr(value)
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, (list, tuple)):
        return [normalize_diagnostic_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): normalize_diagnostic_value(value[key])
            for key in sorted(value, key=str)
        }
    return repr(value)


def _format_value(value: object) -> str:
    normalized = normalize_diagnostic_value(value)
    if isinstance(normalized, (list, dict)):
        return repr(normalized)
    return str(normalized)


def _row_key(row: Mapping[str, Any], columns: Sequence[str]) -> str:
    return "|".join(f"{column}={_format_value(row.get(column))}" for column in columns)


def _counter_delta(left: Counter[str], right: Counter[str]) -> List[str]:
    delta: List[str] = []
    for key in sorted(set(left) | set(right)):
        count = left[key] - right[key]
        if count > 0:
            suffix = f" x{count}" if count > 1 else ""
            delta.append(f"{key}{suffix}")
    return delta


def _context_text(context: Mapping[str, object]) -> str:
    parts = []
    for key, value in context.items():
        rendered = str(value) if key == "mode" else _format_value(value)
        parts.append(f"{key}={rendered}")
    return " ".join(parts)


def _anchored_diagnostic(
    *,
    kind: str,
    scenario_key: str,
    context: Mapping[str, object],
    expected: object,
    actual: object,
    note: Optional[str] = None,
) -> str:
    lines = [
        f"{kind} mismatch for scenario {scenario_key}",
        f"context: {_context_text(context)}",
        f"expected: {_format_value(expected)}",
        f"actual: {_format_value(actual)}",
    ]
    if note is not None:
        lines.append(f"note: {note}")
    return "\n".join(lines)


def compare_null_values(
    *,
    scenario_key: str,
    expected: object,
    actual: object,
    nulls_equal: bool = False,
    row_index: Optional[int] = None,
    column: Optional[str] = None,
) -> ComparisonResult:
    expected_null = _is_nullish(expected)
    actual_null = _is_nullish(actual)
    if not expected_null and not actual_null:
        return ComparisonResult(True)
    if expected_null and actual_null and nulls_equal:
        return ComparisonResult(True)
    return ComparisonResult(
        False,
        _anchored_diagnostic(
            kind="null comparison",
            scenario_key=scenario_key,
            context={
                "row": "<none>" if row_index is None else row_index,
                "column": "<none>" if column is None else column,
                "nulls_equal": nulls_equal,
            },
            expected=expected,
            actual=actual,
            note="null equality is configurable and defaults to false",
        ),
    )


def compare_numeric_values(
    *,
    scenario_key: str,
    expected: object,
    actual: object,
    abs_tolerance: object = Decimal("0"),
    rel_tolerance: object = Decimal("0"),
    allow_lossy: bool = False,
    row_index: Optional[int] = None,
    column: Optional[str] = None,
) -> ComparisonResult:
    context = {
        "row": "<none>" if row_index is None else row_index,
        "column": "<none>" if column is None else column,
        "allow_lossy": allow_lossy,
    }
    if not _is_numeric(expected) or not _is_numeric(actual):
        return ComparisonResult(
            False,
            _anchored_diagnostic(
                kind="numeric comparison",
                scenario_key=scenario_key,
                context=context,
                expected=expected,
                actual=actual,
                note="both values must be numeric",
            ),
        )

    try:
        expected_decimal = _decimal_from_numeric(expected)
        actual_decimal = _decimal_from_numeric(actual)
        abs_decimal = _decimal_from_numeric(abs_tolerance)
        rel_decimal = _decimal_from_numeric(rel_tolerance)
    except InvalidOperation:
        return ComparisonResult(
            False,
            _anchored_diagnostic(
                kind="numeric comparison",
                scenario_key=scenario_key,
                context=context,
                expected=expected,
                actual=actual,
                note="numeric value cannot be converted losslessly for comparison",
            ),
        )

    tolerance_enabled = abs_decimal != 0 or rel_decimal != 0
    if type(expected) is not type(actual) and not allow_lossy and not tolerance_enabled:
        return ComparisonResult(
            False,
            _anchored_diagnostic(
                kind="numeric comparison",
                scenario_key=scenario_key,
                context=context,
                expected=expected,
                actual=actual,
                note="numeric type drift is rejected unless tolerance or allow_lossy is set",
            ),
        )

    diff = abs(expected_decimal - actual_decimal)
    rel_limit = rel_decimal * max(abs(expected_decimal), abs(actual_decimal))
    limit = max(abs_decimal, rel_limit)
    if diff <= limit:
        return ComparisonResult(True)
    return ComparisonResult(
        False,
        _anchored_diagnostic(
            kind="numeric comparison",
            scenario_key=scenario_key,
            context={
                "row": "<none>" if row_index is None else row_index,
                "column": "<none>" if column is None else column,
                "abs_tolerance": abs_decimal,
                "rel_tolerance": rel_decimal,
            },
            expected=expected,
            actual=actual,
            note=f"difference {_format_value(diff)} exceeds tolerance {_format_value(limit)}",
        ),
    )


def _row_columns(
    expected_rows: Sequence[Mapping[str, Any]],
    actual_rows: Sequence[Mapping[str, Any]],
    columns: Optional[Iterable[str]],
) -> Tuple[str, ...]:
    if columns is not None:
        return tuple(columns)
    keys = set()
    for row in tuple(expected_rows) + tuple(actual_rows):
        keys.update(str(key) for key in row.keys())
    return tuple(sorted(keys))


def _compare_cell_values(
    *,
    scenario_key: str,
    expected: object,
    actual: object,
    nulls_equal: bool,
    allow_lossy_numeric: bool,
    numeric_abs_tolerance: object,
    numeric_rel_tolerance: object,
    mode: str,
    row_index: int,
    column: str,
) -> ComparisonResult:
    if _is_nullish(expected) or _is_nullish(actual):
        result = compare_null_values(
            scenario_key=scenario_key,
            expected=expected,
            actual=actual,
            nulls_equal=nulls_equal,
            row_index=row_index,
            column=column,
        )
        if result.matched:
            return result
        return ComparisonResult(
            False,
            result.diagnostic.replace("context: ", f"context: mode={mode} ", 1),
        )

    if _is_numeric(expected) or _is_numeric(actual):
        result = compare_numeric_values(
            scenario_key=scenario_key,
            expected=expected,
            actual=actual,
            abs_tolerance=numeric_abs_tolerance,
            rel_tolerance=numeric_rel_tolerance,
            allow_lossy=allow_lossy_numeric,
            row_index=row_index,
            column=column,
        )
        if result.matched:
            return result
        return ComparisonResult(
            False,
            result.diagnostic.replace("context: ", f"context: mode={mode} ", 1),
        )

    if expected == actual:
        return ComparisonResult(True)
    return ComparisonResult(
        False,
        _anchored_diagnostic(
            kind="cell comparison",
            scenario_key=scenario_key,
            context={"mode": mode, "row": row_index, "column": column},
            expected=expected,
            actual=actual,
        ),
    )


def _rows_equal(
    *,
    scenario_key: str,
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    columns: Sequence[str],
    nulls_equal: bool,
    allow_lossy_numeric: bool,
    numeric_abs_tolerance: object,
    numeric_rel_tolerance: object,
    mode: str,
    row_index: int,
) -> ComparisonResult:
    for column in columns:
        if column not in expected or column not in actual:
            return ComparisonResult(
                False,
                _anchored_diagnostic(
                    kind="row column",
                    scenario_key=scenario_key,
                    context={"mode": mode, "row": row_index, "column": column},
                    expected="<present>" if column in expected else "<missing>",
                    actual="<present>" if column in actual else "<missing>",
                ),
            )
        result = _compare_cell_values(
            scenario_key=scenario_key,
            expected=expected[column],
            actual=actual[column],
            nulls_equal=nulls_equal,
            allow_lossy_numeric=allow_lossy_numeric,
            numeric_abs_tolerance=numeric_abs_tolerance,
            numeric_rel_tolerance=numeric_rel_tolerance,
            mode=mode,
            row_index=row_index,
            column=column,
        )
        if not result.matched:
            return result
    return ComparisonResult(True)


def compare_rows(
    *,
    scenario_key: str,
    expected_rows: Sequence[Mapping[str, Any]],
    actual_rows: Sequence[Mapping[str, Any]],
    ordered: bool,
    columns: Optional[Iterable[str]] = None,
    unordered_mode: str = "multiset",
    nulls_equal: bool = False,
    allow_lossy_numeric: bool = False,
    numeric_abs_tolerance: object = Decimal("0"),
    numeric_rel_tolerance: object = Decimal("0"),
) -> ComparisonResult:
    if unordered_mode not in {"set", "multiset"}:
        raise ValueError("unordered_mode must be 'set' or 'multiset'")

    resolved_columns = _row_columns(expected_rows, actual_rows, columns)
    mode = "ordered-rows" if ordered else f"unordered-rows-{unordered_mode}"
    if len(expected_rows) != len(actual_rows) and (ordered or unordered_mode == "multiset"):
        return ComparisonResult(
            False,
            _anchored_diagnostic(
                kind="row comparison",
                scenario_key=scenario_key,
                context={"mode": mode, "row": min(len(expected_rows), len(actual_rows))},
                expected=f"{len(expected_rows)} rows",
                actual=f"{len(actual_rows)} rows",
                note="row cardinality differs",
            ),
        )

    if ordered:
        for index, (expected, actual) in enumerate(zip(expected_rows, actual_rows)):
            result = _rows_equal(
                scenario_key=scenario_key,
                expected=expected,
                actual=actual,
                columns=resolved_columns,
                nulls_equal=nulls_equal,
                allow_lossy_numeric=allow_lossy_numeric,
                numeric_abs_tolerance=numeric_abs_tolerance,
                numeric_rel_tolerance=numeric_rel_tolerance,
                mode=mode,
                row_index=index,
            )
            if not result.matched:
                return result
        return ComparisonResult(True)

    if unordered_mode == "set":
        for expected_index, expected in enumerate(expected_rows):
            matched = False
            last_mismatch = ComparisonResult(True)
            for actual in actual_rows:
                result = _rows_equal(
                    scenario_key=scenario_key,
                    expected=expected,
                    actual=actual,
                    columns=resolved_columns,
                    nulls_equal=nulls_equal,
                    allow_lossy_numeric=allow_lossy_numeric,
                    numeric_abs_tolerance=numeric_abs_tolerance,
                    numeric_rel_tolerance=numeric_rel_tolerance,
                    mode=mode,
                    row_index=expected_index,
                )
                if result.matched:
                    matched = True
                    break
                last_mismatch = result
            if not matched:
                return last_mismatch
        for actual_index, actual in enumerate(actual_rows):
            matched = False
            for expected in expected_rows:
                result = _rows_equal(
                    scenario_key=scenario_key,
                    expected=expected,
                    actual=actual,
                    columns=resolved_columns,
                    nulls_equal=nulls_equal,
                    allow_lossy_numeric=allow_lossy_numeric,
                    numeric_abs_tolerance=numeric_abs_tolerance,
                    numeric_rel_tolerance=numeric_rel_tolerance,
                    mode=mode,
                    row_index=actual_index,
                )
                if result.matched:
                    matched = True
                    break
            if not matched:
                return ComparisonResult(
                    False,
                    _anchored_diagnostic(
                        kind="row comparison",
                        scenario_key=scenario_key,
                        context={"mode": mode, "row": actual_index, "column": "<row>"},
                        expected="<matching row>",
                        actual=_row_key(actual, resolved_columns),
                    ),
                )
        return ComparisonResult(True)

    unmatched_actual = set(range(len(actual_rows)))
    for expected_index, expected in enumerate(expected_rows):
        matched_actual_index = None
        last_mismatch = ComparisonResult(True)
        for actual_index in sorted(unmatched_actual):
            result = _rows_equal(
                scenario_key=scenario_key,
                expected=expected,
                actual=actual_rows[actual_index],
                columns=resolved_columns,
                nulls_equal=nulls_equal,
                allow_lossy_numeric=allow_lossy_numeric,
                numeric_abs_tolerance=numeric_abs_tolerance,
                numeric_rel_tolerance=numeric_rel_tolerance,
                mode=mode,
                row_index=expected_index,
            )
            if result.matched:
                matched_actual_index = actual_index
                break
            last_mismatch = result
        if matched_actual_index is None:
            return last_mismatch
        unmatched_actual.remove(matched_actual_index)
    return ComparisonResult(True)


def compare_declared_order(
    *,
    scenario_key: str,
    expected_rows: Sequence[Mapping[str, Any]],
    actual_rows: Sequence[Mapping[str, Any]],
    order_declared: bool,
    columns: Optional[Iterable[str]] = None,
    **kwargs: object,
) -> ComparisonResult:
    if not order_declared:
        return compare_rows(
            scenario_key=scenario_key,
            expected_rows=expected_rows,
            actual_rows=actual_rows,
            columns=columns,
            ordered=False,
            **kwargs,
        )

    ordered_result = compare_rows(
        scenario_key=scenario_key,
        expected_rows=expected_rows,
        actual_rows=actual_rows,
        columns=columns,
        ordered=True,
        **kwargs,
    )
    if ordered_result.matched:
        return ordered_result

    unordered_result = compare_rows(
        scenario_key=scenario_key,
        expected_rows=expected_rows,
        actual_rows=actual_rows,
        columns=columns,
        ordered=False,
        **kwargs,
    )
    if unordered_result.matched:
        resolved_columns = _row_columns(expected_rows, actual_rows, columns)
        first_expected = "<none>" if not expected_rows else _row_key(expected_rows[0], resolved_columns)
        first_actual = "<none>" if not actual_rows else _row_key(actual_rows[0], resolved_columns)
        return ComparisonResult(
            False,
            _anchored_diagnostic(
                kind="order comparison",
                scenario_key=scenario_key,
                context={"mode": "ordered-rows", "row": 0, "declared_order": True},
                expected=first_expected,
                actual=first_actual,
                note="same rows were present, but declared order was not preserved",
            ),
        )
    return ordered_result


def _field_value(value: object, field: str) -> object:
    if isinstance(value, Mapping):
        return value.get(field)
    return getattr(value, field, None)


def compare_expected_error(
    *,
    scenario_key: str,
    expected: object,
    actual: object,
    key_fields: Sequence[str] = ("code", "category", "field", "value"),
) -> ComparisonResult:
    fields = ("code",) + tuple(field for field in key_fields if field != "code")
    for field in fields:
        expected_value = _field_value(expected, field)
        actual_value = _field_value(actual, field)
        if field == "code" and expected_value is None and actual_value is None:
            return ComparisonResult(
                False,
                _anchored_diagnostic(
                    kind="expected error",
                    scenario_key=scenario_key,
                    context={"field": field},
                    expected="<structured error code>",
                    actual="<missing error code>",
                    note="expected-error matching requires a structured error code",
                ),
            )
        if expected_value != actual_value:
            return ComparisonResult(
                False,
                _anchored_diagnostic(
                    kind="expected error",
                    scenario_key=scenario_key,
                    context={"field": field},
                    expected=expected_value,
                    actual=actual_value,
                    note="expected-error matching uses structured code/key fields, not full text",
                ),
            )
    return ComparisonResult(True)


def render_row_mismatch(
    *,
    scenario_key: str,
    expected_rows: Sequence[Mapping[str, Any]],
    actual_rows: Sequence[Mapping[str, Any]],
    expected_columns: Iterable[str],
    ordered: bool,
    limit: int = 5,
) -> str:
    columns = tuple(expected_columns)
    mode = "ordered" if ordered else "unordered"
    lines = [
        f"{mode} row mismatch for scenario {scenario_key}",
        f"row_count: expected={len(expected_rows)} actual={len(actual_rows)}",
        "columns: " + (", ".join(columns) if columns else "<none>"),
    ]

    if ordered:
        first_mismatch = None
        for index, (expected, actual) in enumerate(zip(expected_rows, actual_rows)):
            if _row_key(expected, columns) != _row_key(actual, columns):
                first_mismatch = index
                break
        if first_mismatch is None and len(expected_rows) != len(actual_rows):
            first_mismatch = min(len(expected_rows), len(actual_rows))
        if first_mismatch is not None:
            lines.append(f"first_ordered_mismatch_index: {first_mismatch}")

    expected_counter = Counter(_row_key(row, columns) for row in expected_rows)
    actual_counter = Counter(_row_key(row, columns) for row in actual_rows)
    expected_only = _counter_delta(expected_counter, actual_counter)
    actual_only = _counter_delta(actual_counter, expected_counter)

    lines.append("expected_only:")
    lines.extend(f"- {item}" for item in expected_only[:limit])
    if len(expected_only) > limit:
        lines.append(f"- ... {len(expected_only) - limit} more")
    if not expected_only:
        lines.append("- none")

    lines.append("actual_only:")
    lines.extend(f"- {item}" for item in actual_only[:limit])
    if len(actual_only) > limit:
        lines.append(f"- ... {len(actual_only) - limit} more")
    if not actual_only:
        lines.append("- none")

    return "\n".join(lines)


def render_expected_error_mismatch(
    *,
    scenario_key: str,
    expected: object,
    actual: object,
) -> str:
    return "\n".join(
        [
            f"expected error mismatch for scenario {scenario_key}",
            f"expected: {_format_value(expected)}",
            f"actual: {_format_value(actual)}",
        ]
    )
