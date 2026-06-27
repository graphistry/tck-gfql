import os
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, Iterable, List, Sequence

import pandas as pd
import pytest

from graphistry.compute.exceptions import GFQLValidationError
from graphistry.embed_utils import check_cudf
from graphistry.gfql.ref.enumerator import OracleCaps, enumerate_chain
from graphistry.tests.test_compute import CGFull

from tests.cypher_tck.comparator import (
    render_expected_error_mismatch,
    render_row_mismatch,
)
from tests.cypher_tck.direct_cypher_xfail_contract import (
    DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY,
    DIRECT_CYPHER_PROMOTED_FROM_XFAIL_MATCHES_EXPECTED_KEYS,
    DIRECT_CYPHER_XFAIL_MATCHES_EXPECTED_BASE_KEYS,
    DIRECT_CYPHER_XFAIL_MATCHES_EXPECTED_KEYS,
    DIRECT_CYPHER_XFAIL_VALIDATION_OUTCOME,
    expected_direct_cypher_xfail_outcome,
)
from tests.cypher_tck.direct_cypher_support import (
    DIRECT_CYPHER_PROMOTION_ERROR_KEYS,
    DIRECT_CYPHER_PROMOTION_KEYS,
)
from tests.cypher_tck.gfql_plan import PlanStep, col, order_by
from tests.cypher_tck.models import Expected, GraphFixture, Scenario
from tests.cypher_tck.parse_cypher import _parse_literal
from tests.cypher_tck.plan_executor import execute_plan
from tests.cypher_tck.scenarios import SCENARIOS
from tests.cypher_tck.typed_schema_support import (
    bind_schema_for_scenario,
    is_typed_schema_scenario,
    validate_typed_schema_scenario,
)


_HAS_CUDF, _ = check_cudf()
_TEST_CUDF = os.environ.get("TEST_CUDF", "0") == "1"
_STRICT_PURE = os.environ.get("TCK_STRICT_PURE", "0") == "1"


def _check_polars() -> bool:
    try:
        import polars  # noqa: F401
        return True
    except Exception:
        return False


# Validate the native PyGraphistry Polars GFQL engine (pygraphistry #1648/#1649)
# against the same expected TCK results as pandas. Opt-in via TEST_POLARS=1, like
# TEST_CUDF for the cuDF engine.
_HAS_POLARS = _check_polars()
_TEST_POLARS = os.environ.get("TEST_POLARS", "0") == "1"
_NUMERIC_ROW_EQUIVALENCE_KEYS = {
    "expr-aggregation3-1",
    "expr-literals5-5",
    "expr-literals5-6",
    "expr-literals5-11",
    "expr-literals5-12",
    "expr-literals5-25",
    "expr-literals5-26",
}
_STRING_KEYWORD_ROW_EQUIVALENCE_KEYS = {
    "expr-typeconversion4-2",
    "expr-typeconversion4-3",
    "expr-typeconversion4-4",
    "expr-typeconversion4-5",
}
_NUMERIC_CONTAINER_ROW_EQUIVALENCE_KEYS = {
    "expr-literals7-7",
    "expr-literals8-11",
}
_LABEL_ORDER_ROW_EQUIVALENCE_KEYS = {
    "match3-7",
}
_MAP_KEY_ORDER_ROW_EQUIVALENCE_KEYS = {
    "expr-literals7-18",
    "expr-literals8-18",
}
_NETWORKX_SMOKE_ALGORITHM_BY_ERROR_KEY = {
    "firstparty-networkx-closeness-centrality-error-1": "closeness_centrality",
    "firstparty-networkx-connected-components-error-1": "connected_components",
    "firstparty-networkx-core-number-error-1": "core_number",
    "firstparty-networkx-degree-centrality-error-1": "degree_centrality",
    "firstparty-networkx-eigenvector-centrality-error-1": "eigenvector_centrality",
    "firstparty-networkx-hits-error-1": "hits",
    "firstparty-networkx-katz-centrality-error-1": "katz_centrality",
    "firstparty-networkx-strongly-connected-components-error-1": "strongly_connected_components",
}
_NUMERIC_TOKEN_PATTERN = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_NUMERIC_STRING_RE = re.compile(rf"^{_NUMERIC_TOKEN_PATTERN}$")
_NUMERIC_LIST_STRING_RE = re.compile(rf"^\[\s*({_NUMERIC_TOKEN_PATTERN})\s*\]$")
_NUMERIC_MAP_STRING_RE = re.compile(
    rf"^\{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*({_NUMERIC_TOKEN_PATTERN})\s*\}}$"
)
_SIMPLE_NODE_LABELS_RE = re.compile(r"^\(:([A-Za-z_][A-Za-z0-9_]*(?::[A-Za-z_][A-Za-z0-9_]*)*)\)$")
_NUMERIC_ROW_VALUE_PREFIX = "__tck_numeric__:"


def _df_from_records(records: Sequence[dict], required_cols: Iterable[str]) -> pd.DataFrame:
    if records:
        df = pd.DataFrame(records)
        for col in required_cols:
            if col not in df.columns:
                df[col] = pd.NA
        return df
    return pd.DataFrame(columns=list(required_cols))


def _normalize_labels(value: Any) -> Sequence[str]:
    if value is None:
        return []
    if isinstance(value, float) and pd.isna(value):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _expand_label_columns(nodes_df: pd.DataFrame, label_col: str = "labels") -> pd.DataFrame:
    if label_col not in nodes_df.columns:
        return nodes_df
    normalized = [_normalize_labels(value) for value in nodes_df[label_col].tolist()]
    all_labels = sorted({label for labels in normalized for label in labels})
    for label in all_labels:
        nodes_df[f"label__{label}"] = [label in labels for labels in normalized]
    return nodes_df


def _build_graph(fixture: GraphFixture) -> Any:
    g: Any = CGFull()  # type: ignore[abstract]
    nodes_df = _df_from_records(fixture.nodes, fixture.node_columns)
    nodes_df = _expand_label_columns(nodes_df)
    g = g.nodes(nodes_df, fixture.node_id)
    edges_df = _df_from_records(fixture.edges, fixture.edge_columns)
    g = g.edges(edges_df, fixture.src, fixture.dst, edge=fixture.edge_id)
    return g


def _to_pandas(df: Any) -> Any:
    if df is None:
        return None
    return df.to_pandas() if hasattr(df, "to_pandas") else df


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


def _normalize_row_value(value: Any, *, quote_keyword_strings: bool = False) -> Any:
    if hasattr(value, "item") and not isinstance(value, (str, bytes, list, tuple, dict)):
        try:
            value = value.item()
        except Exception:
            pass

    if _is_null(value):
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        if value.startswith(_NUMERIC_ROW_VALUE_PREFIX):
            return value
        if value.startswith(("(", "[", "{", "<")):
            return value
        if value.startswith("'") and value.endswith("'") and len(value) > 1:
            return value
        if value in {"null", "true", "false"} and not quote_keyword_strings:
            return value
        escaped = (
            value
            .replace("\\", "\\\\")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
            .replace("'", "\\'")
        )
        return f"'{escaped}'"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(
            str(_normalize_row_value(v, quote_keyword_strings=quote_keyword_strings))
            for v in value
        ) + "]"
    if isinstance(value, dict):
        parts = []
        for key in sorted(value.keys()):
            parts.append(
                f"{key}: {_normalize_row_value(value[key], quote_keyword_strings=quote_keyword_strings)}"
            )
        return "{" + ", ".join(parts) + "}"
    return value


