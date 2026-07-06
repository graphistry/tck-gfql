from __future__ import annotations

from collections import Counter
from typing import Final, Literal


DirectCypherXfailOutcome = Literal[
    "GFQLValidationError",
    "ValueError",
    "TypeError",
    "success_matches_expected",
    "success_wrong_rows",
    "unexpected_success_expected_error",
]


DIRECT_CYPHER_XFAIL_VALIDATION_OUTCOME: Final[DirectCypherXfailOutcome] = (
    "GFQLValidationError"
)

# Audit snapshot is pinned to the current sibling CI target for this branch pair.
DIRECT_CYPHER_XFAIL_VALUE_ERROR_KEYS: Final[tuple[str, ...]] = ()

# Pygraphistry #1224 (row-boolean WHERE in connected OPTIONAL MATCH +
# routes non-filter-dict expressions through ``where_rows``) lifted the
# string-GT-on-mixed-Series TypeError pattern: those scenarios now
# execute and return correct rows.  Bucket emptied; left in place as
# Final[tuple[str, ...]] so the ``DirectCypherXfailOutcome["TypeError"]``
# Literal stays valid for any future xfail that legitimately needs it.
DIRECT_CYPHER_XFAIL_TYPE_ERROR_KEYS: Final[tuple[str, ...]] = ()

# with2-1 (the last wrong-row entry) was reconciled in tck-gfql#115: its
# `success_wrong_rows` outcome was a fixture-modeling artifact, not a
# pygraphistry join bug.  The ported `graph_fixture_from_create` setup
# stringified the `a.id` property reference and conflated the Cypher `id`
# property with the node-identity column; with an explicit fixture the
# WITH-pipelined join returns the expected row, so with2-1 is promoted.
# pygraphistry#1490 shifts one counting-subgraph use case into wrong-row
# execution; keep it tracked as branch-paired drift until promoted/reconciled.
DIRECT_CYPHER_XFAIL_WRONG_ROW_KEYS: Final[tuple[str, ...]] = (
    # tck-gfql#119 fixes Scenario Outline placeholder substitution for these
    # comparison cases; direct Cypher now executes but returns rows that do not
    # match the TCK oracle while the scenarios remain expression-lane xfails.
    "expr-comparison2-6-3",
    "expr-comparison2-6-4",
    "usecase-countingsubgraphmatches1-2",
)

DIRECT_CYPHER_XFAIL_UNEXPECTED_SUCCESS_KEYS: Final[tuple[str, ...]] = ()

DIRECT_CYPHER_PROMOTED_FROM_XFAIL_MATCHES_EXPECTED_KEYS: Final[tuple[str, ...]] = (
    # These keys now match their expected row oracle via the direct-Cypher row
    # support snapshot and are no longer tracked as xfail non-validation debt.
    "expr-aggregation3-1",
    "expr-comparison1-6-5",
    "expr-comparison1-7-12",
    "expr-comparison1-7-13",
    "expr-comparison1-7-14",
    "expr-comparison1-7-15",
    "expr-comparison1-7-16",
    "expr-comparison2-5-1",
    "expr-comparison2-5-2",
    "expr-comparison2-5-3",
    "expr-comparison2-5-4",
    "expr-comparison2-6-1",
    "expr-comparison2-6-2",
    "expr-comparison3-1",
    "expr-comparison3-2",
    "expr-comparison3-3",
    "expr-comparison3-4",
    "expr-comparison3-5",
    "expr-comparison3-6",
    "expr-comparison3-7",
    "expr-comparison3-8",
    "expr-list1-3",
    "expr-list1-4",
    "expr-list1-5",
    "expr-list2-10",
    "expr-list2-11",
    "expr-list3-7",
    "expr-list12-3",
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
    "expr-literals6-5",
    "expr-literals7-18",
    "expr-literals7-7",
    "expr-literals8-18",
    "expr-literals8-11",
    "expr-graph3-5",
    "expr-map3-2",
    "expr-mathematical8-1",
    "expr-mathematical8-2",
    "expr-null1-3",
    "expr-null2-3",
    "expr-null3-4-1",
    "expr-null3-4-2",
    "expr-null3-4-3",
    "expr-null3-4-5",
    "expr-null3-4-6",
    "expr-null3-4-7",
    "expr-pattern1-10",
    "expr-pattern1-12",
    "expr-pattern1-13",
    "expr-pattern1-14",
    "expr-pattern1-15",
    "expr-pattern1-16",
    "expr-pattern1-17",
    "expr-pattern1-18",
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
    "expr-precedence3-6-1",
    "expr-precedence3-6-2",
    "expr-quantifier7-3-1",
    "expr-quantifier7-3-2",
    "expr-quantifier7-3-3",
    "expr-quantifier7-3-4",
    "expr-quantifier7-3-5",
    "return2-10",
    "return2-9",
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
    "expr-typeconversion2-6",
    "expr-typeconversion4-2",
    "expr-typeconversion4-3",
    "expr-typeconversion4-4",
    "expr-typeconversion4-5",
    "return-orderby2-6",
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
    "match-where1-10",
    "match-where3-3",
    "match3-1",
    "match3-5",
    "match3-7",
    "match4-3",
    "match5-25",
    "match5-26",
    "match5-8",
    "match7-24",
    "usecase-countingsubgraphmatches1-5",
    "usecase-countingsubgraphmatches1-6",
    "usecase-countingsubgraphmatches1-7",
    "usecase-countingsubgraphmatches1-9",
    "with-where3-3",
    "with2-1",
)
DIRECT_CYPHER_XFAIL_MATCHES_EXPECTED_BASE_KEYS: Final[tuple[str, ...]] = (
    # Empty after tck-gfql#142: all tracked success_matches_expected xfails
    # are represented in the direct-Cypher row support snapshot.
)
DIRECT_CYPHER_XFAIL_MATCHES_EXPECTED_KEYS: Final[tuple[str, ...]] = (
    *DIRECT_CYPHER_XFAIL_MATCHES_EXPECTED_BASE_KEYS,
)

DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY: Final[
    dict[str, DirectCypherXfailOutcome]
] = {
    **{key: "ValueError" for key in DIRECT_CYPHER_XFAIL_VALUE_ERROR_KEYS},
    **{key: "TypeError" for key in DIRECT_CYPHER_XFAIL_TYPE_ERROR_KEYS},
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
    + len(DIRECT_CYPHER_XFAIL_TYPE_ERROR_KEYS)
    + len(DIRECT_CYPHER_XFAIL_MATCHES_EXPECTED_KEYS)
    + len(DIRECT_CYPHER_XFAIL_WRONG_ROW_KEYS)
    + len(DIRECT_CYPHER_XFAIL_UNEXPECTED_SUCCESS_KEYS)
)


def expected_direct_cypher_xfail_outcome(key: str) -> DirectCypherXfailOutcome:
    return DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY.get(
        key, DIRECT_CYPHER_XFAIL_VALIDATION_OUTCOME
    )
