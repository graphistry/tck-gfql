from __future__ import annotations

import pytest

from tests.cypher_tck.plan_executor import PlanExecutionError, _compile_match_pattern


def _node_aliases(chain: list[object]) -> list[str | None]:
    out: list[str | None] = []
    for part in chain[::2]:
        alias = getattr(part, "name", None)
        if alias is None:
            alias = getattr(part, "_name", None)
        out.append(alias)
    return out


def _edge_directions(chain: list[object]) -> list[str | None]:
    return [getattr(part, "direction", None) for part in chain[1::2]]


def test_compile_match_pattern_allows_three_hop_linear_chain() -> None:
    chain = _compile_match_pattern("(a)-[:R1]->(b)-[:R2]->(c)-[:R3]->(d)")

    assert _node_aliases(chain) == ["a", "b", "c", "d"]
    assert _edge_directions(chain) == ["forward", "forward", "forward"]


def test_compile_match_pattern_stitches_comma_separated_linear_segments() -> None:
    chain = _compile_match_pattern("(a)-[:R1]->(b), (b)-[:R2]->(c)")

    assert _node_aliases(chain) == ["a", "b", "c"]
    assert _edge_directions(chain) == ["forward", "forward"]


def test_compile_match_pattern_stitches_reversed_second_segment() -> None:
    chain = _compile_match_pattern("(a)-[:R1]->(b), (c)<-[:R2]-(b)")

    assert _node_aliases(chain) == ["a", "b", "c"]
    assert _edge_directions(chain) == ["forward", "forward"]


def test_compile_match_pattern_rejects_disconnected_comma_segments() -> None:
    with pytest.raises(PlanExecutionError, match="single linear connected path"):
        _compile_match_pattern("(a)-[:R1]->(b), (c)-[:R2]->(d)")
