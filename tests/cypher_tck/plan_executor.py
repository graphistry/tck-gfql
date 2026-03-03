from __future__ import annotations

import ast
import datetime as dt
import math
import numbers
import random
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, cast
from zoneinfo import ZoneInfo

import pandas as pd

from tests.cypher_tck.gfql_plan import Expr, PlanStep
from tests.cypher_tck.models import GraphFixture


class PlanExecutionError(ValueError):
    pass


_AGG_RE = re.compile(r"(?is)^(count|sum|min|max|avg)\((.*)\)$")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")
_KEYWORDS = {"AND", "OR", "NOT", "TRUE", "FALSE", "NULL"}
_FN_NAMES = {
    "count",
    "sum",
    "min",
    "max",
    "avg",
    "date",
    "time",
    "localtime",
    "datetime",
    "localdatetime",
    "range",
    "size",
    "keys",
    "toString",
    "toFloat",
    "toBoolean",
    "coalesce",
    "abs",
    "sqrt",
    "substring",
    "reverse",
    "toInteger",
    "ceil",
    "rand",
    "collect",
    "nodes",
    "length",
    "head",
}
_CTX_PREFIX = "__ctx__"

_OFFSET_RE = re.compile(r"^([+-])(\d{2})(?::?(\d{2}))?(?::?(\d{2}))?$")


@dataclass
class PlanState:
    graph: Any
    fixture: GraphFixture
    frame: pd.DataFrame
    match_result: Optional[Any] = None
    group_keys: Optional[List[str]] = None
    alias_exprs: Optional[Dict[str, str]] = None


@dataclass
class _SyntheticMatchResult:
    _nodes: pd.DataFrame
    _edges: pd.DataFrame


def _to_pandas(df: Any) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    if hasattr(df, "to_pandas"):
        return df.to_pandas()
    return df


def _is_null(value: Any) -> bool:
    if value is None:
        return True
    try:
        marker = pd.isna(value)
    except Exception:
        return False
    if isinstance(marker, bool):
        return marker
    return False


def _format_scalar(value: Any, quote_strings: bool = True) -> str:
    if _is_null(value):
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        if quote_strings and not (
            value.startswith("(")
            or value.startswith("[")
            or (value.startswith("'") and value.endswith("'"))
        ):
            return f"'{value}'"
        return value
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_format_scalar(v, quote_strings=True) for v in value) + "]"
    return str(value)


def _strip_outer_quotes(value: str) -> str:
    txt = value.strip()
    if len(txt) >= 2 and txt[0] == txt[-1] and txt[0] in {"'", '"'}:
        return txt[1:-1]
    return txt


def _coerce_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise PlanExecutionError(f"{field} must be numeric, got bool")
    if isinstance(value, numbers.Integral):
        return int(value)
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        raise PlanExecutionError(f"{field} must be an integer: {value}")
    if isinstance(value, str):
        txt = value.strip()
        if re.fullmatch(r"-?\d+", txt):
            return int(txt)
    raise PlanExecutionError(f"{field} must be an integer: {value!r}")


def _format_year(year: int) -> str:
    if year >= 0:
        return f"{year:04d}"
    return f"-{abs(year):04d}"


def _format_fraction(nanos: int, digits: int, trim: bool) -> str:
    if nanos <= 0:
        return ""
    frac = f"{nanos:09d}"[:digits]
    if trim:
        frac = frac.rstrip("0")
    return f".{frac}" if frac else ""


def _format_offset_seconds(total_seconds: int) -> str:
    if total_seconds == 0:
        return "Z"
    sign = "+" if total_seconds >= 0 else "-"
    rem = abs(total_seconds)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    if seconds:
        return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{sign}{hours:02d}:{minutes:02d}"


def _parse_offset_token(token: str) -> Tuple[int, str]:
    if token == "Z":
        return 0, "Z"
    match = _OFFSET_RE.fullmatch(token)
    if not match:
        raise PlanExecutionError(f"invalid timezone offset: {token}")
    sign = 1 if match.group(1) == "+" else -1
    hours = int(match.group(2))
    minutes = int(match.group(3) or 0)
    seconds = int(match.group(4) or 0)
    total = sign * (hours * 3600 + minutes * 60 + seconds)
    return total, _format_offset_seconds(total)


def _parse_date_parts(value: str) -> Tuple[int, int, int]:
    txt = _strip_outer_quotes(value)

    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", txt)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))

    m = re.fullmatch(r"(\d{8})", txt)
    if m:
        raw = m.group(1)
        return int(raw[0:4]), int(raw[4:6]), int(raw[6:8])

    m = re.fullmatch(r"(\d{4})-(\d{2})", txt)
    if m:
        return int(m.group(1)), int(m.group(2)), 1

    m = re.fullmatch(r"(\d{6})", txt)
    if m:
        raw = m.group(1)
        return int(raw[0:4]), int(raw[4:6]), 1

    m = re.fullmatch(r"(\d{4})-W(\d{2})(?:-(\d))?", txt)
    if m:
        year = int(m.group(1))
        week = int(m.group(2))
        day = int(m.group(3) or "1")
        d = dt.date.fromisocalendar(year, week, day)
        return d.year, d.month, d.day

    m = re.fullmatch(r"(\d{4})W(\d{2})(\d)?", txt)
    if m:
        year = int(m.group(1))
        week = int(m.group(2))
        day = int(m.group(3) or "1")
        d = dt.date.fromisocalendar(year, week, day)
        return d.year, d.month, d.day

    m = re.fullmatch(r"(\d{4})-(\d{3})", txt)
    if m:
        year = int(m.group(1))
        ordinal = int(m.group(2))
        d = dt.date(year, 1, 1) + dt.timedelta(days=ordinal - 1)
        return d.year, d.month, d.day

    m = re.fullmatch(r"(\d{7})", txt)
    if m:
        raw = m.group(1)
        year = int(raw[0:4])
        ordinal = int(raw[4:7])
        d = dt.date(year, 1, 1) + dt.timedelta(days=ordinal - 1)
        return d.year, d.month, d.day

    m = re.fullmatch(r"(\d{4})", txt)
    if m:
        return int(m.group(1)), 1, 1

    raise PlanExecutionError(f"unsupported date literal: {value}")


def _format_date(year: int, month: int, day: int) -> str:
    return f"{_format_year(year)}-{month:02d}-{day:02d}"


def _coerce_date_string(value: Any) -> str:
    if value is None:
        raise PlanExecutionError("date() does not accept null")
    txt = str(value)
    if "T" in txt:
        txt = txt.split("T", 1)[0]
    year, month, day = _parse_date_parts(txt)
    return _format_date(year, month, day)


def _split_zone_suffix(value: str) -> Tuple[str, Optional[str]]:
    txt = value.strip()
    if not txt.endswith("]"):
        return txt, None
    idx = txt.rfind("[")
    if idx <= 0:
        return txt, None
    return txt[:idx], txt[idx + 1 : -1]


def _split_time_offset(value: str) -> Tuple[str, Optional[str]]:
    txt = value.strip()
    if txt.endswith("Z"):
        return txt[:-1], "Z"
    match = re.search(r"([+-]\d{2}(?::?\d{2})?(?::?\d{2})?)$", txt)
    if not match:
        return txt, None
    return txt[: match.start()], match.group(1)


