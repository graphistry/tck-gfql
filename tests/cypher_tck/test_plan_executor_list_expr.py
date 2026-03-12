from __future__ import annotations

import pandas as pd

from tests.cypher_tck.gfql_plan import func, list_, lit
from tests.cypher_tck.plan_executor import _expr_to_gfql_value
from tests.cypher_tck.scenarios import SCENARIOS


def _scenario(key: str):
    for scenario in SCENARIOS:
        if scenario.key == key:
            return scenario
    raise AssertionError(f"scenario not found: {key}")


def test_expr_to_gfql_value_lowers_list_order_expression() -> None:
    scenario = _scenario("with-orderby2-9-1")
    order_step = next(step for step in scenario.gfql if step.op == "order_by")
    order_expr = order_step.args["keys"][0][0]

    frame = pd.DataFrame(
        {
            "a": [True],
            "list": [[1, 2]],
            "list2": [[3, 4]],
        }
    )
    lowered = _expr_to_gfql_value(order_expr, frame)
    assert isinstance(lowered, str)
    assert lowered == "[list2[1], list2[0], list[1]] + list + list2"


def test_expr_to_gfql_value_lowers_size_over_expr_list() -> None:
    expr = func("size", [list_([lit(1), lit(2), lit(3)])])
    lowered = _expr_to_gfql_value(expr, pd.DataFrame(index=[0]))
    assert lowered == "size([1, 2, 3])"
