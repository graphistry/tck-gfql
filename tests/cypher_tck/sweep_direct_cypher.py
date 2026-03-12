
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Sequence, Tuple

from graphistry.gfql.ref.enumerator import OracleCaps, enumerate_chain

from tests.cypher_tck.models import Scenario
from tests.cypher_tck.scenarios import SCENARIOS
from tests.cypher_tck.sweep_promotions import _expects_error_scenario
from tests.cypher_tck.test_tck_runner import (
    _assert_expected_rows,
    _build_graph,
    _ids_from_df,
    _rows_from_result,
)

_SUPPORT_FILE = Path(__file__).resolve().parent / "direct_cypher_support.py"


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
        candidates = [candidate for candidate in meta.values() if isinstance(candidate, dict) and candidate.get("table") == table]

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


def _compare_graph_result(scenario: Scenario, result: object) -> None:
    actual_nodes = _ids_from_df(getattr(result, "_nodes", None), scenario.graph.node_id)
    actual_edges = _ids_from_df(getattr(result, "_edges", None), scenario.graph.edge_id)
    if scenario.expected.node_ids is not None and not actual_nodes:
        actual_nodes = _ids_from_entity_projection_meta(result, table="nodes", alias_hint=scenario.return_alias)
    if scenario.expected.edge_ids is not None and not actual_edges:
        actual_edges = _ids_from_entity_projection_meta(result, table="edges", alias_hint=scenario.return_alias)

    if scenario.expected.node_ids is not None:
        assert set(scenario.expected.node_ids) == actual_nodes, (
            f"node id mismatch for {scenario.key}: expected={sorted(set(scenario.expected.node_ids))}, "
            f"actual={sorted(actual_nodes)}"
        )
    if scenario.expected.edge_ids is not None:
        assert set(scenario.expected.edge_ids) == actual_edges, (
            f"edge id mismatch for {scenario.key}: expected={sorted(set(scenario.expected.edge_ids))}, "
            f"actual={sorted(actual_edges)}"
        )

    if scenario.expected.node_ids is not None or scenario.expected.edge_ids is not None:
        return

    if scenario.gfql is None:
        raise AssertionError(
            f"graph comparison for {scenario.key} requires translated GFQL oracle or explicit expected ids"
        )

    oracle = enumerate_chain(_build_graph(scenario.graph), scenario.gfql, caps=OracleCaps(max_nodes=100, max_edges=100))
    oracle_nodes = _ids_from_df(oracle._nodes, scenario.graph.node_id)
    oracle_edges = _ids_from_df(oracle._edges, scenario.graph.edge_id)
    assert oracle_nodes == actual_nodes, (
        f"node id mismatch vs translated oracle for {scenario.key}: "
        f"oracle={sorted(oracle_nodes)}, actual={sorted(actual_nodes)}"
    )
    assert oracle_edges == actual_edges, (
        f"edge id mismatch vs translated oracle for {scenario.key}: "
        f"oracle={sorted(oracle_edges)}, actual={sorted(actual_edges)}"
    )


def _run_direct_cypher_scenario(scenario: Scenario) -> Tuple[bool, str]:
    graph = _build_graph(scenario.graph)
    expects_error = _expects_error_scenario(scenario)

    try:
        result = graph.gfql(scenario.cypher, params=scenario.params)
    except Exception as exc:  # noqa: BLE001 - report exact blocker class/message
        if expects_error:
            return True, ""
        return False, f"{type(exc).__name__}: {exc}"

    if expects_error:
        return False, "expected error but direct Cypher executed successfully"

    try:
        if scenario.expected.rows is not None:
            _assert_expected_rows(scenario, _rows_from_result(result))
        else:
            _compare_graph_result(scenario, result)
    except Exception as exc:  # noqa: BLE001 - report exact blocker class/message
        return False, f"{type(exc).__name__}: {exc}"

    return True, ""