def _parse_time_literal(value: str) -> Tuple[int, int, int, int, bool, int]:
    txt = _strip_outer_quotes(value)

    m = re.fullmatch(r"(\d{2})(?::(\d{2}))?(?::(\d{2})(?:\.(\d{1,9}))?)?", txt)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2) or "0")
        second = int(m.group(3) or "0")
        frac = m.group(4)
        nanos = 0
        frac_digits = 0
        if frac is not None:
            frac_digits = len(frac)
            nanos = int(frac.ljust(9, "0"))
        show_seconds = m.group(3) is not None or frac is not None
        return hour, minute, second, nanos, show_seconds, frac_digits

    m = re.fullmatch(r"(\d{2})(\d{2})(\d{2})(?:\.(\d{1,9}))?", txt)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        second = int(m.group(3))
        frac = m.group(4)
        nanos = 0
        frac_digits = 0
        if frac is not None:
            frac_digits = len(frac)
            nanos = int(frac.ljust(9, "0"))
        return hour, minute, second, nanos, True, frac_digits

    m = re.fullmatch(r"(\d{2})(\d{2})", txt)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        return hour, minute, 0, 0, False, 0

    m = re.fullmatch(r"(\d{2})", txt)
    if m:
        hour = int(m.group(1))
        return hour, 0, 0, 0, False, 0

    raise PlanExecutionError(f"unsupported time literal: {value}")


def _format_time(
    hour: int,
    minute: int,
    second: int,
    nanos: int,
    show_seconds: bool,
    fraction_digits: int = 9,
    trim_fraction: bool = True,
) -> str:
    base = f"{hour:02d}:{minute:02d}"
    should_show_seconds = show_seconds or second != 0 or nanos != 0
    if not should_show_seconds:
        return base
    out = f"{base}:{second:02d}"
    if nanos:
        out += _format_fraction(nanos, fraction_digits, trim_fraction)
    return out


def _coerce_localtime_string(value: Any) -> str:
    hour, minute, second, nanos, show_seconds, frac_digits = _parse_time_literal(str(value))
    digits = frac_digits if frac_digits > 0 else 9
    trim = frac_digits > 0
    return _format_time(hour, minute, second, nanos, show_seconds, fraction_digits=digits, trim_fraction=trim)


def _coerce_time_string(value: Any) -> str:
    body, zone = _split_zone_suffix(str(value))
    time_part, offset_part = _split_time_offset(body)
    if offset_part is None:
        raise PlanExecutionError(f"time literal requires timezone offset: {value}")

    hour, minute, second, nanos, show_seconds, frac_digits = _parse_time_literal(time_part)
    _, offset_txt = _parse_offset_token(offset_part)
    digits = frac_digits if frac_digits > 0 else 9
    trim = frac_digits > 0
    out = _format_time(hour, minute, second, nanos, show_seconds, fraction_digits=digits, trim_fraction=trim) + offset_txt
    if zone:
        out += f"[{zone}]"
    return out


def _coerce_localdatetime_string(value: Any) -> str:
    txt = _strip_outer_quotes(str(value))
    if "T" not in txt:
        raise PlanExecutionError(f"localdatetime literal missing 'T': {value}")
    date_part, time_part = txt.split("T", 1)
    date_txt = _format_date(*_parse_date_parts(date_part))
    time_txt = _coerce_localtime_string(time_part)
    return f"{date_txt}T{time_txt}"


def _resolve_named_zone_offset(
    zone: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
) -> str:
    try:
        aware = dt.datetime(year, month, day, hour, minute, second, tzinfo=ZoneInfo(zone))
        delta = aware.utcoffset() or dt.timedelta()
        return _format_offset_seconds(int(delta.total_seconds()))
    except Exception as exc:
        raise PlanExecutionError(f"failed resolving timezone '{zone}': {exc}") from exc


def _coerce_datetime_string(value: Any) -> str:
    txt = _strip_outer_quotes(str(value))
    if "T" not in txt:
        raise PlanExecutionError(f"datetime literal missing 'T': {value}")

    body, zone = _split_zone_suffix(txt)
    date_part, time_with_offset = body.split("T", 1)
    date_txt = _format_date(*_parse_date_parts(date_part))
    year, month, day = _parse_date_parts(date_part)

    time_part, offset_part = _split_time_offset(time_with_offset)
    hour, minute, second, nanos, show_seconds, frac_digits = _parse_time_literal(time_part)

    offset_txt: Optional[str] = None
    if offset_part is not None:
        _, offset_txt = _parse_offset_token(offset_part)
    elif zone:
        offset_txt = _resolve_named_zone_offset(zone, year, month, day, hour, minute, second)
    else:
        raise PlanExecutionError(f"datetime literal requires timezone: {value}")

    digits = frac_digits if frac_digits > 0 else 9
    trim = frac_digits > 0
    out = f"{date_txt}T{_format_time(hour, minute, second, nanos, show_seconds, fraction_digits=digits, trim_fraction=trim)}{offset_txt}"
    if zone:
        out += f"[{zone}]"
    return out


def _extract_date_from_temporal(value: Any) -> Optional[str]:
    if _is_null(value):
        return None
    txt = _strip_outer_quotes(str(value))
    if "T" in txt:
        return txt.split("T", 1)[0]
    if re.fullmatch(r"-?\d{4}-\d{2}-\d{2}", txt):
        return txt
    return None


def _extract_time_from_temporal(value: Any) -> Optional[str]:
    if _is_null(value):
        return None
    txt = _strip_outer_quotes(str(value))
    if "T" in txt:
        return txt.split("T", 1)[1]
    if re.fullmatch(r"\d{2}:\d{2}(?::\d{2}(?:\.\d{1,9})?)?(?:Z|[+-]\d{2}:\d{2}(?::\d{2})?)?(?:\[[^\]]+\])?", txt):
        return txt
    return None


