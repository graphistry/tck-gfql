from __future__ import annotations

import pandas as pd

from tests.cypher_tck.gfql_plan import Expr
from tests.cypher_tck.plan_executor import _aggregate_series, _parse_agg


def test_parse_agg_collect_string() -> None:
    parsed = _parse_agg("collect(v)")
    assert parsed == ("collect", "v")


def test_parse_agg_collect_expr() -> None:
    parsed = _parse_agg(Expr(op="func", args={"name": "collect", "args": (Expr(op="col", args={"name": "v"}),)}))
    assert parsed is not None
    assert parsed[0] == "collect"


def test_aggregate_series_collect_ignores_nulls() -> None:
    df = pd.DataFrame({"v": [1, None, 3]})
    out = _aggregate_series(df, "collect", "v")
    assert out == [1.0, 3.0]