def _normalize_numeric_row_value(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return f"{_NUMERIC_ROW_VALUE_PREFIX}{Decimal(value).normalize()}"
    if isinstance(value, float):
        return f"{_NUMERIC_ROW_VALUE_PREFIX}{Decimal(str(value)).normalize()}"
    if isinstance(value, str) and _NUMERIC_STRING_RE.fullmatch(value):
        try:
            return f"{_NUMERIC_ROW_VALUE_PREFIX}{Decimal(value).normalize()}"
        except InvalidOperation:
            return value
    return value


def _normalize_numeric_container_row_value(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return [_normalize_numeric_container_row_value(v) for v in value]
    if isinstance(value, dict):
        return {
            key: _normalize_numeric_container_row_value(nested)
            for key, nested in value.items()
        }
    if isinstance(value, str):
        list_match = _NUMERIC_LIST_STRING_RE.fullmatch(value)
        if list_match:
            return [_normalize_numeric_row_value(list_match.group(1))]
        map_match = _NUMERIC_MAP_STRING_RE.fullmatch(value)
        if map_match:
            return {
                map_match.group(1): _normalize_numeric_row_value(map_match.group(2))
            }
    return _normalize_numeric_row_value(value)


def _normalize_label_order_row_value(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return [_normalize_label_order_row_value(v) for v in value]
    if isinstance(value, dict):
        return {
            key: _normalize_label_order_row_value(nested)
            for key, nested in value.items()
        }
    if isinstance(value, str):
        match = _SIMPLE_NODE_LABELS_RE.fullmatch(value)
        if match:
            labels = sorted(match.group(1).split(":"))
            return "(:" + ":".join(labels) + ")"
    return value


def _normalize_map_key_order_row_value(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return [_normalize_map_key_order_row_value(v) for v in value]
    if isinstance(value, dict):
        return {
            key: _normalize_map_key_order_row_value(nested)
            for key, nested in value.items()
        }
    if isinstance(value, str) and value.startswith(("[", "{")):
        try:
            return _parse_literal(value, {})
        except Exception:
            return value
    return value


def _normalize_rows(
    rows: Sequence[Dict[str, Any]],
    expected_keys: Sequence[str],
    *,
    numeric_equivalence: bool = False,
    quote_keyword_strings: bool = False,
    numeric_container_equivalence: bool = False,
    label_order_equivalence: bool = False,
    map_key_order_equivalence: bool = False,
) -> List[Dict[str, Any]]:
    normalized = []
    for row in rows:
        missing = [k for k in expected_keys if k not in row]
        assert not missing, f"missing expected row columns: {missing}; row={row}"
        normalized_row = {}
        for key in expected_keys:
            value = row[key]
            if numeric_equivalence:
                value = _normalize_numeric_row_value(value)
            if numeric_container_equivalence:
                value = _normalize_numeric_container_row_value(value)
            if label_order_equivalence:
                value = _normalize_label_order_row_value(value)
            if map_key_order_equivalence:
                value = _normalize_map_key_order_row_value(value)
            normalized_row[key] = _normalize_row_value(
                value,
                quote_keyword_strings=quote_keyword_strings,
            )
        normalized.append(normalized_row)
    return normalized


def _rows_ordered(scenario: Scenario) -> bool:
    if scenario.expected.ordered is not None:
        return scenario.expected.ordered
    if scenario.gfql is None:
        return False
    for step in scenario.gfql:
        if isinstance(step, PlanStep) and step.op in {"order_by", "skip", "limit"}:
            return True
    return False


def _assert_expected_rows(scenario: Scenario, actual_rows: Sequence[Dict[str, Any]]) -> None:
    if scenario.expected.rows is None:
        return

    expected_rows = scenario.expected.rows
    if len(expected_rows) == 0:
        assert len(actual_rows) == 0, (
            f"expected no rows but received {len(actual_rows)} rows for scenario {scenario.key}: "
            f"{actual_rows}"
        )
        return

    expected_keys = sorted({key for row in expected_rows for key in row.keys()})
    numeric_equivalence = scenario.key in _NUMERIC_ROW_EQUIVALENCE_KEYS
    quote_keyword_strings = scenario.key in _STRING_KEYWORD_ROW_EQUIVALENCE_KEYS
    numeric_container_equivalence = (
        scenario.key in _NUMERIC_CONTAINER_ROW_EQUIVALENCE_KEYS
    )
    label_order_equivalence = scenario.key in _LABEL_ORDER_ROW_EQUIVALENCE_KEYS
    map_key_order_equivalence = scenario.key in _MAP_KEY_ORDER_ROW_EQUIVALENCE_KEYS
    expected_norm = _normalize_rows(
        expected_rows,
        expected_keys,
        numeric_equivalence=numeric_equivalence,
        quote_keyword_strings=quote_keyword_strings,
        numeric_container_equivalence=numeric_container_equivalence,
        label_order_equivalence=label_order_equivalence,
        map_key_order_equivalence=map_key_order_equivalence,
    )
    actual_norm = _normalize_rows(
        actual_rows,
        expected_keys,
        numeric_equivalence=numeric_equivalence,
        quote_keyword_strings=quote_keyword_strings,
        numeric_container_equivalence=numeric_container_equivalence,
        label_order_equivalence=label_order_equivalence,
        map_key_order_equivalence=map_key_order_equivalence,
    )

    if _rows_ordered(scenario):
        assert actual_norm == expected_norm, (
            render_row_mismatch(
                scenario_key=scenario.key,
                expected_rows=expected_norm,
                actual_rows=actual_norm,
                expected_columns=expected_keys,
                ordered=True,
            )
        )
        return

    def _row_key(row: Dict[str, Any]) -> str:
        return "|".join(f"{key}={row[key]!r}" for key in expected_keys)

    actual_sorted = sorted(_row_key(row) for row in actual_norm)
    expected_sorted = sorted(_row_key(row) for row in expected_norm)
    assert actual_sorted == expected_sorted, (
        render_row_mismatch(
            scenario_key=scenario.key,
            expected_rows=expected_norm,
            actual_rows=actual_norm,
            expected_columns=expected_keys,
            ordered=False,
        )
    )


def _assert_expected_error(
    scenario: Scenario,
    operation: Callable[[], object],
    *,
    expected: str,
) -> None:
    try:
        operation()
    except Exception:
        return

    assert False, render_expected_error_mismatch(
        scenario_key=scenario.key,
        expected=expected,
        actual="success",
    )


def test_rows_ordered_uses_explicit_expected_flag_when_present() -> None:
    scenario = Scenario(
        key="unit-ordered-flag",
        feature_path="unit.feature",
        scenario="unit",
        cypher="RETURN 1",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"x": 1}], ordered=False),
        gfql=(order_by(((col("x"), "asc"),)),),
        status="supported",
    )
    assert _rows_ordered(scenario) is False


def test_rows_ordered_falls_back_to_plan_steps_without_expected_flag() -> None:
    scenario = Scenario(
        key="unit-fallback-orderby",
        feature_path="unit.feature",
        scenario="unit",
        cypher="RETURN 1",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"x": 1}]),
        gfql=(order_by(((col("x"), "asc"),)),),
        status="supported",
    )
    assert _rows_ordered(scenario) is True