def _temporal_property(value: Any, prop: str) -> Any:
    if _is_null(value):
        return None
    txt = _strip_outer_quotes(str(value))
    property_name = prop.strip()

    date_part = _extract_date_from_temporal(txt)
    if date_part is not None:
        try:
            year, month, day = _parse_date_parts(date_part)
            d = dt.date(year, month, day)
        except Exception:
            d = None
        if d is not None:
            quarter = ((d.month - 1) // 3) + 1
            if property_name == "year":
                return d.year
            if property_name == "month":
                return d.month
            if property_name == "day":
                return d.day
            if property_name == "quarter":
                return quarter
            if property_name == "week":
                return d.isocalendar().week
            if property_name == "dayOfWeek":
                return d.isoweekday()
            if property_name == "ordinalDay":
                return d.timetuple().tm_yday
            if property_name == "dayOfQuarter":
                quarter_start = dt.date(d.year, (quarter - 1) * 3 + 1, 1)
                return (d - quarter_start).days + 1

    time_part = _extract_time_from_temporal(txt)
    if time_part is not None:
        core_time = _split_zone_suffix(time_part)[0]
        core_time, offset_part = _split_time_offset(core_time)
        try:
            hour, minute, second, nanos, _, _ = _parse_time_literal(core_time)
        except Exception:
            return None
        if property_name == "hour":
            return hour
        if property_name == "minute":
            return minute
        if property_name == "second":
            return second
        if property_name == "nanosecond":
            return nanos
        if property_name == "millisecond":
            return nanos // 1_000_000
        if property_name == "microsecond":
            return nanos // 1_000
        if property_name == "timezone":
            zone_name = _split_zone_suffix(time_part)[1]
            if zone_name:
                return zone_name
            return offset_part

    return None


def _coerce_date_from_map(mapping: Dict[str, Any]) -> str:
    base_date: Optional[dt.date] = None
    if "date" in mapping and not _is_null(mapping["date"]):
        base_str = _extract_date_from_temporal(mapping["date"])
        if base_str is None:
            raise PlanExecutionError(f"date map 'date' value is not temporal: {mapping['date']!r}")
        base_y, base_m, base_d = _parse_date_parts(base_str)
        base_date = dt.date(base_y, base_m, base_d)

    if "year" in mapping:
        year = _coerce_int(mapping["year"], "date.year")
    elif base_date is not None:
        year = base_date.year
    else:
        raise PlanExecutionError("date map requires year when date is absent")

    if "week" in mapping:
        week = _coerce_int(mapping["week"], "date.week")
        day_of_week = _coerce_int(mapping.get("dayOfWeek", base_date.isoweekday() if base_date else 1), "date.dayOfWeek")
        out = dt.date.fromisocalendar(year, week, day_of_week)
        return _format_date(out.year, out.month, out.day)

    if "ordinalDay" in mapping:
        ordinal = _coerce_int(mapping["ordinalDay"], "date.ordinalDay")
        out = dt.date(year, 1, 1) + dt.timedelta(days=ordinal - 1)
        return _format_date(out.year, out.month, out.day)

    if "dayOfQuarter" in mapping:
        if "quarter" in mapping:
            quarter = _coerce_int(mapping["quarter"], "date.quarter")
        elif base_date is not None:
            quarter = ((base_date.month - 1) // 3) + 1
        else:
            quarter = 1
        day_of_quarter = _coerce_int(mapping["dayOfQuarter"], "date.dayOfQuarter")
        start_month = (quarter - 1) * 3 + 1
        out = dt.date(year, start_month, 1) + dt.timedelta(days=day_of_quarter - 1)
        return _format_date(out.year, out.month, out.day)

    if "quarter" in mapping:
        quarter = _coerce_int(mapping["quarter"], "date.quarter")
        if base_date is not None and "month" not in mapping:
            month_in_quarter = ((base_date.month - 1) % 3) + 1
            month = (quarter - 1) * 3 + month_in_quarter
        else:
            month = _coerce_int(mapping.get("month", (quarter - 1) * 3 + 1), "date.month")
    else:
        month = _coerce_int(mapping.get("month", base_date.month if base_date else 1), "date.month")

    day = _coerce_int(mapping.get("day", base_date.day if base_date else 1), "date.day")
    out = dt.date(year, month, day)
    return _format_date(out.year, out.month, out.day)


def _coerce_localtime_from_map(mapping: Dict[str, Any]) -> str:
    base_time = "00:00"
    if "time" in mapping and not _is_null(mapping["time"]):
        extracted = _extract_time_from_temporal(mapping["time"])
        if extracted is None:
            raise PlanExecutionError(f"localtime map 'time' value is not temporal: {mapping['time']!r}")
        base_time = extracted

    base_hour, base_min, base_sec, base_nanos, _, _ = _parse_time_literal(_split_time_offset(base_time)[0])

    hour = _coerce_int(mapping.get("hour", base_hour), "localtime.hour")
    minute = _coerce_int(mapping.get("minute", base_min), "localtime.minute")
    second = _coerce_int(mapping.get("second", base_sec), "localtime.second")

    if "nanosecond" in mapping:
        nanos = _coerce_int(mapping["nanosecond"], "localtime.nanosecond")
    elif "microsecond" in mapping:
        nanos = _coerce_int(mapping["microsecond"], "localtime.microsecond") * 1000
    elif "millisecond" in mapping:
        nanos = _coerce_int(mapping["millisecond"], "localtime.millisecond") * 1_000_000
    else:
        nanos = base_nanos

    show_seconds = ("second" in mapping) or ("nanosecond" in mapping) or ("microsecond" in mapping) or ("millisecond" in mapping) or second != 0 or nanos != 0
    return _format_time(hour, minute, second, nanos, show_seconds, fraction_digits=9, trim_fraction=False)


def _coerce_time_from_map(mapping: Dict[str, Any]) -> str:
    base_time = "00:00+00:00"
    if "time" in mapping and not _is_null(mapping["time"]):
        extracted = _extract_time_from_temporal(mapping["time"])
        if extracted is None:
            raise PlanExecutionError(f"time map 'time' value is not temporal: {mapping['time']!r}")
        if "[" in extracted and extracted.endswith("]"):
            extracted, _ = _split_zone_suffix(extracted)
        base_time = extracted

    base_body, base_offset = _split_time_offset(base_time)
    if base_offset is None:
        base_offset = "+00:00"
    base_hour, base_min, base_sec, base_nanos, _, _ = _parse_time_literal(base_body)

    hour = _coerce_int(mapping.get("hour", base_hour), "time.hour")
    minute = _coerce_int(mapping.get("minute", base_min), "time.minute")
    second = _coerce_int(mapping.get("second", base_sec), "time.second")
    if "nanosecond" in mapping:
        nanos = _coerce_int(mapping["nanosecond"], "time.nanosecond")
    elif "microsecond" in mapping:
        nanos = _coerce_int(mapping["microsecond"], "time.microsecond") * 1000
    elif "millisecond" in mapping:
        nanos = _coerce_int(mapping["millisecond"], "time.millisecond") * 1_000_000
    else:
        nanos = base_nanos

    zone_txt = mapping.get("timezone", base_offset)
    _, offset_txt = _parse_offset_token(str(zone_txt))
    show_seconds = ("second" in mapping) or ("nanosecond" in mapping) or ("microsecond" in mapping) or ("millisecond" in mapping) or second != 0 or nanos != 0
    return _format_time(hour, minute, second, nanos, show_seconds, fraction_digits=9, trim_fraction=False) + offset_txt


def _coerce_localdatetime_from_map(mapping: Dict[str, Any]) -> str:
    base_date_txt = "0001-01-01"
    if "datetime" in mapping and not _is_null(mapping["datetime"]):
        base_datetime = _strip_outer_quotes(str(mapping["datetime"]))
        if "T" in base_datetime:
            base_date_txt = base_datetime.split("T", 1)[0]
        else:
            base_date_txt = base_datetime
    elif "date" in mapping and not _is_null(mapping["date"]):
        extracted_date = _extract_date_from_temporal(mapping["date"])
        if extracted_date is not None:
            base_date_txt = extracted_date

    base_time_txt = "00:00"
    if "datetime" in mapping and not _is_null(mapping["datetime"]):
        dt_value = _strip_outer_quotes(str(mapping["datetime"]))
        if "T" in dt_value:
            base_time_txt = dt_value.split("T", 1)[1]
            if "[" in base_time_txt and base_time_txt.endswith("]"):
                base_time_txt, _ = _split_zone_suffix(base_time_txt)
            base_time_txt, _ = _split_time_offset(base_time_txt)
    if "time" in mapping and not _is_null(mapping["time"]):
        extracted_time = _extract_time_from_temporal(mapping["time"])
        if extracted_time is not None:
            base_time_txt = _split_time_offset(_split_zone_suffix(extracted_time)[0])[0]

    date_map = dict(mapping)
    date_map["date"] = base_date_txt
    date_txt = _coerce_date_from_map(date_map)

    time_map = dict(mapping)
    time_map["time"] = base_time_txt
    time_txt = _coerce_localtime_from_map(time_map)
    return f"{date_txt}T{time_txt}"


def _coerce_datetime_from_map(mapping: Dict[str, Any]) -> str:
    local_txt = _coerce_localdatetime_from_map(mapping)
    date_part, time_part = local_txt.split("T", 1)
    year, month, day = _parse_date_parts(date_part)
    hour, minute, second, _, _, _ = _parse_time_literal(time_part)

    zone_raw = mapping.get("timezone")
    if zone_raw is None:
        zone_txt = "Z"
        zone_name: Optional[str] = None
    else:
        zone_str = str(zone_raw).strip()
        zone_name = zone_str if "/" in zone_str else None
        if zone_name is None:
            _, zone_txt = _parse_offset_token(zone_str)
        else:
            zone_txt = _resolve_named_zone_offset(zone_name, year, month, day, hour, minute, second)

    out = f"{local_txt}{zone_txt}"
    if zone_name is not None:
        out += f"[{zone_name}]"
    return out


def _normalize_labels(value: Any) -> List[str]:
    if _is_null(value):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value if not _is_null(v)]
    return [str(value)]


def _format_props(row: pd.Series, prop_cols: Sequence[str]) -> str:
    items = []
    for col in prop_cols:
        if col not in row.index:
            continue
        v = row[col]
        if _is_null(v):
            continue
        items.append(f"{col}: {_format_scalar(v, quote_strings=True)}")
    return ", ".join(items)


def _format_node_entity(row: pd.Series, fixture: GraphFixture) -> str:
    labels = _normalize_labels(row.get("labels"))
    label_part = ":" + ":".join(labels) if labels else ""
    node_id_value = row.get(fixture.node_id)
    include_node_id = isinstance(node_id_value, (int, float)) and not isinstance(node_id_value, bool)
    prop_cols = [
        c
        for c in row.index
        if isinstance(c, str)
        and (c != fixture.node_id or include_node_id)
        and c != "labels"
        and not c.startswith("label__")
        and "." not in c
        and c not in {"src", "dst", "edge_id", "type"}
        and not c.startswith(_CTX_PREFIX)
    ]
    props = _format_props(row, prop_cols)
    if props:
        if label_part:
            return f"({label_part} {{{props}}})"
        return f"({{{props}}})"
    if label_part:
        return f"({label_part})"
    return "()"


def _format_edge_entity(row: pd.Series, fixture: GraphFixture) -> str:
    edge_type = row.get("type")
    type_part = f":{edge_type}" if isinstance(edge_type, str) and edge_type else ""
    prop_cols = [
        c
        for c in row.index
        if isinstance(c, str)
        and c not in (fixture.src, fixture.dst, fixture.edge_id, "type")
        and "." not in c
        and not c.startswith(_CTX_PREFIX)
    ]
    props = _format_props(row, prop_cols)
    if props:
        return f"[{type_part} {{{props}}}]"
    return f"[{type_part}]"


def _add_alias_columns(df: pd.DataFrame, alias: str, fixture: GraphFixture, table: str) -> pd.DataFrame:
    out = df.copy()
    for col in list(df.columns):
        out[f"{alias}.{col}"] = df[col]
    if table == "nodes":
        out[alias] = df.apply(lambda row: _format_node_entity(row, fixture), axis=1)
    elif table == "edges":
        out[alias] = df.apply(lambda row: _format_edge_entity(row, fixture), axis=1)
    return out


def _literal_expr(value: str) -> Any:
    txt = value.strip()
    if txt.startswith("$"):
        raise PlanExecutionError(f"parameter expressions are not supported: {value}")
    if txt.startswith("'") and txt.endswith("'") and len(txt) >= 2:
        return txt[1:-1]
    if txt.startswith('"') and txt.endswith('"') and len(txt) >= 2:
        return txt[1:-1]
    low = txt.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low == "null":
        return None
    if re.fullmatch(r"-?\d+", txt):
        return int(txt)
    if re.fullmatch(r"-?\d+\.\d+", txt):
        return float(txt)
    return None


def _fn_range(args: Sequence[Any]) -> List[int]:
    if len(args) not in (2, 3):
        raise PlanExecutionError(f"range() expects 2 or 3 arguments, got {len(args)}")
    start = _coerce_int(args[0], "range.start")
    end = _coerce_int(args[1], "range.end")
    step = _coerce_int(args[2], "range.step") if len(args) == 3 else 1
    if step == 0:
        raise PlanExecutionError("range() step cannot be zero")
    if step > 0:
        return list(range(start, end + 1, step)) if start <= end else []
    return list(range(start, end - 1, step)) if start >= end else []


def _fn_size(args: Sequence[Any]) -> Any:
    if len(args) != 1:
        raise PlanExecutionError(f"size() expects 1 argument, got {len(args)}")
    value = args[0]
    if _is_null(value):
        return None
    if isinstance(value, (list, tuple, dict, str)):
        return len(value)
    raise PlanExecutionError(f"size() unsupported argument type: {type(value).__name__}")


def _fn_keys(args: Sequence[Any]) -> Any:
    if len(args) != 1:
        raise PlanExecutionError(f"keys() expects 1 argument, got {len(args)}")
    value = args[0]
    if _is_null(value):
        return None
    if isinstance(value, dict):
        return list(value.keys())
    raise PlanExecutionError(f"keys() requires a map argument, got {type(value).__name__}")


def _fn_to_string(args: Sequence[Any]) -> Any:
    if len(args) != 1:
        raise PlanExecutionError(f"toString() expects 1 argument, got {len(args)}")
    value = args[0]
    if _is_null(value):
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return _strip_outer_quotes(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple, dict)):
        return _format_scalar(value, quote_strings=False)
    return str(value)


