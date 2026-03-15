import os
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd
import pytest

from graphistry.compute.exceptions import GFQLValidationError
from graphistry.embed_utils import check_cudf
from graphistry.gfql.ref.enumerator import OracleCaps, enumerate_chain
from graphistry.tests.test_compute import CGFull

from tests.cypher_tck.direct_cypher_xfail_contract import (
    DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY,
    DIRECT_CYPHER_XFAIL_MATCHES_EXPECTED_BASE_KEYS,
    DIRECT_CYPHER_XFAIL_MATCHES_EXPECTED_KEYS,
    DIRECT_CYPHER_XFAIL_VALIDATION_OUTCOME,
    expected_direct_cypher_xfail_outcome,
)
from tests.cypher_tck.gfql_plan import PlanStep
from tests.cypher_tck.models import Expected, GraphFixture, Scenario
from tests.cypher_tck.plan_executor import execute_plan
from tests.cypher_tck.scenarios import SCENARIOS


_HAS_CUDF, _ = check_cudf()
_TEST_CUDF = os.environ.get("TEST_CUDF", "0") == "1"
_STRICT_PURE = os.environ.get("TCK_STRICT_PURE", "0") == "1"


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


def _normalize_row_value(value: Any) -> Any:
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
        if value.startswith(("(", "[", "{", "<", "'")):
            return value
        if value in {"null", "true", "false"}:
            return value
        return f"'{value}'"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(str(_normalize_row_value(v)) for v in value) + "]"
    if isinstance(value, dict):
        parts = []
        for key in sorted(value.keys()):
            parts.append(f"{key}: {_normalize_row_value(value[key])}")
        return "{" + ", ".join(parts) + "}"
    return value


def _normalize_rows(rows: Sequence[Dict[str, Any]], expected_keys: Sequence[str]) -> List[Dict[str, Any]]:
    normalized = []
    for row in rows:
        missing = [k for k in expected_keys if k not in row]
        assert not missing, f"missing expected row columns: {missing}; row={row}"
        normalized.append({key: _normalize_row_value(row[key]) for key in expected_keys})
    return normalized


def _rows_ordered(gfql: Sequence[Any]) -> bool:
    for step in gfql:
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
    expected_norm = _normalize_rows(expected_rows, expected_keys)
    actual_norm = _normalize_rows(actual_rows, expected_keys)

    if _rows_ordered(scenario.gfql or ()):
        assert actual_norm == expected_norm, (
            f"ordered row mismatch for scenario {scenario.key}; "
            f"expected={expected_norm}, actual={actual_norm}"
        )
        return

    def _row_key(row: Dict[str, Any]) -> str:
        return "|".join(f"{key}={row[key]!r}" for key in expected_keys)

    actual_sorted = sorted(_row_key(row) for row in actual_norm)
    expected_sorted = sorted(_row_key(row) for row in expected_norm)
    assert actual_sorted == expected_sorted, (
        f"unordered row mismatch for scenario {scenario.key}; "
        f"expected={expected_sorted}, actual={actual_sorted}"
    )


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


def _rows_from_result(result: Any) -> List[Dict[str, Any]]:
    if result._nodes is None:
        return []
    pdf = _to_pandas(result._nodes)
    if pdf is None:
        return []
    return pdf.to_dict("records")


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
        "usecase-countingsubgraphmatches1-5",
    ],
)
def test_counting_subgraph_match_count_star_cases_are_not_direct_promoted(key: str) -> None:
    scenario = next(s for s in SCENARIOS if s.key == key)
    assert scenario.status == "xfail"
    assert "cypher-string" not in scenario.tags


def test_match7_9_is_not_direct_promoted() -> None:
    scenario = next(s for s in SCENARIOS if s.key == "match7-9")
    assert scenario.status == "xfail"
    assert "cypher-string" not in scenario.tags


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

    if _is_cypher_string_supported(scenario):
        if _is_cypher_string_error(scenario):
            with pytest.raises(Exception):
                g.gfql(scenario.cypher, params=scenario.params, engine="pandas")
            if _TEST_CUDF and _HAS_CUDF:
                with pytest.raises(Exception):
                    g.gfql(scenario.cypher, params=scenario.params, engine="cudf")
        else:
            pandas_result = g.gfql(scenario.cypher, params=scenario.params, engine="pandas")
            _assert_expected_rows(scenario, _rows_from_result(pandas_result))
            if _TEST_CUDF and _HAS_CUDF:
                cudf_result = g.gfql(scenario.cypher, params=scenario.params, engine="cudf")
                _assert_expected_rows(scenario, _rows_from_result(cudf_result))
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
            with pytest.raises(Exception):
                execute_plan(
                    g,
                    scenario.graph,
                    scenario.gfql,
                    params=scenario.params,
                    strict_pure=_STRICT_PURE,
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
