from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Sequence, Tuple

from tests.cypher_tck.gfql_plan import PlanStep
from tests.cypher_tck.plan_executor import PlanPurityError, execute_plan
from tests.cypher_tck.scenarios import SCENARIOS
from tests.cypher_tck.test_tck_runner import _assert_expected_rows, _build_graph

_SUPPORT_FILE = Path(__file__).resolve().parent / "phase_support.py"


def _is_executable_plan(gfql: object) -> bool:
    if not isinstance(gfql, tuple) or not gfql:
        return False
    if not all(isinstance(step, PlanStep) for step in gfql):
        return False
    return not any(step.op in {"raw", "invalid"} for step in gfql)


def _is_error_plan(gfql: object) -> bool:
    if not isinstance(gfql, tuple) or not gfql:
        return False
    if not all(isinstance(step, PlanStep) for step in gfql):
        return False
    return not any(step.op == "raw" for step in gfql)


def _expects_error_scenario(scenario: object) -> bool:
    status = getattr(scenario, "status", None)
    if status != "xfail":
        return False
    expected = getattr(scenario, "expected", None)
    if expected is None or getattr(expected, "rows", None) is not None:
        return False
    tags = set(getattr(scenario, "tags", ()))
    if "syntax-error" in tags or "runtime-error" in tags:
        return True
    reason = str(getattr(scenario, "reason", "") or "").lower()
    return any(
        marker in reason
        for marker in (
            "compile-time validation",
            "runtime validation",
            "runtime error",
            "deleted-entity runtime errors",
        )
    )


def _compute_pass_sweep(strict_pure: bool = False) -> Tuple[List[str], List[str], List[Tuple[str, str]]]:
    keys: List[str] = []
    error_keys: List[str] = []
    failures: List[Tuple[str, str]] = []

    for scenario in SCENARIOS:
        if scenario.gfql is None:
            continue
        graph = _build_graph(scenario.graph)
        impurity_reasons: List[str] = []

        if scenario.expected.rows is not None:
            if not _is_executable_plan(scenario.gfql):
                continue
            try:
                rows_df = execute_plan(
                    graph,
                    scenario.graph,
                    scenario.gfql,
                    params=scenario.params,
                    strict_pure=strict_pure,
                    impurity_reasons=impurity_reasons,
                )
                _assert_expected_rows(scenario, rows_df.to_dict("records"))
                if strict_pure and impurity_reasons:
                    raise AssertionError(
                        "strict pure execution unexpectedly carried impurity markers: "
                        + ", ".join(impurity_reasons)
                    )
                keys.append(scenario.key)
            except Exception as exc:  # noqa: BLE001 - summarize sweep blockers
                failures.append((scenario.key, str(exc)))
            continue

        if not _expects_error_scenario(scenario) or not _is_error_plan(scenario.gfql):
            continue

        try:
            _ = execute_plan(
                graph,
                scenario.graph,
                scenario.gfql,
                params=scenario.params,
                strict_pure=strict_pure,
                impurity_reasons=impurity_reasons,
            )
            failures.append((scenario.key, "expected error but plan executed successfully"))
        except PlanPurityError as exc:
            failures.append((scenario.key, f"unexpected strict-pure impurity before expected error: {exc}"))
        except Exception:
            error_keys.append(scenario.key)

    keys.sort()
    error_keys.sort()
    return keys, error_keys, failures


def _render_phase_support(
    semantic_keys: Sequence[str],
    pure_keys: Sequence[str],
    semantic_error_keys: Sequence[str],
    pure_error_keys: Sequence[str],
) -> str:
    supported_all = sorted(set(semantic_keys).union(semantic_error_keys))
    pure_all = sorted(set(pure_keys).union(pure_error_keys))
    lines = [
        '"""Generated support-key snapshots for deterministic scenario promotion."""',
        "",
        "from __future__ import annotations",
        "",
        "PHASE1_EXECUTOR_SUPPORTED_KEYS = {",
    ]
    lines.extend([f'    "{key}",' for key in supported_all])
    lines.append("}")
    lines.append("")
    lines.append("PHASE1_EXECUTOR_PURE_KEYS = {")
    lines.extend([f'    "{key}",' for key in pure_all])
    lines.append("}")
    lines.append("")
    lines.append("PHASE1_EXECUTOR_SUPPORTED_ERROR_KEYS = {")
    lines.extend([f'    "{key}",' for key in semantic_error_keys])
    lines.append("}")
    lines.append("")
    lines.append("PHASE1_EXECUTOR_PURE_ERROR_KEYS = {")
    lines.extend([f'    "{key}",' for key in pure_error_keys])
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sweep executable plan scenarios and refresh promotion keys.")
    parser.add_argument("--write", action="store_true", help="Write refreshed keys to phase_support.py")
    parser.add_argument("--show-failures", type=int, default=0, help="Show first N failing scenario reasons")
    args = parser.parse_args()

    semantic_keys, semantic_error_keys, semantic_failures = _compute_pass_sweep(strict_pure=False)
    pure_keys, pure_error_keys, pure_failures = _compute_pass_sweep(strict_pure=True)
    print(f"pass-sweep semantic keys: {len(semantic_keys)}")
    print(f"pass-sweep semantic error keys: {len(semantic_error_keys)}")
    print(f"pass-sweep semantic failures: {len(semantic_failures)}")
    print(f"pass-sweep pure keys: {len(pure_keys)}")
    print(f"pass-sweep pure error keys: {len(pure_error_keys)}")
    print(f"pass-sweep pure failures: {len(pure_failures)}")

    if args.show_failures > 0:
        print("semantic failures:")
        for key, reason in semantic_failures[: args.show_failures]:
            print(f"- {key}: {reason}")
        print("pure failures:")
        for key, reason in pure_failures[: args.show_failures]:
            print(f"- {key}: {reason}")

    if args.write:
        _SUPPORT_FILE.write_text(
            _render_phase_support(semantic_keys, pure_keys, semantic_error_keys, pure_error_keys),
            encoding="utf-8",
        )
        print(f"wrote: {_SUPPORT_FILE}")


if __name__ == "__main__":
    main()