def test_with_orderby_issue36_keys_are_marked_unordered() -> None:
    for key in (
        "with-orderby1-31-1",
        "with-orderby1-31-2",
        "with-orderby1-31-3",
        "with-orderby1-32-1",
        "with-orderby1-32-2",
        "with-orderby2-7-1",
        "with-orderby2-7-2",
        "with-orderby2-7-3",
        "with-orderby3-2-1",
        "with-orderby3-2-2",
        "with-orderby3-2-3",
        "with-orderby3-2-4",
        "with-orderby3-2-5",
        "with-orderby3-2-6",
    ):
        scenario = next(s for s in SCENARIOS if s.key == key)
        assert scenario.expected.ordered is False
        assert _rows_ordered(scenario) is False


def test_first_party_networkx_smoke_scenarios_are_loaded() -> None:
    keys = {scenario.key for scenario in SCENARIOS}

    assert {
        "firstparty-networkx-closeness-centrality-1",
        "firstparty-networkx-connected-components-1",
        "firstparty-networkx-core-number-1",
        "firstparty-networkx-degree-centrality-1",
        "firstparty-networkx-eigenvector-centrality-1",
        "firstparty-networkx-hits-1",
        "firstparty-networkx-hits-write-1",
        "firstparty-networkx-katz-centrality-1",
        "firstparty-networkx-strongly-connected-components-1",
    }.issubset(keys)


@pytest.mark.parametrize(
    ("key", "algorithm"),
    sorted(_NETWORKX_SMOKE_ALGORITHM_BY_ERROR_KEY.items()),
)
def test_first_party_networkx_error_smokes_use_structured_diagnostics(
    key: str,
    algorithm: str,
) -> None:
    pytest.importorskip("networkx")
    scenario = next(scenario for scenario in SCENARIOS if scenario.key == key)
    graph = _build_graph(scenario.graph)

    with pytest.raises(GFQLValidationError) as exc_info:
        graph.gfql(scenario.cypher, params=scenario.params, engine="pandas")

    assert exc_info.value.code == "unsupported-cypher-query"
    assert exc_info.value.context["field"] == "call.args"
    assert exc_info.value.context["value"] == {"bogus_option": 1}
    assert f"graphistry.nx.{algorithm}" in str(exc_info.value)


def test_first_party_networkx_hits_write_smoke_writes_score_columns() -> None:
    pytest.importorskip("networkx")
    scenario = next(
        scenario
        for scenario in SCENARIOS
        if scenario.key == "firstparty-networkx-hits-write-1"
    )
    graph = _build_graph(scenario.graph)

    result = graph.gfql(scenario.cypher, params=scenario.params, engine="pandas")
    nodes = getattr(result, "_nodes", None)

    assert nodes is not None
    assert {"hubs", "authorities"}.issubset(set(nodes.columns))
    assert not nodes["hubs"].isna().any()
    assert not nodes["authorities"].isna().any()


def test_numeric_row_equivalence_is_allowlisted_for_float_formatting() -> None:
    scenario = Scenario(
        key="expr-aggregation3-1",
        feature_path="unit.feature",
        scenario="unit",
        cypher="RETURN 75",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"sum(n.num)": 75}]),
        gfql=None,
        status="xfail",
    )

    _assert_expected_rows(scenario, [{"sum(n.num)": 75.0}])


def test_numeric_string_equivalence_is_allowlisted_for_exponent_formatting() -> None:
    scenario = Scenario(
        key="expr-literals5-5",
        feature_path="unit.feature",
        scenario="unit",
        cypher="RETURN 1e305",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"literal": "1.2635418652381264e305"}]),
        gfql=None,
        status="xfail",
    )

    _assert_expected_rows(scenario, [{"literal": 1.2635418652381264e305}])


def test_numeric_string_equivalence_is_not_global() -> None:
    scenario = Scenario(
        key="unit-string-number",
        feature_path="unit.feature",
        scenario="unit",
        cypher="RETURN '1'",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"value": "1"}]),
        gfql=None,
        status="supported",
    )

    with pytest.raises(AssertionError, match="unordered row mismatch"):
        _assert_expected_rows(scenario, [{"value": 1}])


def test_string_keyword_equivalence_is_allowlisted_for_to_string_boolean() -> None:
    scenario = Scenario(
        key="expr-typeconversion4-2",
        feature_path="unit.feature",
        scenario="unit",
        cypher="RETURN toString(true)",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"bool": "'true'"}]),
        gfql=None,
        status="xfail",
    )

    _assert_expected_rows(scenario, [{"bool": "true"}])


def test_string_keyword_equivalence_is_recursive_for_to_string_lists() -> None:
    scenario = Scenario(
        key="expr-typeconversion4-5",
        feature_path="unit.feature",
        scenario="unit",
        cypher="RETURN [toString(true)]",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"list": "['1', '2.3', 'true', 'apa']"}]),
        gfql=None,
        status="xfail",
    )

    _assert_expected_rows(scenario, [{"list": ["1", "2.3", "true", "apa"]}])


def test_string_keyword_equivalence_is_not_global() -> None:
    scenario = Scenario(
        key="unit-boolean-keyword",
        feature_path="unit.feature",
        scenario="unit",
        cypher="RETURN true",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"value": "'true'"}]),
        gfql=None,
        status="supported",
    )

    with pytest.raises(AssertionError, match="unordered row mismatch"):
        _assert_expected_rows(scenario, [{"value": "true"}])


def test_numeric_container_equivalence_is_allowlisted_for_list_literals() -> None:
    scenario = Scenario(
        key="expr-literals7-7",
        feature_path="unit.feature",
        scenario="unit",
        cypher="RETURN [-.1e-5]",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"literal": "[-0.000001]"}]),
        gfql=None,
        status="xfail",
    )

    _assert_expected_rows(scenario, [{"literal": [-1e-06]}])


def test_numeric_container_equivalence_is_allowlisted_for_map_literals() -> None:
    scenario = Scenario(
        key="expr-literals8-11",
        feature_path="unit.feature",
        scenario="unit",
        cypher="RETURN {k: -.1e-5}",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"literal": "{k: -0.000001}"}]),
        gfql=None,
        status="xfail",
    )

    _assert_expected_rows(scenario, [{"literal": {"k": -1e-06}}])


