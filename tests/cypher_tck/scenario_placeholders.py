from __future__ import annotations

from dataclasses import replace
from typing import Final

from tests.cypher_tck.models import Scenario

_PREDICATES: Final[tuple[str, ...]] = (
    "x = 2",
    "x % 2 = 0",
    "x % 3 = 0",
    "x < 7",
    "x >= 3",
)

_LIST_OPERANDS: Final[tuple[str, ...]] = tuple(
    f"x IN list WHERE {predicate}" for predicate in _PREDICATES
)

_INLINE_LIST_OPERANDS: Final[tuple[str, ...]] = tuple(
    f"x IN [1, 2, 3, 4, 5, 6, 7, 8, 9] WHERE {predicate}"
    for predicate in _PREDICATES
)

_PLACEHOLDER_VALUES_BY_KEY: Final[dict[str, dict[str, str]]] = {
    **{
        f"expr-comparison2-5-{idx}": {"rhs": rhs}
        for idx, rhs in enumerate(("1", "1.0", "0.0 / 0.0", "'a'"), start=1)
    },
    **{
        f"expr-comparison2-6-{idx}": {"rhs": rhs}
        for idx, rhs in enumerate(("1.0", "1.0", "1.0", "1"), start=1)
    },
    **{
        f"expr-quantifier7-3-{idx}": {"operands": operands}
        for idx, operands in enumerate(_INLINE_LIST_OPERANDS, start=1)
    },
    **{
        f"expr-quantifier9-{scenario_num}-{idx}": {"predicate": predicate}
        for scenario_num in (3, 4, 5)
        for idx, predicate in enumerate(_PREDICATES, start=1)
    },
    **{
        f"expr-quantifier10-4-{idx}": {"predicate": predicate}
        for idx, predicate in enumerate(_PREDICATES, start=1)
    },
    **{
        f"expr-quantifier11-3-{idx}": {"operands": operands}
        for idx, operands in enumerate(_LIST_OPERANDS, start=1)
    },
    **{
        f"expr-quantifier11-{scenario_num}-{idx}": {"predicate": predicate}
        for scenario_num in (4, 5, 6)
        for idx, predicate in enumerate(_PREDICATES, start=1)
    },
    **{
        f"expr-quantifier12-{scenario_num}-{idx}": {"predicate": predicate}
        for scenario_num in (3, 4, 5)
        for idx, predicate in enumerate(_PREDICATES, start=1)
    },
}


PLACEHOLDER_SUBSTITUTION_KEYS: Final[frozenset[str]] = frozenset(
    _PLACEHOLDER_VALUES_BY_KEY
)


def apply_outline_placeholder_substitutions(scenario: Scenario) -> Scenario:
    """Patch committed Scenario Outline rows that missed Examples substitution."""

    replacements = _PLACEHOLDER_VALUES_BY_KEY.get(scenario.key)
    if replacements is None:
        return scenario

    cypher = scenario.cypher
    for name, value in replacements.items():
        cypher = cypher.replace(f"<{name}>", value)

    if cypher == scenario.cypher:
        return scenario

    return replace(scenario, cypher=cypher)