def _fn_to_integer(args: Sequence[Any]) -> Any:
    if len(args) != 1:
        raise PlanExecutionError(f"toInteger() expects 1 argument, got {len(args)}")
    value = args[0]
    if _is_null(value):
        return None
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        txt = _strip_outer_quotes(value)
        return int(float(txt)) if "." in txt else int(txt)
    raise PlanExecutionError(f"toInteger() unsupported argument type: {type(value).__name__}")


def _fn_to_float(args: Sequence[Any]) -> Any:
    if len(args) != 1:
        raise PlanExecutionError(f"toFloat() expects 1 argument, got {len(args)}")
    value = args[0]
    if _is_null(value):
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(_strip_outer_quotes(value))
    raise PlanExecutionError(f"toFloat() unsupported argument type: {type(value).__name__}")


def _fn_to_boolean(args: Sequence[Any]) -> Any:
    if len(args) != 1:
        raise PlanExecutionError(f"toBoolean() expects 1 argument, got {len(args)}")
    value = args[0]
    if _is_null(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        txt = _strip_outer_quotes(value).strip().lower()
        if txt in {"true", "t", "1", "yes"}:
            return True
        if txt in {"false", "f", "0", "no"}:
            return False
    raise PlanExecutionError(f"toBoolean() unsupported argument value: {value!r}")


def _fn_coalesce(args: Sequence[Any]) -> Any:
    for value in args:
        if not _is_null(value):
            return value
    return None


def _fn_substring(args: Sequence[Any]) -> Any:
    if len(args) not in (2, 3):
        raise PlanExecutionError(f"substring() expects 2 or 3 arguments, got {len(args)}")
    text = _strip_outer_quotes(str(args[0]))
    start = _coerce_int(args[1], "substring.start")
    if len(args) == 2:
        return text[start:]
    size = _coerce_int(args[2], "substring.size")
    return text[start : start + size]


def _fn_temporal(name: str, args: Sequence[Any]) -> Any:
    if len(args) != 1:
        raise PlanExecutionError(f"{name}() expects 1 argument, got {len(args)}")
    value = args[0]
    if _is_null(value):
        return None
    if name == "date":
        if isinstance(value, dict):
            return _coerce_date_from_map(value)
        return _coerce_date_string(value)
    if name == "localtime":
        if isinstance(value, dict):
            return _coerce_localtime_from_map(value)
        if isinstance(value, str) and ("+" in value or "-" in value[1:] or value.endswith("Z")):
            return _coerce_localtime_string(_split_time_offset(_split_zone_suffix(value)[0])[0])
        return _coerce_localtime_string(value)
    if name == "time":
        if isinstance(value, dict):
            return _coerce_time_from_map(value)
        return _coerce_time_string(value)
    if name == "localdatetime":
        if isinstance(value, dict):
            return _coerce_localdatetime_from_map(value)
        return _coerce_localdatetime_string(value)
    if name == "datetime":
        if isinstance(value, dict):
            return _coerce_datetime_from_map(value)
        return _coerce_datetime_string(value)
    raise PlanExecutionError(f"unsupported temporal function: {name}")


def _call_expr_function(name: str, args: Sequence[Any]) -> Any:
    fn = name.strip()
    fn_lower = fn.lower()

    if fn_lower in {"date", "localtime", "time", "localdatetime", "datetime"}:
        return _fn_temporal(fn_lower, args)
    if fn_lower == "range":
        return _fn_range(args)
    if fn_lower == "size":
        return _fn_size(args)
    if fn_lower == "keys":
        return _fn_keys(args)
    if fn_lower == "tostring":
        return _fn_to_string(args)
    if fn_lower == "tointeger":
        return _fn_to_integer(args)
    if fn_lower == "tofloat":
        return _fn_to_float(args)
    if fn_lower == "toboolean":
        return _fn_to_boolean(args)
    if fn_lower == "coalesce":
        return _fn_coalesce(args)
    if fn_lower == "ceil":
        if len(args) != 1:
            raise PlanExecutionError(f"ceil() expects 1 argument, got {len(args)}")
        return math.ceil(float(cast(float, args[0])))
    if fn_lower == "rand":
        if len(args) != 0:
            raise PlanExecutionError(f"rand() expects 0 arguments, got {len(args)}")
        return random.random()
    if fn_lower == "abs":
        if len(args) != 1:
            raise PlanExecutionError(f"abs() expects 1 argument, got {len(args)}")
        return abs(args[0])
    if fn_lower == "sqrt":
        if len(args) != 1:
            raise PlanExecutionError(f"sqrt() expects 1 argument, got {len(args)}")
        return math.sqrt(float(cast(float, args[0])))
    if fn_lower == "reverse":
        if len(args) != 1:
            raise PlanExecutionError(f"reverse() expects 1 argument, got {len(args)}")
        return _strip_outer_quotes(str(args[0]))[::-1]
    if fn_lower == "substring":
        return _fn_substring(args)
    if fn_lower in {"min", "max"}:
        if len(args) != 1:
            raise PlanExecutionError(f"{name}() expects 1 argument, got {len(args)}")
        value = args[0]
        if isinstance(value, (list, tuple)):
            return min(value) if fn_lower == "min" else max(value)
        return value
    raise PlanExecutionError(f"unsupported expression function: {name}")


def _rewrite_expr(expr: str, df: pd.DataFrame) -> Tuple[str, Dict[str, Any]]:
    rewritten = expr
    env: Dict[str, Any] = {}
    tokens = sorted(set(_IDENT_RE.findall(expr)), key=len, reverse=True)
    counter = 0
    for token in tokens:
        if token.upper() in _KEYWORDS:
            continue
        if token in _FN_NAMES and re.search(rf"(?i)\b{re.escape(token)}\s*\(", expr):
            continue
        col_name: Optional[str] = None
        if token in df.columns:
            col_name = token
        elif f"{_CTX_PREFIX}{token}" in df.columns:
            col_name = f"{_CTX_PREFIX}{token}"

        if col_name is not None:
            var = f"__c{counter}"
            counter += 1
            rewritten = re.sub(rf"(?<![A-Za-z0-9_.]){re.escape(token)}(?![A-Za-z0-9_.])", var, rewritten)
            env[var] = df[col_name]
    rewritten = rewritten.replace("<>", "!=")
    rewritten = re.sub(r"(?<![<>=!])=(?!=)", "==", rewritten)
    rewritten = re.sub(r"\bAND\b", "&", rewritten, flags=re.IGNORECASE)
    rewritten = re.sub(r"\bOR\b", "|", rewritten, flags=re.IGNORECASE)
    rewritten = re.sub(r"\bNOT\b", "~", rewritten, flags=re.IGNORECASE)
    rewritten = re.sub(r"\btrue\b", "True", rewritten, flags=re.IGNORECASE)
    rewritten = re.sub(r"\bfalse\b", "False", rewritten, flags=re.IGNORECASE)
    rewritten = re.sub(r"\bnull\b", "None", rewritten, flags=re.IGNORECASE)
    return rewritten, env


def _eval_expr_series(df: pd.DataFrame, expr: Any) -> pd.Series:
    if isinstance(expr, Expr):
        if expr.op == "lit":
            value = expr.args.get("value")
            return pd.Series([value] * len(df), index=df.index)
        if expr.op == "list":
            item_series = [_eval_expr_series(df, item) for item in expr.args.get("items", ())]
            list_values: List[List[Any]] = []
            for idx in range(len(df)):
                list_values.append([series.iloc[idx] for series in item_series])
            return pd.Series(list_values, index=df.index)
        if expr.op == "map":
            items = list(expr.args.get("items", ()))
            value_series = [_eval_expr_series(df, v) for _, v in items]
            map_values: List[Dict[str, Any]] = []
            for idx in range(len(df)):
                row: Dict[str, Any] = {}
                for item_idx, (key, _) in enumerate(items):
                    row[str(key)] = value_series[item_idx].iloc[idx]
                map_values.append(row)
            return pd.Series(map_values, index=df.index)
        if expr.op == "col":
            name = str(expr.args.get("name"))
            if name not in df.columns:
                raise PlanExecutionError(f"unknown column in expression: {name}")
            return df[name]
        if expr.op == "func":
            name = str(expr.args.get("name", ""))
            arg_exprs = tuple(expr.args.get("args", ()))
            arg_series = [_eval_expr_series(df, arg_expr) for arg_expr in arg_exprs]
            func_values: List[Any] = []
            for idx in range(len(df)):
                fn_args = [series.iloc[idx] for series in arg_series]
                func_values.append(_call_expr_function(name, fn_args))
            return pd.Series(func_values, index=df.index)
        if expr.op == "index":
            base_series = _eval_expr_series(df, expr.args.get("base"))
            key_series = _eval_expr_series(df, expr.args.get("key"))
            index_values: List[Any] = []
            for idx in range(len(df)):
                base = base_series.iloc[idx]
                key = key_series.iloc[idx]
                if _is_null(base) or _is_null(key):
                    index_values.append(None)
                    continue
                try:
                    index_values.append(base[key])
                except Exception as exc:
                    raise PlanExecutionError(f"index access failed: {exc}") from exc
            return pd.Series(index_values, index=df.index)
        if expr.op == "param":
            name = str(expr.args.get("name", ""))
            raise PlanExecutionError(f"parameter expressions are not supported: ${name}")
        if expr.op == "raw":
            return _eval_expr_series(df, str(expr.args.get("text", "")))
        raise PlanExecutionError(f"unsupported Expr op: {expr.op}")

    if not isinstance(expr, str):
        return pd.Series([expr] * len(df), index=df.index)

    txt = expr.strip()
    if txt in df.columns:
        return df[txt]

    property_access = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)", txt)
    if property_access and txt not in df.columns and f"{_CTX_PREFIX}{txt}" not in df.columns:
        base = property_access.group(1)
        prop = property_access.group(2)
        if base in df.columns or f"{_CTX_PREFIX}{base}" in df.columns:
            source_col = base if base in df.columns else f"{_CTX_PREFIX}{base}"
            return df[source_col].map(lambda value: _temporal_property(value, prop))

    lit = _literal_expr(txt)
    if lit is not None or txt.lower() == "null":
        return pd.Series([lit] * len(df), index=df.index)

    if txt.startswith("$"):
        raise PlanExecutionError(f"parameter expressions are not supported: {txt}")

    if len(df) == 0:
        return pd.Series([], index=df.index, dtype="object")

    rewritten, env = _rewrite_expr(txt, df)
    try:
        result = eval(rewritten, {"__builtins__": {}}, env)  # noqa: S307
    except Exception as exc:
        raise PlanExecutionError(f"failed to evaluate expression '{txt}': {exc}") from exc

    if isinstance(result, pd.Series):
        return result
    return pd.Series([result] * len(df), index=df.index)