def test_numeric_container_equivalence_is_not_global() -> None:
    scenario = Scenario(
        key="unit-numeric-container",
        feature_path="unit.feature",
        scenario="unit",
        cypher="RETURN [-.1e-5]",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"literal": "[-0.000001]"}]),
        gfql=None,
        status="supported",
    )

    with pytest.raises(AssertionError, match="unordered row mismatch"):
        _assert_expected_rows(scenario, [{"literal": [-1e-06]}])


def test_label_order_equivalence_is_allowlisted_for_node_labels() -> None:
    scenario = Scenario(
        key="match3-7",
        feature_path="unit.feature",
        scenario="unit",
        cypher="MATCH (n:A:B)-[:T]->(m:Z:Y) RETURN n, m",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"m": "(:Z:Y)"}]),
        gfql=None,
        status="xfail",
    )

    _assert_expected_rows(scenario, [{"m": "(:Y:Z)"}])


def test_label_order_equivalence_is_not_global() -> None:
    scenario = Scenario(
        key="unit-label-order",
        feature_path="unit.feature",
        scenario="unit",
        cypher="MATCH (n:A:B) RETURN n",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"n": "(:B:A)"}]),
        gfql=None,
        status="supported",
    )

    with pytest.raises(AssertionError, match="unordered row mismatch"):
        _assert_expected_rows(scenario, [{"n": "(:A:B)"}])


def test_map_key_order_equivalence_is_allowlisted_for_nested_literals() -> None:
    scenario = Scenario(
        key="expr-literals8-18",
        feature_path="unit.feature",
        scenario="unit",
        cypher="RETURN {b: {d: 'z', c: [2, 1]}, a: 3} AS literal",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"literal": "{b: {d: 'z', c: [2, 1]}, a: 3}"}]),
        gfql=None,
        status="xfail",
    )

    _assert_expected_rows(
        scenario,
        [{"literal": "{a: 3, b: {c: [2, 1], d: 'z'}}"}],
    )


def test_map_key_order_equivalence_is_not_global() -> None:
    scenario = Scenario(
        key="unit-map-key-order",
        feature_path="unit.feature",
        scenario="unit",
        cypher="RETURN {b: 1, a: 2} AS literal",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[{"literal": "{b: 1, a: 2}"}]),
        gfql=None,
        status="supported",
    )

    with pytest.raises(AssertionError, match="unordered row mismatch"):
        _assert_expected_rows(scenario, [{"literal": "{a: 2, b: 1}"}])


def _ids_from_df(df: Any, id_col: str) -> set:
    if df is None:
        return set()
    pdf = _to_pandas(df)
    if pdf is None or id_col not in pdf.columns:
        return set()
    return set(pdf[id_col])


def _alias_nodes(df: Any, id_col: str, alias: str) -> set:
    if df is None:
        return set()
    pdf = _to_pandas(df)
    if pdf is None or alias not in pdf.columns:
        return set()
    return set(pdf.loc[pdf[alias].astype(bool), id_col])




def _is_cypher_string_supported(scenario: Scenario) -> bool:
    return scenario.status == "supported" and "cypher-string" in scenario.tags


def _is_cypher_string_error(scenario: Scenario) -> bool:
    return _is_cypher_string_supported(scenario) and "cypher-string-error" in scenario.tags


def _whole_entity_aliases(cols: List[str], meta: Any) -> Dict[str, str]:
    """Map ``alias -> table`` for flat ``alias.field`` groups that are WHOLE
    entities (collapse to Cypher text), excluding property projections (stay flat).

    Two signals, unioned:

    * ``_cypher_entity_projection_meta`` records whole-entity aliases that carry an
      id column (the reentry/OPTIONAL payload) — used when present.
    * Structural marker: a ``{alias}.label__*`` (node one-hot label) column. These
      appear ONLY from whole-entity flattening — a scalar property return
      (``RETURN a.val``) never emits ``label__*``. This catches label-only / id-less
      nodes (``MATCH (a) ... RETURN a`` on a labeled, property-less graph), for which
      #1650 emits flat columns but records NO meta (no id column → not a reentry
      payload). The double-underscore guard avoids colliding with a user property
      literally named ``label``.
    """
    aliases: Dict[str, str] = {}
    if isinstance(meta, dict):
        for alias, entry in meta.items():
            aliases[str(alias)] = entry.get("table", "nodes") if isinstance(entry, dict) else "nodes"
    for col in cols:
        marker = ".label__"
        idx = col.find(marker)
        if idx > 0:
            aliases.setdefault(col[:idx], "nodes")  # node label one-hot ⇒ whole node
    return aliases


def _collapse_structured_returns(result: Any) -> Any:
    """Adapter for pygraphistry #1650 structured whole-entity returns.

    Since #1656, a terminal ``RETURN a`` (whole node/edge) emits FLAT
    ``a.id, a.val, …`` columns instead of a single Cypher display-string ``a``
    column. The TCK oracle expects the display string, so reconstruct it from the
    flat columns via pygraphistry's ``render_entity_text`` — but ONLY for aliases
    that are WHOLE-ENTITY projections (see :func:`_whole_entity_aliases`);
    property projections like ``RETURN a.val`` legitimately stay flat (the expected
    rows carry ``a.val`` too). No-op on the legacy single-column shape (pre-#1656
    pygraphistry, or an absent-entity row that already collapsed to text)."""
    nodes = getattr(result, "_nodes", None)
    if nodes is None:
        return result
    cols = [str(c) for c in nodes.columns]
    meta = getattr(result, "_cypher_entity_projection_meta", None)
    aliases = _whole_entity_aliases(cols, meta)
    if not aliases:
        return result
    try:
        from graphistry.compute.gfql.cypher.result_postprocess import render_entity_text
    except Exception:
        return result
    # render_entity_text uses pandas-style frame ops, so run it against a
    # pandas-backed copy of the result (the native polars engine returns a polars
    # _nodes frame; rendering on it directly raises and the collapse is skipped,
    # leaking flat ``a.label__*`` columns — the with-orderby polars failures).
    pdf = _to_pandas(nodes)
    pres = result.bind()
    pres._nodes = pdf
    changed = False
    for alias, table in aliases.items():
        prefix = f"{alias}."
        flat = [c for c in cols if c.startswith(prefix)]
        if not flat:
            continue  # absent-entity row already single-column, or property-only
        try:
            text = render_entity_text(pres, alias, table=table)
            text = _to_pandas(text) if hasattr(text, "to_pandas") else text
        except Exception:
            continue
        pdf = pdf.drop(columns=[c for c in flat if c in pdf.columns])
        pdf[alias] = list(text)
        changed = True
    if not changed:
        return result
    out = result.bind()
    out._nodes = pdf
    return out


_POLARS_NOT_IMPLEMENTED: List[str] = []


