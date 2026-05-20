from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
from math import isnan
from typing import Any, Iterable, List, Mapping, Sequence


def _is_nullish(value: object) -> bool:
    if value is None:
        return True
    if type(value).__name__ in {"NAType", "NaTType"}:
        return True
    if isinstance(value, float):
        return isnan(value)
    return False


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
    if isinstance(value, (int, float, Decimal)):
        try:
            return format(Decimal(str(value)).normalize(), "f")
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