def _expr_literal_value(expr: Any) -> Any:
    if not isinstance(expr, Expr):
        return expr
    if expr.op == "lit":
        return expr.args.get("value")
    if expr.op == "list":
        return [_expr_literal_value(item) for item in expr.args.get("items", ())]
    if expr.op == "map":
        return {str(k): _expr_literal_value(v) for k, v in expr.args.get("items", ())}
    if expr.op == "raw":
        txt = str(expr.args.get("text", "")).strip()
        lit = _literal_expr(txt)
        if lit is not None or txt.lower() == "null":
            return lit
        return txt
    raise PlanExecutionError(f"unsupported literal Expr op: {expr.op}")


def _eval_scalar_limit_skip(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        raise PlanExecutionError(f"non-integer value for SKIP/LIMIT: {value}")
    if not isinstance(value, str):
        raise PlanExecutionError(f"unsupported SKIP/LIMIT value: {value!r}")

    txt = value.strip()
    if txt.startswith("$"):
        raise PlanExecutionError(f"parameter value not supported for SKIP/LIMIT: {value}")
    if re.fullmatch(r"-?\d+", txt):
        return int(txt)
    if re.fullmatch(r"-?\d+\.\d+", txt):
        raise PlanExecutionError(f"non-integer value for SKIP/LIMIT: {value}")

    rewritten = txt.replace("toInteger", "int").replace("ceil", "math.ceil").replace("rand()", "random.random()")
    try:
        result = eval(rewritten, {"__builtins__": {}}, {"math": math, "random": random, "int": int})  # noqa: S307
    except Exception as exc:
        raise PlanExecutionError(f"failed to evaluate SKIP/LIMIT expression '{value}': {exc}") from exc
    if not isinstance(result, (int, float)):
        raise PlanExecutionError(f"SKIP/LIMIT expression did not evaluate to numeric: {value}")
    if isinstance(result, float) and not result.is_integer():
        raise PlanExecutionError(f"non-integer value for SKIP/LIMIT: {value}")
    return int(result)


def _parse_agg(expr: Any) -> Optional[Tuple[str, Any]]:
    if isinstance(expr, Expr):
        if expr.op != "func":
            return None
        func_name = str(expr.args.get("name", "")).lower()
        if func_name not in {"count", "sum", "min", "max", "avg"}:
            return None
        args = tuple(expr.args.get("args", ()))
        if func_name == "count" and len(args) == 1 and isinstance(args[0], Expr) and args[0].op == "star":
            return func_name, "*"
        if len(args) != 1:
            raise PlanExecutionError(f"aggregate {func_name} expects one argument")
        return func_name, args[0]
    if not isinstance(expr, str):
        return None
    m = _AGG_RE.match(expr.strip())
    if not m:
        return None
    return m.group(1).lower(), m.group(2).strip()


def _aggregate_series(df: pd.DataFrame, func: str, arg: Any) -> Any:
    if func == "count" and arg == "*":
        return int(len(df))
    series = _eval_expr_series(df, arg)
    if func == "count":
        return int(series.count())
    if func == "sum":
        return series.sum()
    if func == "min":
        return series.min()
    if func == "max":
        return series.max()
    if func == "avg":
        return series.mean()
    raise PlanExecutionError(f"unsupported aggregate: {func}")


def _group_projection(df: pd.DataFrame, key_exprs: List[Any], items: Sequence[Tuple[str, Any]]) -> pd.DataFrame:
    work = df.copy()
    key_cols: List[str] = []
    expr_to_col: Dict[Any, str] = {}
    for i, key_expr in enumerate(key_exprs):
        col = f"__grp_{i}"
        work[col] = _eval_expr_series(work, key_expr)
        key_cols.append(col)
        expr_to_col[key_expr] = col
    gb = work.groupby(key_cols, dropna=False, sort=False)
    base = gb.size().reset_index(name="__count_star__")

    out = pd.DataFrame(index=base.index)
    for alias, expr in items:
        agg = _parse_agg(expr)
        if agg is not None:
            func, arg = agg
            if func == "count" and arg == "*":
                out[alias] = base["__count_star__"]
                continue
            tmp = work.copy()
            tmp["__agg_val__"] = _eval_expr_series(tmp, arg)
            gb_agg = tmp.groupby(key_cols, dropna=False, sort=False)["__agg_val__"]
            if func == "count":
                agg_df = gb_agg.count().reset_index(name="__val__")
            elif func == "sum":
                agg_df = gb_agg.sum().reset_index(name="__val__")
            elif func == "min":
                agg_df = gb_agg.min().reset_index(name="__val__")
            elif func == "max":
                agg_df = gb_agg.max().reset_index(name="__val__")
            elif func == "avg":
                agg_df = gb_agg.mean().reset_index(name="__val__")
            else:
                raise PlanExecutionError(f"unsupported aggregate function: {func}")
            merged = base.merge(agg_df, on=key_cols, how="left")
            out[alias] = merged["__val__"]
            continue

        if expr in expr_to_col:
            out[alias] = base[expr_to_col[expr]]
            continue

        # Non-aggregate expression in grouped projection: evaluate against grouped base
        eval_df = base.copy()
        for key_expr, key_col in expr_to_col.items():
            eval_df[key_expr] = base[key_col]
        out[alias] = _eval_expr_series(eval_df, expr)

    return out.reset_index(drop=True)


def _with_context(out: pd.DataFrame, source: pd.DataFrame) -> pd.DataFrame:
    if len(out) != len(source):
        return out
    source_reset = source.reset_index(drop=True)
    out_reset = out.reset_index(drop=True)
    for col in source_reset.columns:
        ctx_col = f"{_CTX_PREFIX}{col}"
        if ctx_col in out_reset.columns:
            continue
        out_reset[ctx_col] = source_reset[col]
    return out_reset


def _drop_match_tag_columns(rows_df: pd.DataFrame, fixture: GraphFixture, table: str, source_alias: Optional[str]) -> pd.DataFrame:
    if len(rows_df) == 0:
        return rows_df

    if table == "nodes":
        known_cols = set(fixture.node_columns)
    else:
        known_cols = set(fixture.edge_columns)
    known_cols.update({"labels"})

    drop_cols = []
    for col in rows_df.columns:
        if col in known_cols:
            continue
        if isinstance(col, str) and col.startswith("label__"):
            continue
        series = rows_df[col]
        non_null = series.dropna()
        if pd.api.types.is_bool_dtype(series) or (
            len(non_null) > 0 and non_null.map(lambda v: isinstance(v, bool)).all()
        ):
            drop_cols.append(col)

    if not drop_cols:
        return rows_df
    return rows_df.drop(columns=drop_cols)


def _projection(df: pd.DataFrame, items: Sequence[Tuple[str, Any]], group_keys: Optional[List[str]]) -> pd.DataFrame:
    if group_keys:
        return _group_projection(df, group_keys, items)

    has_agg = any(_parse_agg(expr) is not None for _, expr in items)
    if has_agg:
        key_exprs = [expr for _, expr in items if _parse_agg(expr) is None]
        if key_exprs:
            return _group_projection(df, key_exprs, items)
        out_row: Dict[str, Any] = {}
        for alias, expr in items:
            agg = _parse_agg(expr)
            if agg is None:
                raise PlanExecutionError(
                    f"mixing aggregate and non-aggregate expressions without GROUP BY is unsupported: {expr}"
                )
            func, arg = agg
            out_row[alias] = _aggregate_series(df, func, arg)
        return pd.DataFrame([out_row])

    eval_df = df
    if len(df) == 0 and len(df.columns) == 0:
        eval_df = pd.DataFrame(index=[0])

    out = pd.DataFrame(index=eval_df.index)
    for alias, expr in items:
        out[alias] = _eval_expr_series(eval_df, expr)
    out = out.reset_index(drop=True)
    return _with_context(out, eval_df)


def _eval_unwind_expr(df: pd.DataFrame, expr: Any) -> Sequence[Any]:
    if isinstance(expr, Expr):
        series = _eval_expr_series(df, expr)
        expr_values: List[Any] = []
        for v in series.tolist():
            if isinstance(v, (list, tuple)):
                expr_values.extend(v)
            else:
                expr_values.append(v)
        return expr_values

    if not isinstance(expr, str):
        if isinstance(expr, (list, tuple)):
            return list(expr)
        raise PlanExecutionError(f"unsupported UNWIND expression: {expr!r}")

    txt = expr.strip()
    if txt.startswith("$"):
        raise PlanExecutionError(f"parameters not supported in UNWIND: {expr}")

    if txt in df.columns:
        series = df[txt]
        column_values: List[Any] = []
        for v in series.tolist():
            if isinstance(v, (list, tuple)):
                column_values.extend(v)
            else:
                column_values.append(v)
        return column_values

    subscript_match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_.]*)\s*\[\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\]", txt)
    if subscript_match:
        base_col = subscript_match.group(1)
        index_col = subscript_match.group(2)
        if base_col in df.columns and index_col in df.columns:
            values = []
            for base, idx in zip(df[base_col].tolist(), df[index_col].tolist()):
                if _is_null(base) or _is_null(idx):
                    continue
                if not isinstance(base, (list, tuple)):
                    raise PlanExecutionError(f"UNWIND base expression is not list-like: {base_col}")
                try:
                    values.append(base[int(idx)])
                except Exception as exc:
                    raise PlanExecutionError(f"UNWIND subscript failed for expression '{expr}': {exc}") from exc
            return values

    try:
        series = _eval_expr_series(df, txt)
        expanded_values: List[Any] = []
        for v in series.tolist():
            if isinstance(v, (list, tuple)):
                expanded_values.extend(v)
            else:
                expanded_values.append(v)
        return expanded_values
    except PlanExecutionError:
        pass

    try:
        parsed = ast.literal_eval(txt)
    except Exception as exc:
        raise PlanExecutionError(f"unsupported UNWIND expression '{expr}': {exc}") from exc
    if isinstance(parsed, (list, tuple)):
        return list(parsed)
    raise PlanExecutionError(f"UNWIND expression did not evaluate to list/tuple: {expr}")