def _assert_polars_engine(g: Any, scenario: "Scenario") -> None:
    """Validate the native polars engine, tolerating honest ``NotImplementedError``.

    Per NO-CHEATING (plans/gfql-polars-engine), the native polars engine raises
    ``NotImplementedError`` for Cypher ops it does not yet support NATIVELY — there
    is deliberately NO pandas fallback. That is an honest partial-coverage decline,
    not a conformance violation, so it must NOT fail the suite: the scenario's
    correctness is already pinned by the pandas branch above. A WRONG answer (row /
    graph assertion mismatch) or any OTHER exception from polars still fails — those
    are real polars-engine bugs. Tolerated declines are collected in
    ``_POLARS_NOT_IMPLEMENTED`` for a coverage report (see the session-summary
    fixture / ``-s`` output)."""
    try:
        polars_result = g.gfql(scenario.cypher, params=scenario.params, engine="polars")
    except NotImplementedError as exc:
        _POLARS_NOT_IMPLEMENTED.append(f"{scenario.key}: {str(exc)[:80]}")
        return
    if scenario.expected.rows is not None:
        _assert_expected_rows(scenario, _rows_from_result(polars_result))
    else:
        _assert_expected_graph_result(scenario, polars_result)


def _rows_from_result(result: Any) -> List[Dict[str, Any]]:
    if result._nodes is None:
        return []
    result = _collapse_structured_returns(result)
    pdf = _to_pandas(result._nodes)
    if pdf is None:
        return []
    return pdf.to_dict("records")


def _ids_from_entity_projection_meta(
    result: object,
    *,
    table: str,
    alias_hint: str | None = None,
) -> set:
    meta = getattr(result, "_cypher_entity_projection_meta", None)
    if not isinstance(meta, dict):
        return set()

    candidates: List[object] = []
    if alias_hint is not None:
        candidate = meta.get(alias_hint)
        if candidate is not None:
            candidates = [candidate]
    else:
        candidates = [
            candidate
            for candidate in meta.values()
            if isinstance(candidate, dict) and candidate.get("table") == table
        ]

    if len(candidates) != 1:
        return set()

    candidate = candidates[0]
    if not isinstance(candidate, dict) or candidate.get("table") != table:
        return set()

    ids = candidate.get("ids")
    if ids is None:
        return set()

    values = ids.tolist() if hasattr(ids, "tolist") else list(ids)
    normalized = set()
    for value in values:
        if hasattr(value, "item") and not isinstance(value, (str, bytes, list, tuple, dict)):
            try:
                value = value.item()
            except Exception:
                pass
        if value is not None:
            normalized.add(value)
    return normalized


def _ids_from_flat_entity_columns(result: object, id_attr: str, alias_hint: str | None) -> set:
    """Node/edge ids from #1650 flat ``{alias}.{internal_id}`` columns.

    The native polars engine does not populate ``_cypher_entity_projection_meta``
    (only pandas does), but a whole-entity ``RETURN n`` still flattens the internal
    id column to ``{alias}.{result._node}`` (which holds the original ids). Recover
    the returned-node ids from there — the graph-result analogue of the display-text
    reconstruction in :func:`_collapse_structured_returns`."""
    df = getattr(result, "_nodes" if id_attr == "_node" else "_edges", None)
    if df is None:
        return set()
    id_col = getattr(result, id_attr, None)
    if id_col is None:
        return set()
    pdf = _to_pandas(df)
    if pdf is None:
        return set()
    suffix = f".{id_col}"
    cols = [str(c) for c in pdf.columns if str(c).endswith(suffix)]
    if alias_hint is not None:
        cols = [c for c in cols if c == f"{alias_hint}{suffix}"]
    ids: set = set()
    for c in cols:
        ids.update(v for v in pdf[c].tolist() if v is not None)
    return ids


def _assert_expected_graph_result(scenario: Scenario, result: object) -> None:
    actual_nodes = _ids_from_df(getattr(result, "_nodes", None), scenario.graph.node_id)
    actual_edges = _ids_from_df(getattr(result, "_edges", None), scenario.graph.edge_id)
    if scenario.expected.node_ids is not None and not actual_nodes:
        actual_nodes = _ids_from_entity_projection_meta(
            result,
            table="nodes",
            alias_hint=scenario.return_alias,
        ) or _ids_from_flat_entity_columns(result, "_node", scenario.return_alias)
    if scenario.expected.edge_ids is not None and not actual_edges:
        actual_edges = _ids_from_entity_projection_meta(
            result,
            table="edges",
            alias_hint=scenario.return_alias,
        ) or _ids_from_flat_entity_columns(result, "_edge", scenario.return_alias)

    if scenario.expected.node_ids is not None:
        assert set(scenario.expected.node_ids) == actual_nodes, (
            f"node id mismatch for {scenario.key}: "
            f"expected={sorted(set(scenario.expected.node_ids))}, "
            f"actual={sorted(actual_nodes)}"
        )
    if scenario.expected.edge_ids is not None:
        assert set(scenario.expected.edge_ids) == actual_edges, (
            f"edge id mismatch for {scenario.key}: "
            f"expected={sorted(set(scenario.expected.edge_ids))}, "
            f"actual={sorted(actual_edges)}"
        )
    assert scenario.expected.node_ids is not None or scenario.expected.edge_ids is not None, (
        f"direct Cypher scenario {scenario.key} has no row or graph oracle"
    )


@pytest.mark.parametrize(
    "key",
    [
        "expr-comparison3-9",
        "expr-precedence1-20-1",
        "expr-precedence1-20-2",
        "expr-precedence1-24-2",
        "expr-precedence1-25-6",
        "expr-precedence1-27",
        "expr-quantifier1-10-1",
        "expr-quantifier1-10-2",
        "expr-quantifier1-10-3",
        "expr-quantifier1-10-7",
        "expr-quantifier1-7-2",
        "expr-quantifier1-7-4",
        "expr-quantifier1-7-5",
        "expr-quantifier1-7-6",
        "expr-quantifier1-7-7",
        "expr-quantifier1-7-8",
        "expr-quantifier2-10-1",
        "expr-quantifier2-10-2",
        "expr-quantifier2-10-3",
        "expr-quantifier2-10-4",
        "expr-quantifier2-10-5",
        "expr-quantifier2-10-7",
        "expr-quantifier2-7-2",
        "expr-quantifier2-7-4",
        "expr-quantifier2-7-5",
        "expr-quantifier2-7-7",
        "expr-quantifier3-10-1",
        "expr-quantifier3-10-2",
        "expr-quantifier3-10-3",
        "expr-quantifier3-10-7",
        "expr-quantifier3-7-2",
        "expr-quantifier3-7-4",
        "expr-quantifier3-7-5",
        "expr-quantifier3-7-6",
        "expr-quantifier3-7-7",
        "expr-quantifier3-7-8",
        "expr-quantifier4-10-1",
        "expr-quantifier4-10-2",
        "expr-quantifier4-10-4",
        "expr-quantifier4-10-5",
        "expr-quantifier4-10-8",
        "expr-quantifier4-7-2",
        "expr-quantifier4-7-8",
    ],
)
def test_direct_cypher_only_support_regressions(key: str) -> None:
    scenario = next(s for s in SCENARIOS if s.key == key)
    assert scenario.status == "supported"
    assert "cypher-string" in scenario.tags
    assert "phase1-executor" not in scenario.tags


