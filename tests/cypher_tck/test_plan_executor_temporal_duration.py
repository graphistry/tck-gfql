from __future__ import annotations

from tests.cypher_tck.plan_executor import _call_expr_function, _temporal_property


def test_duration_between_localdatetime_examples() -> None:
    out = _call_expr_function(
        "duration.between",
        [
            "2018-01-01T12:00",
            "2018-01-02T10:00",
        ],
    )
    assert out == "PT22H"


def test_duration_between_negative_fractional_time_only() -> None:
    out = _call_expr_function(
        "duration.between",
        [
            "2018-01-02T10:00:00.1",
            "2018-01-01T10:00:00.2",
        ],
    )
    assert out == "PT-23H-59M-59.9S"


def test_duration_inmonths_date_to_date() -> None:
    out = _call_expr_function(
        "duration.inMonths",
        [
            "1984-10-11",
            "2015-06-24",
        ],
    )
    assert out == "P30Y8M"


def test_duration_indays_date_to_date() -> None:
    out = _call_expr_function(
        "duration.inDays",
        [
            "1984-10-11",
            "2015-06-24",
        ],
    )
    assert out == "P11213D"


def test_duration_inseconds_fractional_localtime() -> None:
    out = _call_expr_function(
        "duration.inSeconds",
        [
            "12:34:56.3",
            "12:34:54.7",
        ],
    )
    assert out == "PT-1.6S"


def test_duration_functions_propagate_null() -> None:
    assert _call_expr_function("duration.inSeconds", [None, None]) is None


def test_duration_string_literal_roundtrip() -> None:
    out = _call_expr_function("duration", ["P14DT16H12M"])
    assert out == "P14DT16H12M"


def test_temporal_zero_arg_defaults_are_deterministic() -> None:
    assert _call_expr_function("date", []) == "2000-01-01"
    assert _call_expr_function("localtime", []) == "00:00"
    assert _call_expr_function("time", []) == "00:00+00:00"
    assert _call_expr_function("localdatetime", []) == "2000-01-01T00:00"
    assert _call_expr_function("datetime", []) == "2000-01-01T00:00Z"


def test_time_without_explicit_offset_defaults_to_z() -> None:
    assert _call_expr_function("time", ["14:30"]) == "14:30Z"


def test_duration_property_access_values() -> None:
    dur = "PT-23H-59M-59.9S"
    assert _temporal_property(dur, "days") == 0
    assert _temporal_property(dur, "seconds") == -86400
    assert _temporal_property(dur, "nanosecondsOfSecond") == 100000000


def test_datetime_truncate_accepts_date_input_with_date_units() -> None:
    out_year = _call_expr_function(
        "datetime.truncate",
        ["year", "1984-10-11", {"day": 2}],
    )
    assert out_year == "1984-01-02T00:00Z"

    out_month = _call_expr_function(
        "datetime.truncate",
        ["month", "1984-10-11", {"day": 2}],
    )
    assert out_month == "1984-10-02T00:00Z"


def test_datetime_truncate_accepts_time_units_for_datetime() -> None:
    out = _call_expr_function(
        "datetime.truncate",
        [
            "hour",
            "1984-10-11T12:31:14.645876123-01:00",
            {"nanosecond": 2},
        ],
    )
    assert out == "1984-10-11T12:00:00.000000002-01:00"


def test_time_truncate_nanosecond_unit() -> None:
    out = _call_expr_function(
        "time.truncate",
        ["nanosecond", "12:31:14.645876123+01:00", {"nanosecond": 2}],
    )
    assert out == "12:31:14.000000002+01:00"