def _is_empty_graph(graph: Any) -> bool:
    nodes_pdf = _to_pandas(getattr(graph, "_nodes", None))
    return nodes_pdf is None or len(nodes_pdf) == 0


def _can_treat_match_as_empty(graph: Any, exc: Exception) -> bool:
    message = str(exc).lower()
    if "column-not-found" not in message:
        return False
    return _is_empty_graph(graph)


def _empty_match_result(graph: Any, chain: Sequence[Any]) -> _SyntheticMatchResult:
    nodes_pdf = _to_pandas(getattr(graph, "_nodes", None))
    if nodes_pdf is None or nodes_pdf.empty:
        node_id_col = getattr(graph, "_node", "id")
        nodes_pdf = pd.DataFrame(columns=[node_id_col])
    else:
        nodes_pdf = nodes_pdf.iloc[0:0].copy()

    edges_pdf = _to_pandas(getattr(graph, "_edges", None))
    if edges_pdf is None:
        edge_cols = [getattr(graph, "_source", "src"), getattr(graph, "_destination", "dst"), getattr(graph, "_edge", "edge_id")]
        edges_pdf = pd.DataFrame(columns=edge_cols)
    else:
        edges_pdf = edges_pdf.iloc[0:0].copy()

    alias_cols = []
    for part in chain:
        alias = getattr(part, "name", None)
        if isinstance(alias, str) and alias:
            alias_cols.append(alias)
    for alias in alias_cols:
        if alias not in nodes_pdf.columns:
            nodes_pdf[alias] = pd.Series(dtype=bool)
        if alias not in edges_pdf.columns:
            edges_pdf[alias] = pd.Series(dtype=bool)

    return _SyntheticMatchResult(_nodes=nodes_pdf.iloc[0:0], _edges=edges_pdf.iloc[0:0])


