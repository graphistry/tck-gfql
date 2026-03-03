from __future__ import annotations

import ast
import math
import random
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

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
    "toInteger",
    "ceil",
    "rand",
    "collect",
    "nodes",
    "length",
    "head",
}
_CTX_PREFIX = "__ctx__"


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
            items = [_expr_literal_value(item) for item in expr.args.get("items", ())]
            return pd.Series([items] * len(df), index=df.index)
        if expr.op == "map":
            mapping = {str(k): _expr_literal_value(v) for k, v in expr.args.get("items", ())}
            return pd.Series([mapping] * len(df), index=df.index)
        if expr.op == "col":
            name = str(expr.args.get("name"))
            if name not in df.columns:
                raise PlanExecutionError(f"unknown column in expression: {name}")
            return df[name]
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
        if base in df.columns or f"{_CTX_PREFIX}{base}" in df.columns:
            return pd.Series([None] * len(df), index=df.index)

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


def _parse_agg(expr: Any) -> Optional[Tuple[str, str]]:
    if isinstance(expr, Expr):
        return None
    if not isinstance(expr, str):
        return None
    m = _AGG_RE.match(expr.strip())
    if not m:
        return None
    return m.group(1).lower(), m.group(2).strip()


def _aggregate_series(df: pd.DataFrame, func: str, arg: str) -> Any:
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


def _group_projection(df: pd.DataFrame, key_exprs: List[str], items: Sequence[Tuple[str, Any]]) -> pd.DataFrame:
    work = df.copy()
    key_cols: List[str] = []
    expr_to_col: Dict[str, str] = {}
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

        if isinstance(expr, str) and expr in expr_to_col:
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
        if expr.op == "list":
            return [_expr_literal_value(item) for item in expr.args.get("items", ())]
        if expr.op == "col":
            col_name = str(expr.args.get("name", ""))
            if col_name not in df.columns:
                raise PlanExecutionError(f"UNWIND column not present: {col_name}")
            values: List[Any] = []
            for v in df[col_name].tolist():
                if isinstance(v, (list, tuple)):
                    values.extend(v)
                else:
                    values.append(v)
            return values
        raise PlanExecutionError(f"unsupported UNWIND Expr: {expr.op}")

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