def test_direct_cypher_only_error_support_regression() -> None:
    scenario = next(s for s in SCENARIOS if s.key == "expr-quantifier1-15-2")
    assert scenario.status == "supported"
    assert "cypher-string" in scenario.tags
    assert "cypher-string-error" in scenario.tags
    assert "phase1-executor" not in scenario.tags


def test_direct_cypher_only_error_support_regression_quantifier2() -> None:
    scenario = next(s for s in SCENARIOS if s.key == "expr-quantifier2-16-2")
    assert scenario.status == "supported"
    assert "cypher-string" in scenario.tags
    assert "cypher-string-error" in scenario.tags
    assert "phase1-executor" not in scenario.tags


def test_direct_cypher_only_error_support_regression_quantifier3() -> None:
    scenario = next(s for s in SCENARIOS if s.key == "expr-quantifier3-15-2")
    assert scenario.status == "supported"
    assert "cypher-string" in scenario.tags
    assert "cypher-string-error" in scenario.tags
    assert "phase1-executor" not in scenario.tags


def test_direct_cypher_only_error_support_regression_quantifier4() -> None:
    scenario = next(s for s in SCENARIOS if s.key == "expr-quantifier4-15-2")
    assert scenario.status == "supported"
    assert "cypher-string" in scenario.tags
    assert "cypher-string-error" in scenario.tags
    assert "phase1-executor" not in scenario.tags


def test_direct_cypher_only_error_support_regression_typeconversion2() -> None:
    scenario = next(s for s in SCENARIOS if s.key == "expr-typeconversion2-8-3")
    assert scenario.status == "supported"
    assert "cypher-string" in scenario.tags
    assert "cypher-string-error" in scenario.tags
    assert "phase1-executor" not in scenario.tags


@pytest.mark.parametrize("key", ["expr-typeconversion3-6-1", "expr-typeconversion3-6-4"])
def test_direct_cypher_only_error_support_regression_typeconversion3(key: str) -> None:
    scenario = next(s for s in SCENARIOS if s.key == key)
    assert scenario.status == "supported"
    assert "cypher-string" in scenario.tags
    assert "cypher-string-error" in scenario.tags
    assert "phase1-executor" not in scenario.tags


_RANGE_INVALID_ARG_ERROR_KEYS = tuple(
    f"expr-list11-4-{i}" for i in range(1, 5)
) + tuple(f"expr-list11-5-{i}" for i in range(1, 23))


_PARAM_BINDING_CLUSTER3_KEYS = (
    "delete5-1",
    "delete5-2",
    "expr-aggregation6-1-1",
    "expr-aggregation6-1-2",
    "expr-aggregation6-1-3",
    "expr-aggregation6-2-1",
    "expr-aggregation6-2-2",
    "expr-aggregation6-2-3",
    "expr-aggregation6-3-1",
    "expr-aggregation6-3-2",
    "expr-aggregation6-3-3",
    "expr-aggregation6-4-1",
    "expr-aggregation6-4-2",
    "expr-aggregation6-4-3",
    "expr-graph7-3",
    "expr-list1-3",
    "expr-list1-4",
    "expr-list1-5",
    "expr-list2-10",
    "expr-list2-11",
    "expr-map2-1",
    "expr-map2-2",
    "expr-map3-2",
    "expr-null3-4-1",
    "expr-null3-4-2",
    "expr-null3-4-3",
    "expr-null3-4-4",
    "expr-null3-4-5",
    "expr-null3-4-6",
    "expr-null3-4-7",
    "expr-typeconversion2-6",
)

_PARAM_BINDING_PROMOTED_ROW_KEYS = (
    "expr-list1-3",
    "expr-list1-4",
    "expr-list1-5",
    "expr-list2-10",
    "expr-list2-11",
    "expr-map3-2",
    "expr-null3-4-1",
    "expr-null3-4-2",
    "expr-null3-4-3",
    "expr-null3-4-5",
    "expr-null3-4-6",
    "expr-null3-4-7",
    "expr-typeconversion2-6",
)

_ISSUE142_PROMOTED_ROW_KEYS = (
    "match7-24",
    "return-orderby2-6",
    "expr-comparison2-5-1",
    "expr-comparison2-5-2",
    "expr-comparison2-5-3",
    "expr-comparison2-5-4",
    "expr-comparison2-6-1",
    "expr-comparison2-6-2",
    "expr-graph3-5",
    "expr-quantifier7-3-1",
    "expr-quantifier7-3-2",
    "expr-quantifier7-3-3",
    "expr-quantifier7-3-4",
    "expr-quantifier7-3-5",
    "usecase-countingsubgraphmatches1-5",
    "usecase-countingsubgraphmatches1-6",
    "usecase-countingsubgraphmatches1-7",
    "usecase-countingsubgraphmatches1-9",
)

_ISSUE142_PROMOTED_ERROR_KEYS = (
    "expr-list1-6-4",
    "expr-typeconversion4-10-1",
    "expr-typeconversion4-10-2",
)


@pytest.mark.parametrize("key", _PARAM_BINDING_CLUSTER3_KEYS)
def test_issue120_parameter_binding_cluster_has_explicit_params(key: str) -> None:
    scenario = next(s for s in SCENARIOS if s.key == key)
    assert scenario.params is not None


@pytest.mark.parametrize("key", _PARAM_BINDING_PROMOTED_ROW_KEYS)
def test_issue120_parameter_binding_row_promotions_execute_direct_cypher(key: str) -> None:
    scenario = next(s for s in SCENARIOS if s.key == key)
    assert scenario.status == "supported"
    assert "cypher-string" in scenario.tags
    assert key in DIRECT_CYPHER_PROMOTION_KEYS

    result = _build_graph(scenario.graph).gfql(
        scenario.cypher, params=scenario.params, engine="pandas"
    )
    assert scenario.expected.rows is not None
    _assert_expected_rows(scenario, _rows_from_result(result))


@pytest.mark.parametrize("key", _RANGE_INVALID_ARG_ERROR_KEYS)
def test_range_invalid_argument_scenarios_promoted_as_direct_cypher_errors(key: str) -> None:
    """Positive: range() invalid-argument scenarios are supported error cases."""
    scenario = next(s for s in SCENARIOS if s.key == key)
    assert scenario.status == "supported"
    assert "cypher-string" in scenario.tags
    assert "cypher-string-error" in scenario.tags
    assert "phase1-executor" not in scenario.tags
    # These are error scenarios — no row/graph oracle.
    assert scenario.expected.rows is None
    assert scenario.expected.node_ids is None
    assert scenario.expected.edge_ids is None
    # Direct Cypher must actually raise for the promotion to be valid.
    with pytest.raises(Exception):
        _build_graph(scenario.graph).gfql(
            scenario.cypher, params=scenario.params, engine="pandas"
        )