def _compute_direct_cypher_sets(
    scenarios: Sequence[Scenario] = SCENARIOS,
) -> Tuple[List[str], List[str], List[str], List[Tuple[str, str]], List[Tuple[str, str]]]:
    overlap_keys: List[str] = []
    promotion_row_keys: List[str] = []
    promotion_error_keys: List[str] = []
    overlap_failures: List[Tuple[str, str]] = []
    promotion_failures: List[Tuple[str, str]] = []

    for scenario in scenarios:
        if scenario.status == "skip":
            continue

        passed, detail = _run_direct_cypher_scenario(scenario)
        is_direct_supported = scenario.status == "supported" and "cypher-string" in scenario.tags
        is_translated_supported = (
            scenario.status == "supported"
            and scenario.gfql is not None
            and not is_direct_supported
        )

        if is_translated_supported:
            if passed:
                overlap_keys.append(scenario.key)
            else:
                overlap_failures.append((scenario.key, detail))
            continue

        if passed:
            if _expects_error_scenario(scenario):
                promotion_error_keys.append(scenario.key)
            else:
                promotion_row_keys.append(scenario.key)
        else:
            promotion_failures.append((scenario.key, detail))

    overlap_keys.sort()
    promotion_row_keys.sort()
    promotion_error_keys.sort()
    return (
        overlap_keys,
        promotion_row_keys,
        promotion_error_keys,
        overlap_failures,
        promotion_failures,
    )


def _render_direct_cypher_support(
    overlap_keys: Sequence[str],
    promotion_row_keys: Sequence[str],
    promotion_error_keys: Sequence[str],
) -> str:
    lines = [
        '"""Generated direct-Cypher support snapshots for deterministic reporting."""',
        "",
        "from __future__ import annotations",
        "",
        "DIRECT_CYPHER_OVERLAP_KEYS = {",
    ]
    lines.extend([f'    "{key}",' for key in overlap_keys])
    lines.append("}")
    lines.append("")
    lines.append("DIRECT_CYPHER_PROMOTION_ROW_KEYS = {")
    lines.extend([f'    "{key}",' for key in promotion_row_keys])
    lines.append("}")
    lines.append("")
    lines.append("DIRECT_CYPHER_PROMOTION_ERROR_KEYS = {")
    lines.extend([f'    "{key}",' for key in promotion_error_keys])
    lines.append("}")
    lines.append("")
    lines.append("DIRECT_CYPHER_PROMOTION_KEYS = DIRECT_CYPHER_PROMOTION_ROW_KEYS | DIRECT_CYPHER_PROMOTION_ERROR_KEYS")
    lines.append("DIRECT_CYPHER_ADDITIONAL_PASS_KEYS = DIRECT_CYPHER_PROMOTION_KEYS")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sweep direct local Cypher support and refresh direct support snapshots.")
    parser.add_argument("--write", action="store_true", help="Write refreshed direct support keys")
    parser.add_argument("--show-failures", type=int, default=0, help="Show first N overlap/additional failures")
    args = parser.parse_args()

    (
        overlap_keys,
        promotion_row_keys,
        promotion_error_keys,
        overlap_failures,
        promotion_failures,
    ) = _compute_direct_cypher_sets()
    supported_total = sum(
        1
        for scenario in SCENARIOS
        if scenario.status == "supported"
        and scenario.gfql is not None
        and "cypher-string" not in scenario.tags
    )
    print(f"direct-Cypher overlap keys: {len(overlap_keys)} / {supported_total}")
    print(f"direct-Cypher promotion row keys: {len(promotion_row_keys)}")
    print(f"direct-Cypher promotion error keys: {len(promotion_error_keys)}")
    print(f"direct-Cypher promotion total: {len(promotion_row_keys) + len(promotion_error_keys)}")
    print(f"direct-Cypher overlap failures: {len(overlap_failures)}")
    print(f"direct-Cypher promotion failures: {len(promotion_failures)}")

    if args.show_failures > 0:
        print("overlap failures:")
        for key, reason in overlap_failures[: args.show_failures]:
            print(f"- {key}: {reason}")
        print("promotion failures:")
        for key, reason in promotion_failures[: args.show_failures]:
            print(f"- {key}: {reason}")

    if args.write:
        _SUPPORT_FILE.write_text(
            _render_direct_cypher_support(overlap_keys, promotion_row_keys, promotion_error_keys),
            encoding="utf-8",
        )
        print(f"wrote: {_SUPPORT_FILE}")


if __name__ == "__main__":
    main()
