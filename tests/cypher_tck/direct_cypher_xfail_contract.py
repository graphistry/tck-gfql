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

DIRECT_CYPHER_XFAIL_WRONG_ROW_KEYS: Final[tuple[str, ...]] = (
    "expr-aggregation3-1",
    "expr-comparison3-1",
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
    "match5-25",
    "match5-26",
    "match5-8",
    "return2-10",
    "return2-9",
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
    # with2-1: WITH-pipelined join (`MATCH (a:Begin) WITH a.num AS p
    # MATCH (b) WHERE b.id = p RETURN b`).  Pre-#1217 LALR/binder
    # rejected the WITH-projection-driven join shape with a validation
    # error.  Earley + the with_where_clause priority bump now lets the
    # query parse + execute, but the join semantics aren't right yet —
    # rows differ from the scenario oracle.  Real fix is out of slice 1
    # scope; lock the current outcome here.
    "with2-1",
)

DIRECT_CYPHER_XFAIL_UNEXPECTED_SUCCESS_KEYS: Final[tuple[str, ...]] = (
    "expr-list1-6-4",
    "expr-typeconversion4-10-1",
    "expr-typeconversion4-10-2",
    # match-where1-10: disjunctive WHERE predicate (`p1 = 12 OR p2 = 13`).
    # Now parses + executes under pygraphistry #1217's Earley swap; the
    # scenario only carries `node_ids`, no row-level oracle, so the TCK
    # runner returns ``unexpected_success_expected_error``.  Native
    # row-level validation lives in pygraphistry's
    # test_string_cypher_executes_disjunctive_property_predicate_returns_union
    # (see #1217).  Static-validation gap on row-boolean shapes tracked
    # in pygraphistry/#1219.
    "match-where1-10",
)

DIRECT_CYPHER_XFAIL_MATCHES_EXPECTED_BASE_KEYS: Final[tuple[str, ...]] = (
    "expr-comparison2-4-3",
    "expr-comparison2-2",
    "expr-aggregation2-7",
    "expr-aggregation2-8",
    "expr-comparison2-4-4",
    "expr-pattern1-7",
    "expr-pattern1-8",
    "expr-pattern1-9",
    "match4-2",
    "match5-1",
    "match5-10",
    "match5-16",
    "match5-17",
    "match5-18",
    "match5-4",
    "match5-5",
    "match5-6",
    "match5-7",
    "match5-9",
    "match7-13",
    "match7-9",
    "match1-5",
    "match-where3-1",
    "match-where3-2",
    "match-where4-1",
    # match-where5-{1,2,3,4} + expr-comparison2-1: string-GT-on-mixed-Series
    # scenarios.  Pygraphistry #1217 admitted them through Earley parsing
    # (raised TypeError at runtime); pygraphistry #1224 routed non-filter-dict
    # expressions through ``where_rows`` so they now execute correctly.
    # (with-where5-3 is the same pattern but lives in PROMOTION_ROW_KEYS
    # in direct_cypher_support.py, so its status flips xfail→supported and
    # it doesn't go through the xfail-contract bucket.)
    "match-where5-1",
    "match-where5-2",
    "match-where5-3",
    "match-where5-4",
    "expr-comparison2-1",
    "return-orderby2-11",
    "with-where3-1",
    "with-where3-2",
    "with-where4-1",
    "with-where1-2",
    "with-where7-1",
    "with-where7-3",
    "with-orderby2-10-1",
    "with-orderby2-10-2",
    "with-orderby2-9-1",
    "with-orderby2-9-2",
    "with-orderby2-9-3",
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