def test_range_invalid_argument_promotion_covers_exactly_the_audited_keys() -> None:
    """Negative guard: promotion set matches the audited range() invalid-arg keys.

    Catches drift if a range() scenario is added/removed or mis-bucketed.
    """
    promoted_list11 = {
        key
        for key in DIRECT_CYPHER_PROMOTION_ERROR_KEYS
        if key.startswith("expr-list11-4-") or key.startswith("expr-list11-5-")
    }
    assert promoted_list11 == set(_RANGE_INVALID_ARG_ERROR_KEYS)


@pytest.mark.parametrize("key", _ISSUE142_PROMOTED_ROW_KEYS)
def test_issue142_refreshed_xfail_row_promotions_execute_direct_cypher(
    key: str,
) -> None:
    scenario = next(s for s in SCENARIOS if s.key == key)
    assert scenario.status == "supported"
    assert "cypher-string" in scenario.tags
    assert "cypher-string-error" not in scenario.tags
    assert key in DIRECT_CYPHER_PROMOTION_KEYS

    result = _build_graph(scenario.graph).gfql(
        scenario.cypher, params=scenario.params, engine="pandas"
    )
    assert scenario.expected.rows is not None
    _assert_expected_rows(scenario, _rows_from_result(result))


@pytest.mark.parametrize("key", _ISSUE142_PROMOTED_ERROR_KEYS)
def test_issue142_refreshed_xfail_error_promotions_raise_direct_cypher(
    key: str,
) -> None:
    scenario = next(s for s in SCENARIOS if s.key == key)
    assert scenario.status == "supported"
    assert "cypher-string" in scenario.tags
    assert "cypher-string-error" in scenario.tags
    assert key in DIRECT_CYPHER_PROMOTION_ERROR_KEYS
    assert scenario.expected.rows is None

    with pytest.raises(Exception):
        _build_graph(scenario.graph).gfql(
            scenario.cypher, params=scenario.params, engine="pandas"
        )


def test_valid_range_scenario_is_not_promoted_as_an_error() -> None:
    """Negative: a valid range() call stays a non-error supported scenario."""
    scenario = next(s for s in SCENARIOS if s.key == "unwind1-2")
    assert scenario.status == "supported"
    assert "cypher-string-error" not in scenario.tags
    # A valid range() executes and yields rows without raising.
    result = _build_graph(scenario.graph).gfql(
        scenario.cypher, params=scenario.params, engine="pandas"
    )
    assert _rows_from_result(result)


def test_quantifier11_placeholder_case_is_not_phase_promoted() -> None:
    scenario = next(s for s in SCENARIOS if s.key == "expr-quantifier11-3-4")
    assert scenario.status == "xfail"
    assert "phase1-executor" not in scenario.tags


@pytest.mark.parametrize(
    "key",
    [
        "usecase-countingsubgraphmatches1-1",
        "usecase-countingsubgraphmatches1-2",
        "usecase-countingsubgraphmatches1-3",
        "usecase-countingsubgraphmatches1-4",
    ],
)
def test_counting_subgraph_match_count_star_cases_are_not_direct_promoted(key: str) -> None:
    scenario = next(s for s in SCENARIOS if s.key == key)
    assert scenario.status == "xfail"
    assert "cypher-string" not in scenario.tags


def test_match7_9_is_direct_only_promoted_not_phase_promoted() -> None:
    scenario = next(s for s in SCENARIOS if s.key == "match7-9")
    assert scenario.status == "supported"
    assert "cypher-string" in scenario.tags
    assert "phase1-executor" not in scenario.tags


def test_match_where1_10_direct_cypher_graph_id_promotion() -> None:
    scenario = next(s for s in SCENARIOS if s.key == "match-where1-10")
    assert scenario.status == "supported"
    assert "cypher-string" in scenario.tags
    assert "cypher-string-error" not in scenario.tags
    assert scenario.expected.node_ids == ["a", "b"]

    result = _build_graph(scenario.graph).gfql(
        scenario.cypher,
        params=scenario.params,
        engine="pandas",
    )
    _assert_expected_graph_result(scenario, result)


def _direct_cypher_xfail_outcome(scenario: Scenario) -> str:
    g = _build_graph(scenario.graph)
    try:
        result = g.gfql(scenario.cypher, params=scenario.params, engine="pandas")
    except GFQLValidationError:
        return DIRECT_CYPHER_XFAIL_VALIDATION_OUTCOME
    except Exception as exc:
        return type(exc).__name__

    if scenario.expected.rows is None:
        return "unexpected_success_expected_error"

    try:
        _assert_expected_rows(scenario, _rows_from_result(result))
    except AssertionError:
        return "success_wrong_rows"
    return "success_matches_expected"


def test_direct_cypher_xfail_contract_map_only_targets_current_xfails() -> None:
    xfail_keys = {scenario.key for scenario in SCENARIOS if scenario.status == "xfail"}
    assert set(DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY).issubset(xfail_keys)


def test_direct_cypher_matches_expected_contract_keys_are_stable() -> None:
    assert set(DIRECT_CYPHER_XFAIL_MATCHES_EXPECTED_KEYS) == set(
        DIRECT_CYPHER_XFAIL_MATCHES_EXPECTED_BASE_KEYS
    )


def test_direct_cypher_promoted_from_xfail_matches_expected_keys_are_supported() -> None:
    scenarios_by_key = {scenario.key: scenario for scenario in SCENARIOS}
    for key in DIRECT_CYPHER_PROMOTED_FROM_XFAIL_MATCHES_EXPECTED_KEYS:
        scenario = scenarios_by_key[key]
        assert scenario.status == "supported"
        assert "cypher-string" in scenario.tags


def test_direct_cypher_promoted_from_xfail_matches_expected_keys_not_tracked_as_nonvalidation_debt() -> None:
    assert set(DIRECT_CYPHER_PROMOTED_FROM_XFAIL_MATCHES_EXPECTED_KEYS).isdisjoint(
        DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY
    )


def test_direct_cypher_promotion_snapshot_matches_status_tags() -> None:
    represented_keys = {scenario.key for scenario in SCENARIOS}
    translated_supported_keys = {
        scenario.key
        for scenario in SCENARIOS
        if scenario.status == "supported"
        and scenario.gfql is not None
        and "cypher-string" not in scenario.tags
    }
    promotion_snapshot_keys = (
        DIRECT_CYPHER_PROMOTION_KEYS & represented_keys
    ) - translated_supported_keys
    status_promoted_keys = {
        scenario.key
        for scenario in SCENARIOS
        if scenario.status == "supported"
        and "cypher-string" in scenario.tags
        and "first-party" not in scenario.tags
    }
    first_party_cypher_string_keys = {
        scenario.key
        for scenario in SCENARIOS
        if scenario.status == "supported"
        and "cypher-string" in scenario.tags
        and "first-party" in scenario.tags
    }
    assert promotion_snapshot_keys == status_promoted_keys
    assert first_party_cypher_string_keys
    assert promotion_snapshot_keys.isdisjoint(first_party_cypher_string_keys)


