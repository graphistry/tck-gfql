from __future__ import annotations

from collections import Counter
from typing import Final, Literal


DirectCypherXfailOutcome = Literal[
    "GFQLValidationError",
    "ValueError",
    "success_matches_expected",
    "success_wrong_rows",
    "unexpected_success_expected_error",
]


DIRECT_CYPHER_XFAIL_VALIDATION_OUTCOME: Final[DirectCypherXfailOutcome] = (
    "GFQLValidationError"
)

# Audit snapshot is pinned to the current sibling CI target: pygraphistry@master.
DIRECT_CYPHER_XFAIL_VALUE_ERROR_KEYS: Final[tuple[str, ...]] = (
    "expr-comparison2-1",
    "match-where5-1",
    "match-where5-2",
    "match-where5-3",
)

DIRECT_CYPHER_XFAIL_WRONG_ROW_KEYS: Final[tuple[str, ...]] = (
    "expr-aggregation3-1",
    "expr-comparison1-6-5",
    "expr-comparison1-7-12",
    "expr-comparison1-7-13",
    "expr-comparison1-7-14",
    "expr-comparison1-7-15",
    "expr-comparison1-7-16",
    "expr-comparison3-5",
    "expr-comparison3-6",
    "expr-comparison3-7",
    "expr-comparison3-8",
    "expr-list12-3",
    "expr-list3-7",
    "expr-list5-21",
    "expr-list5-29",
    "expr-list5-31",
    "expr-list5-34",
    "expr-literals5-11",
    "expr-literals5-12",
    "expr-literals5-25",
    "expr-literals5-26",
    "expr-literals5-5",
    "expr-literals5-6",
    "expr-literals6-4",
    "expr-literals6-5",
    "expr-literals7-18",
    "expr-literals7-7",
    "expr-literals8-11",
    "expr-literals8-18",
    "expr-mathematical8-1",
    "expr-mathematical8-2",
    "expr-null1-3",
    "expr-null2-3",
    "expr-precedence2-1-10",
    "expr-precedence2-1-11",
    "expr-precedence2-1-12",
    "expr-precedence2-1-14",
    "expr-precedence2-1-17",
    "expr-precedence2-1-2",
    "expr-precedence2-1-5",
    "expr-precedence2-1-7",
    "expr-precedence2-1-8",
    "expr-precedence2-1-9",
    "expr-pattern1-10",
    "expr-string10-4",
    "expr-string10-5",
    "expr-string8-4",
    "expr-string8-5",
    "expr-string9-4",
    "expr-string9-5",
    "expr-temporal2-6-5",
    "expr-temporal6-6-2",
    "expr-temporal6-6-8",
    "expr-temporal7-1-1",
    "expr-temporal7-1-2",
    "expr-temporal7-2-1",
    "expr-temporal7-2-2",
    "expr-temporal7-3-1",
    "expr-temporal7-3-2",
    "expr-temporal7-4-1",
    "expr-temporal7-4-2",
    "expr-temporal7-5-1",
    "expr-temporal7-5-2",
    "expr-temporal7-6-8",
    "expr-typeconversion4-2",
    "expr-typeconversion4-3",
    "expr-typeconversion4-4",
    "expr-typeconversion4-5",
    "return2-10",
    "return2-9",
    "return7-1",
    "match4-1",
    "match4-5",
    "match4-6",
    "match5-21",
    "match5-23",
    "match5-25",
    "match5-26",
    "match9-2",
    "match9-3",
    "match9-4",
    "match9-5",
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
)

DIRECT_CYPHER_XFAIL_UNEXPECTED_SUCCESS_KEYS: Final[tuple[str, ...]] = (
    "expr-list1-6-4",
    "expr-typeconversion4-10-1",
    "expr-typeconversion4-10-2",
)

DIRECT_CYPHER_XFAIL_MATCHES_EXPECTED_KEYS: Final[tuple[str, ...]] = (
    "expr-comparison2-4-3",
    "expr-comparison2-4-4",
    "expr-pattern1-7",
    "expr-pattern1-8",
    "expr-pattern1-9",
    "match4-2",
    "match5-1",
    "match5-10",
    "match5-22",
    "match5-24",
    "match5-4",
    "match5-5",
    "match5-7",
    "match5-9",
    "match7-13",
    "match7-9",
)

DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY: Final[
    dict[str, DirectCypherXfailOutcome]
] = {
    **{key: "ValueError" for key in DIRECT_CYPHER_XFAIL_VALUE_ERROR_KEYS},
    **{
        key: "success_matches_expected"
        for key in DIRECT_CYPHER_XFAIL_MATCHES_EXPECTED_KEYS
    },
    **{key: "success_wrong_rows" for key in DIRECT_CYPHER_XFAIL_WRONG_ROW_KEYS},
    **{
        key: "unexpected_success_expected_error"
        for key in DIRECT_CYPHER_XFAIL_UNEXPECTED_SUCCESS_KEYS
    },
}

DIRECT_CYPHER_NONVALIDATION_XFAIL_COUNTS: Final[dict[str, int]] = dict(
    sorted(Counter(DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY.values()).items())
)

assert len(DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY) == (
    len(DIRECT_CYPHER_XFAIL_VALUE_ERROR_KEYS)
    + len(DIRECT_CYPHER_XFAIL_MATCHES_EXPECTED_KEYS)
    + len(DIRECT_CYPHER_XFAIL_WRONG_ROW_KEYS)
    + len(DIRECT_CYPHER_XFAIL_UNEXPECTED_SUCCESS_KEYS)
)


def expected_direct_cypher_xfail_outcome(key: str) -> DirectCypherXfailOutcome:
    return DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY.get(
        key, DIRECT_CYPHER_XFAIL_VALIDATION_OUTCOME
    )
