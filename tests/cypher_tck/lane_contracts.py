from __future__ import annotations

from typing import Final


# Issue #43 tranche-1: row-pipeline read-form xfail lane.
# These keys are intentionally kept in sync with the issue body.
ROW_PIPELINE_TRANCHE1_KEYS: Final[tuple[str, ...]] = (
    "match3-24",
    "match3-25",
    "match3-26",
    "match4-8",
    "unwind1-12",
    "with4-6",
)

ROW_PIPELINE_TRANCHE1_EXPECTED_STATUS: Final[str] = "xfail"
ROW_PIPELINE_TRANCHE1_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #45 tranche-1: grouped aggregates over expanded MATCH.
GROUPED_MATCH_AGG_TRANCHE1_KEYS: Final[tuple[str, ...]] = (
    "return6-12",
    "with-skip-limit1-2",
    "with-skip-limit2-4",
    "with7-2",
)

GROUPED_MATCH_AGG_TRANCHE1_EXPECTED_STATUS: Final[str] = "xfail"
GROUPED_MATCH_AGG_TRANCHE1_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #44 tranche-1: OPTIONAL MATCH / null-extension lane.
OPTIONAL_NULL_TRANCHE1_KEYS: Final[tuple[str, ...]] = (
    "match7-27",
    "match7-29",
    "match7-30",
    "match7-31",
)

OPTIONAL_NULL_TRANCHE1_EXPECTED_STATUS: Final[str] = "xfail"
OPTIONAL_NULL_TRANCHE1_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #51 tranche-1: expression long-tail (List11 + Precedence2 clusters).
EXPRESSION_LONG_TAIL_TRANCHE1_KEYS: Final[tuple[str, ...]] = (
    "expr-list11-4-1",
    "expr-list11-4-2",
    "expr-list11-4-3",
    "expr-list11-4-4",
    "expr-list11-5-1",
    "expr-list11-5-2",
    "expr-list11-5-3",
    "expr-list11-5-4",
    "expr-list11-5-5",
    "expr-list11-5-6",
    "expr-list11-5-7",
    "expr-list11-5-8",
    "expr-list11-5-9",
    "expr-list11-5-10",
    "expr-list11-5-11",
    "expr-list11-5-12",
    "expr-list11-5-13",
    "expr-list11-5-14",
    "expr-list11-5-15",
    "expr-list11-5-16",
    "expr-list11-5-17",
    "expr-list11-5-18",
    "expr-list11-5-19",
    "expr-list11-5-20",
    "expr-list11-5-21",
    "expr-list11-5-22",
    "expr-precedence2-1-2",
    "expr-precedence2-1-5",
    "expr-precedence2-1-7",
    "expr-precedence2-1-8",
    "expr-precedence2-1-9",
    "expr-precedence2-1-10",
    "expr-precedence2-1-11",
    "expr-precedence2-1-12",
    "expr-precedence2-1-14",
    "expr-precedence2-1-17",
    "expr-precedence2-2-1",
    "expr-precedence2-2-2",
    "expr-precedence2-2-3",
    "expr-precedence2-3-1",
    "expr-precedence2-3-2",
    "expr-precedence2-4",
)

EXPRESSION_LONG_TAIL_TRANCHE1_EXPECTED_STATUS: Final[str] = "xfail"
EXPRESSION_LONG_TAIL_TRANCHE1_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #51 tranche-2: expression long-tail (Temporal4 + Aggregation6 clusters).
EXPRESSION_LONG_TAIL_TRANCHE2_KEYS: Final[tuple[str, ...]] = (
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
    "expr-temporal4-13-2",
    "expr-temporal4-13-3",
    "expr-temporal4-13-4",
    "expr-temporal4-13-6",
    "expr-temporal4-13-7",
    "expr-temporal4-13-8",
    "expr-temporal4-13-10",
    "expr-temporal4-13-11",
    "expr-temporal4-13-12",
    "expr-temporal4-13-14",
    "expr-temporal4-13-15",
    "expr-temporal4-13-16",
    "expr-temporal4-13-18",
    "expr-temporal4-13-19",
    "expr-temporal4-13-20",
)

EXPRESSION_LONG_TAIL_TRANCHE2_EXPECTED_STATUS: Final[str] = "xfail"
EXPRESSION_LONG_TAIL_TRANCHE2_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #51 tranche-3: expression long-tail (Temporal8 cluster).
EXPRESSION_LONG_TAIL_TRANCHE3_KEYS: Final[tuple[str, ...]] = (
    "expr-temporal8-6-1",
    "expr-temporal8-6-2",
    "expr-temporal8-6-3",
    "expr-temporal8-6-4",
    "expr-temporal8-6-5",
    "expr-temporal8-6-6",
    "expr-temporal8-6-7",
    "expr-temporal8-6-8",
    "expr-temporal8-6-9",
    "expr-temporal8-7-1",
    "expr-temporal8-7-2",
    "expr-temporal8-7-3",
)

EXPRESSION_LONG_TAIL_TRANCHE3_EXPECTED_STATUS: Final[str] = "xfail"
EXPRESSION_LONG_TAIL_TRANCHE3_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #52 tranche-1: residual read-only lane (variable-length + named-path anchors).
OTHER_READ_GAPS_TRANCHE1_KEYS: Final[tuple[str, ...]] = (
    "match4-1",
    "match4-3",
    "match4-4",
    "match4-5",
    "match5-2",
    "match5-11",
    "match6-1",
    "match6-2",
    "match6-3",
    "return2-9",
)

OTHER_READ_GAPS_TRANCHE1_EXPECTED_STATUS: Final[str] = "xfail"
OTHER_READ_GAPS_TRANCHE1_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)