@pytest.mark.parametrize(
    "scenario",
    tuple(scenario for scenario in SCENARIOS if scenario.status == "xfail"),
    ids=lambda scenario: scenario.key,
)
def test_direct_cypher_xfail_contract(scenario: Scenario) -> None:
    assert (
        _direct_cypher_xfail_outcome(scenario)
        == expected_direct_cypher_xfail_outcome(scenario.key)
    )


def _assert_ids(
    expected: Expected,
    oracle_nodes: set,
    oracle_edges: set,
    actual_nodes: set,
    actual_edges: set,
) -> None:
    if expected.node_ids is not None:
        assert set(expected.node_ids) == oracle_nodes
        assert set(expected.node_ids) == actual_nodes
    else:
        assert oracle_nodes == actual_nodes

    if expected.edge_ids is not None:
        assert set(expected.edge_ids) == oracle_edges
        assert set(expected.edge_ids) == actual_edges
    else:
        assert oracle_edges == actual_edges


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.key)
def test_cypher_tck_scenario(scenario: Scenario) -> None:
    if scenario.status == "skip":
        pytest.skip(scenario.reason or "skipped")
    if scenario.status == "xfail":
        pytest.xfail(scenario.reason or "expected failure")

    g = _build_graph(scenario.graph)

    if is_typed_schema_scenario(scenario):
        g = bind_schema_for_scenario(g, scenario)
        if _is_cypher_string_error(scenario):
            _assert_expected_error(
                scenario,
                lambda: validate_typed_schema_scenario(g, scenario),
                expected="typed schema validation exception",
            )
            return
        validate_typed_schema_scenario(g, scenario)
        pandas_result = g.gfql(scenario.cypher, params=scenario.params, engine="pandas")
        if scenario.expected.rows is not None:
            _assert_expected_rows(scenario, _rows_from_result(pandas_result))
        else:
            _assert_expected_graph_result(scenario, pandas_result)
        if _TEST_CUDF and _HAS_CUDF:
            cudf_result = g.gfql(scenario.cypher, params=scenario.params, engine="cudf")
            if scenario.expected.rows is not None:
                _assert_expected_rows(scenario, _rows_from_result(cudf_result))
            else:
                _assert_expected_graph_result(scenario, cudf_result)
        if _TEST_POLARS and _HAS_POLARS:
            _assert_polars_engine(g, scenario)
        return

    if _is_cypher_string_supported(scenario):
        if _is_cypher_string_error(scenario):
            _assert_expected_error(
                scenario,
                lambda: g.gfql(
                    scenario.cypher,
                    params=scenario.params,
                    engine="pandas",
                ),
                expected="direct Cypher exception",
            )
            if _TEST_CUDF and _HAS_CUDF:
                _assert_expected_error(
                    scenario,
                    lambda: g.gfql(
                        scenario.cypher,
                        params=scenario.params,
                        engine="cudf",
                    ),
                    expected="direct Cypher exception",
                )
            if _TEST_POLARS and _HAS_POLARS:
                _assert_expected_error(
                    scenario,
                    lambda: g.gfql(
                        scenario.cypher,
                        params=scenario.params,
                        engine="polars",
                    ),
                    expected="direct Cypher exception",
                )
        else:
            pandas_result = g.gfql(scenario.cypher, params=scenario.params, engine="pandas")
            if scenario.expected.rows is not None:
                _assert_expected_rows(scenario, _rows_from_result(pandas_result))
            else:
                _assert_expected_graph_result(scenario, pandas_result)
            if _TEST_CUDF and _HAS_CUDF:
                cudf_result = g.gfql(scenario.cypher, params=scenario.params, engine="cudf")
                if scenario.expected.rows is not None:
                    _assert_expected_rows(scenario, _rows_from_result(cudf_result))
                else:
                    _assert_expected_graph_result(scenario, cudf_result)
            if _TEST_POLARS and _HAS_POLARS:
                _assert_polars_engine(g, scenario)
        return

    assert scenario.gfql is not None


    is_plan = (
        isinstance(scenario.gfql, Sequence)
        and len(scenario.gfql) > 0
        and all(isinstance(step, PlanStep) for step in scenario.gfql)
    )

    if is_plan:
        expects_error = scenario.expected.rows is None and "phase1-executor-error" in scenario.tags
        if expects_error:
            _assert_expected_error(
                scenario,
                lambda: execute_plan(
                    g,
                    scenario.graph,
                    scenario.gfql,
                    params=scenario.params,
                    strict_pure=_STRICT_PURE,
                ),
                expected="phase1 executor exception",
            )
        else:
            plan_rows_df = execute_plan(
                g,
                scenario.graph,
                scenario.gfql,
                params=scenario.params,
                strict_pure=_STRICT_PURE,
            )
            _assert_expected_rows(scenario, plan_rows_df.to_dict("records"))
        return

    oracle = enumerate_chain(g, scenario.gfql, caps=OracleCaps(max_nodes=100, max_edges=100))

    oracle_nodes = _ids_from_df(oracle.nodes, g._node)
    oracle_edges = _ids_from_df(oracle.edges, g._edge)

    pandas_result = g.gfql(scenario.gfql, engine="pandas")
    pandas_nodes = _ids_from_df(pandas_result._nodes, g._node)
    pandas_edges = _ids_from_df(pandas_result._edges, g._edge)

    if scenario.return_alias:
        oracle_nodes = set(oracle.tags.get(scenario.return_alias, set()))
        pandas_nodes = _alias_nodes(pandas_result._nodes, g._node, scenario.return_alias)

    _assert_ids(scenario.expected, oracle_nodes, oracle_edges, pandas_nodes, pandas_edges)

    if _TEST_CUDF and _HAS_CUDF:
        cudf_result = g.gfql(scenario.gfql, engine="cudf")
        cudf_nodes = _ids_from_df(cudf_result._nodes, g._node)
        cudf_edges = _ids_from_df(cudf_result._edges, g._edge)
        if scenario.return_alias:
            cudf_nodes = _alias_nodes(cudf_result._nodes, g._node, scenario.return_alias)
        _assert_ids(scenario.expected, oracle_nodes, oracle_edges, cudf_nodes, cudf_edges)

    if _TEST_POLARS and _HAS_POLARS:
        try:
            polars_result = g.gfql(scenario.gfql, engine="polars")
        except NotImplementedError as exc:
            # Honest NO-CHEATING decline on the gfql-AST path — tolerate (see
            # _assert_polars_engine). pandas already pinned correctness above.
            _POLARS_NOT_IMPLEMENTED.append(f"{scenario.key}: {str(exc)[:80]}")
        else:
            polars_nodes = _ids_from_df(polars_result._nodes, g._node)
            polars_edges = _ids_from_df(polars_result._edges, g._edge)
            if scenario.return_alias:
                polars_nodes = _alias_nodes(polars_result._nodes, g._node, scenario.return_alias)
            _assert_ids(scenario.expected, oracle_nodes, oracle_edges, polars_nodes, polars_edges)