def _rewrite_with_projection_aliases(expr: Any, alias_exprs: Optional[Dict[str, str]]) -> Any:
    if alias_exprs is None or not isinstance(expr, str):
        return expr
    rewritten = expr
    for src, alias in sorted(alias_exprs.items(), key=lambda item: len(item[0]), reverse=True):
        if src == alias:
            continue
        rewritten = rewritten.replace(src, alias)
    return rewritten


def _hashable_value(value: Any) -> Any:
    if _is_null(value):
        return ("null",)
    if isinstance(value, list):
        return tuple(_hashable_value(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_hashable_value(v) for v in value)
    if isinstance(value, dict):
        return tuple((k, _hashable_value(v)) for k, v in sorted(value.items()))
    return value


def _drop_duplicates_safe(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) == 0:
        return df.reset_index(drop=True)
    key_df = pd.DataFrame(
        {col: df[col].map(_hashable_value) for col in df.columns},
        index=df.index,
    )
    mask = ~key_df.duplicated(keep="first")
    return df.loc[mask].reset_index(drop=True)


def execute_plan(graph: Any, fixture: GraphFixture, steps: Sequence[PlanStep]) -> pd.DataFrame:
    state = PlanState(graph=graph, fixture=fixture, frame=pd.DataFrame(), alias_exprs=None)

    for step in steps:
        op = step.op
        args = step.args

        if op == "raw":
            raise PlanExecutionError("raw plan steps are non-executable placeholders")

        if op == "invalid":
            raise PlanExecutionError(str(args.get("note", "invalid plan step")))

        if op == "match":
            if "chain" in args:
                chain = list(args["chain"])
                try:
                    state.match_result = state.graph.gfql(chain, engine="pandas")
                except Exception as exc:
                    if _can_treat_match_as_empty(state.graph, exc):
                        state.match_result = _empty_match_result(state.graph, chain)
                    else:
                        raise
                state.group_keys = None
                state.alias_exprs = None
                continue
            raise PlanExecutionError("only match(chain=...) steps are executable")

        if op == "rows":
            if state.match_result is None:
                raise PlanExecutionError("rows step requires a preceding executable match step")
            table = str(args.get("table", "nodes"))
            source = args.get("source")
            if table == "nodes":
                rows_df = _to_pandas(state.match_result._nodes).copy()
            elif table == "edges":
                rows_df = _to_pandas(state.match_result._edges).copy()
            else:
                raise PlanExecutionError(f"unsupported rows table: {table}")

            if source is not None:
                source_str = str(source)
                if source_str not in rows_df.columns and len(rows_df) == 0:
                    rows_df[source_str] = pd.Series(dtype=bool)
                if source_str not in rows_df.columns:
                    raise PlanExecutionError(f"rows source alias not present in match output: {source_str}")
                rows_df = rows_df.loc[rows_df[source_str].astype(bool)].copy()
                rows_df = _drop_match_tag_columns(rows_df, fixture, table, source_str)
                rows_df = _add_alias_columns(rows_df, source_str, fixture, table)

            state.frame = rows_df.reset_index(drop=True)
            state.group_keys = None
            continue

        if op == "group_by":
            keys = args.get("keys", ())
            state.group_keys = [str(k) for k in keys]
            continue

        if op in {"select", "with"}:
            items = args.get("items", ())
            state.frame = _projection(state.frame, list(items), state.group_keys)
            state.group_keys = None
            alias_exprs = {}
            for alias, expr in items:
                if isinstance(expr, str):
                    alias_exprs[str(expr)] = str(alias)
            state.alias_exprs = alias_exprs
            continue

        if op == "distinct":
            state.frame = _drop_duplicates_safe(state.frame)
            continue

        if op == "where":
            expr = args.get("expr")
            mask = _eval_expr_series(state.frame, expr)
            if not isinstance(mask, pd.Series):
                mask = pd.Series([bool(mask)] * len(state.frame), index=state.frame.index)
            if mask.dtype != bool:
                mask = mask.astype(bool)
            state.frame = state.frame.loc[mask].reset_index(drop=True)
            state.group_keys = None
            state.alias_exprs = None
            continue

        if op == "order_by":
            keys = list(args.get("keys", ()))
            sort_cols: List[str] = []
            ascending: List[bool] = []
            work = state.frame.copy()
            for i, (expr, direction) in enumerate(keys):
                col = f"__sort_{i}"
                expr_for_eval = _rewrite_with_projection_aliases(expr, state.alias_exprs)
                work[col] = _eval_expr_series(work, expr_for_eval)
                sort_cols.append(col)
                ascending.append(str(direction).lower() != "desc")
            if sort_cols:
                work = work.sort_values(by=sort_cols, ascending=ascending, kind="mergesort")
                work = work.drop(columns=sort_cols)
            state.frame = work.reset_index(drop=True)
            continue

        if op == "skip":
            v = _eval_scalar_limit_skip(args.get("value"))
            if v < 0:
                raise PlanExecutionError("negative SKIP is invalid")
            state.frame = state.frame.iloc[v:].reset_index(drop=True)
            continue

        if op == "limit":
            v = _eval_scalar_limit_skip(args.get("value"))
            if v < 0:
                raise PlanExecutionError("negative LIMIT is invalid")
            state.frame = state.frame.iloc[:v].reset_index(drop=True)
            continue

        if op == "unwind":
            as_name = str(args.get("as_", "value"))
            base_rows: List[Dict[str, Any]]
            if state.frame.empty and len(state.frame.columns) == 0:
                base_rows = [{}]
            else:
                base_rows = state.frame.to_dict("records")

            out_rows: List[Dict[str, Any]] = []
            for row in base_rows:
                row_df = pd.DataFrame([row]) if row else pd.DataFrame(index=[0])
                values = _eval_unwind_expr(row_df, args.get("expr"))
                for value in values:
                    next_row = dict(row)
                    next_row[as_name] = value
                    out_rows.append(next_row)
            state.frame = pd.DataFrame(out_rows)
            state.group_keys = None
            state.alias_exprs = None
            continue

        raise PlanExecutionError(f"unsupported plan step: {op}")

    out = state.frame.reset_index(drop=True)
    drop_cols = [c for c in out.columns if isinstance(c, str) and c.startswith(_CTX_PREFIX)]
    if drop_cols:
        out = out.drop(columns=drop_cols)
    return out
