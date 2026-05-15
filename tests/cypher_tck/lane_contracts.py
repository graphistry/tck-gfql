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


# Issue #43 tranche-2: row-pipeline read forms (WITH/ORDER BY/SKIP/LIMIT anchors).
ROW_PIPELINE_TRANCHE2_KEYS: Final[tuple[str, ...]] = (
    "with1-1",
    "with1-2",
    "with1-3",
    "with1-4",
    "with2-1",
    "with3-1",
    "with4-1",
    "with5-2",
    "with-skip-limit1-1",
    "with-skip-limit2-2",
    "with-skip-limit2-3",
    "with7-1",
)

ROW_PIPELINE_TRANCHE2_EXPECTED_STATUS: Final[str] = "xfail"
ROW_PIPELINE_TRANCHE2_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #43 tranche-3: row-pipeline read forms (remaining non-expression anchors).
ROW_PIPELINE_TRANCHE3_KEYS: Final[tuple[str, ...]] = (
    "match6-18",
    "match8-1",
    "match9-6",
    "match9-7",
    "return-orderby1-11",
    "return-orderby1-12",
    "return-orderby2-12",
    "return-orderby6-1",
    "return-orderby6-3",
    "return4-11",
    "return6-13",
    "unwind1-5",
    "with-orderby1-21",
    "with-orderby1-22",
    "with-where2-1",
    "with-where2-2",
    "with-where3-3",
    "with-where4-2",
    "with6-5",
    "with6-6",
    "with6-7",
)

ROW_PIPELINE_TRANCHE3_EXPECTED_STATUS: Final[str] = "xfail"
ROW_PIPELINE_TRANCHE3_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #43 tranche-4: row-pipeline expression forms (quantifier11 residual cluster).
ROW_PIPELINE_TRANCHE4_KEYS: Final[tuple[str, ...]] = (
    "expr-quantifier11-3-1",
    "expr-quantifier11-3-2",
    "expr-quantifier11-3-3",
    "expr-quantifier11-3-4",
    "expr-quantifier11-3-5",
    "expr-quantifier11-4-1",
    "expr-quantifier11-4-2",
    "expr-quantifier11-4-3",
    "expr-quantifier11-4-4",
    "expr-quantifier11-4-5",
    "expr-quantifier11-5-1",
    "expr-quantifier11-5-2",
    "expr-quantifier11-5-3",
    "expr-quantifier11-5-4",
    "expr-quantifier11-5-5",
    "expr-quantifier11-6-1",
    "expr-quantifier11-6-2",
    "expr-quantifier11-6-3",
    "expr-quantifier11-6-4",
    "expr-quantifier11-6-5",
)

ROW_PIPELINE_TRANCHE4_EXPECTED_STATUS: Final[str] = "xfail"
ROW_PIPELINE_TRANCHE4_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #43 tranche-5: row-pipeline expression forms (quantifier12 residual cluster).
ROW_PIPELINE_TRANCHE5_KEYS: Final[tuple[str, ...]] = (
    "expr-quantifier12-3-1",
    "expr-quantifier12-3-2",
    "expr-quantifier12-3-3",
    "expr-quantifier12-3-4",
    "expr-quantifier12-3-5",
    "expr-quantifier12-4-1",
    "expr-quantifier12-4-2",
    "expr-quantifier12-4-3",
    "expr-quantifier12-4-4",
    "expr-quantifier12-4-5",
    "expr-quantifier12-5-1",
    "expr-quantifier12-5-2",
    "expr-quantifier12-5-3",
    "expr-quantifier12-5-4",
    "expr-quantifier12-5-5",
)

ROW_PIPELINE_TRANCHE5_EXPECTED_STATUS: Final[str] = "xfail"
ROW_PIPELINE_TRANCHE5_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #43 tranche-6: row-pipeline expression forms (quantifier9 residual cluster).
ROW_PIPELINE_TRANCHE6_KEYS: Final[tuple[str, ...]] = (
    "expr-quantifier9-3-1",
    "expr-quantifier9-3-2",
    "expr-quantifier9-3-3",
    "expr-quantifier9-3-4",
    "expr-quantifier9-3-5",
    "expr-quantifier9-4-1",
    "expr-quantifier9-4-2",
    "expr-quantifier9-4-3",
    "expr-quantifier9-4-4",
    "expr-quantifier9-4-5",
    "expr-quantifier9-5-1",
    "expr-quantifier9-5-2",
    "expr-quantifier9-5-3",
    "expr-quantifier9-5-4",
    "expr-quantifier9-5-5",
)

ROW_PIPELINE_TRANCHE6_EXPECTED_STATUS: Final[str] = "xfail"
ROW_PIPELINE_TRANCHE6_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #43 tranche-7: row-pipeline expression forms (temporal8 residual cluster).
ROW_PIPELINE_TRANCHE7_KEYS: Final[tuple[str, ...]] = (
    "expr-temporal8-1-1",
    "expr-temporal8-1-2",
    "expr-temporal8-1-3",
    "expr-temporal8-2-1",
    "expr-temporal8-2-2",
    "expr-temporal8-2-3",
    "expr-temporal8-3-1",
    "expr-temporal8-3-2",
    "expr-temporal8-3-3",
    "expr-temporal8-4-1",
    "expr-temporal8-4-2",
    "expr-temporal8-4-3",
    "expr-temporal8-5-1",
    "expr-temporal8-5-2",
    "expr-temporal8-5-3",
)

ROW_PIPELINE_TRANCHE7_EXPECTED_STATUS: Final[str] = "xfail"
ROW_PIPELINE_TRANCHE7_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #43 tranche-8: row-pipeline expression forms (temporal5 residual cluster).
ROW_PIPELINE_TRANCHE8_KEYS: Final[tuple[str, ...]] = (
    "expr-temporal5-1",
    "expr-temporal5-2",
    "expr-temporal5-3",
    "expr-temporal5-4",
    "expr-temporal5-5",
    "expr-temporal5-6",
    "expr-temporal5-7",
)

ROW_PIPELINE_TRANCHE8_EXPECTED_STATUS: Final[str] = "xfail"
ROW_PIPELINE_TRANCHE8_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #43 tranche-9: row-pipeline expression forms (map1 residual cluster).
ROW_PIPELINE_TRANCHE9_KEYS: Final[tuple[str, ...]] = (
    "expr-map1-5-1",
    "expr-map1-5-2",
    "expr-map1-5-3",
    "expr-map1-5-4",
    "expr-map1-5-5",
    "expr-map1-5-6",
)

ROW_PIPELINE_TRANCHE9_EXPECTED_STATUS: Final[str] = "xfail"
ROW_PIPELINE_TRANCHE9_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #43 tranche-10: row-pipeline expression forms (quantifier10 residual cluster).
ROW_PIPELINE_TRANCHE10_KEYS: Final[tuple[str, ...]] = (
    "expr-quantifier10-4-1",
    "expr-quantifier10-4-2",
    "expr-quantifier10-4-3",
    "expr-quantifier10-4-4",
    "expr-quantifier10-4-5",
)

ROW_PIPELINE_TRANCHE10_EXPECTED_STATUS: Final[str] = "xfail"
ROW_PIPELINE_TRANCHE10_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #43 tranche-11: row-pipeline expression forms (comparison1 residual cluster).
ROW_PIPELINE_TRANCHE11_KEYS: Final[tuple[str, ...]] = (
    "expr-comparison1-1",
    "expr-comparison1-2",
    "expr-comparison1-3",
    "expr-comparison1-4",
)

ROW_PIPELINE_TRANCHE11_EXPECTED_STATUS: Final[str] = "xfail"
ROW_PIPELINE_TRANCHE11_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #43 tranche-12: row-pipeline expression forms (comparison2 residual cluster).
ROW_PIPELINE_TRANCHE12_KEYS: Final[tuple[str, ...]] = (
    "expr-comparison2-3-1",
    "expr-comparison2-3-2",
    "expr-comparison2-3-3",
    "expr-comparison2-3-4",
)

ROW_PIPELINE_TRANCHE12_EXPECTED_STATUS: Final[str] = "xfail"
ROW_PIPELINE_TRANCHE12_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #43 tranche-13: row-pipeline expression forms (list1 residual cluster).
ROW_PIPELINE_TRANCHE13_KEYS: Final[tuple[str, ...]] = (
    "expr-list1-3",
    "expr-list1-4",
    "expr-list1-5",
    "expr-list1-6-4",
)

ROW_PIPELINE_TRANCHE13_EXPECTED_STATUS: Final[str] = "xfail"
ROW_PIPELINE_TRANCHE13_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #43 tranche-14: row-pipeline expression forms (final residual sweep).
ROW_PIPELINE_TRANCHE14_KEYS: Final[tuple[str, ...]] = (
    "expr-string8-8",
    "expr-string9-8",
    "expr-aggregation2-11",
    "expr-aggregation2-12",
    "expr-aggregation6-5",
    "expr-list12-5",
    "expr-list2-10",
    "expr-list2-11",
    "expr-map2-1",
    "expr-map2-2",
    "expr-pattern2-11",
    "expr-precedence4-4",
    "expr-quantifier1-8",
    "expr-quantifier2-8",
    "expr-quantifier3-8",
    "expr-quantifier4-8",
    "expr-string10-8",
    "expr-string4-1",
    "expr-typeconversion2-5",
    "expr-typeconversion3-4",
)

ROW_PIPELINE_TRANCHE14_EXPECTED_STATUS: Final[str] = "xfail"
ROW_PIPELINE_TRANCHE14_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
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


# Issue #45 tranche-2: grouped aggregates over expanded MATCH (non-expression anchors).
GROUPED_MATCH_AGG_TRANCHE2_KEYS: Final[tuple[str, ...]] = (
    "match8-3",
    "match9-5",
    "return4-6",
    "return6-8",
    "return6-16",
    "usecase-countingsubgraphmatches1-4",
    "usecase-countingsubgraphmatches1-5",
    "usecase-countingsubgraphmatches1-8",
    "usecase-countingsubgraphmatches1-10",
    "with-where6-1",
    "with6-2",
    "with6-3",
    "with6-4",
)

GROUPED_MATCH_AGG_TRANCHE2_EXPECTED_STATUS: Final[str] = "xfail"
GROUPED_MATCH_AGG_TRANCHE2_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #45 tranche-3: grouped aggregates over expanded MATCH (remaining expression anchors).
GROUPED_MATCH_AGG_TRANCHE3_KEYS: Final[tuple[str, ...]] = (
    "expr-comparison1-5",
    "expr-existentialsubquery2-2",
    "expr-pattern2-6",
    "expr-pattern2-8",
    "expr-pattern2-9",
    "expr-quantifier1-9",
    "expr-quantifier2-9",
    "expr-quantifier3-9",
    "expr-quantifier4-9",
)

GROUPED_MATCH_AGG_TRANCHE3_EXPECTED_STATUS: Final[str] = "xfail"
GROUPED_MATCH_AGG_TRANCHE3_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
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


# Issue #44 tranche-2: OPTIONAL MATCH / null-extension (core match7 cluster).
OPTIONAL_NULL_TRANCHE2_KEYS: Final[tuple[str, ...]] = (
    "match7-2",
    "match7-3",
    "match7-4",
    "match7-5",
    "match7-6",
    "match7-8",
    "match7-10",
    "match7-11",
    "match7-12",
    "match7-21",
    "match7-22",
    "match7-23",
    "match7-25",
    "match7-26",
)

OPTIONAL_NULL_TRANCHE2_EXPECTED_STATUS: Final[str] = "xfail"
OPTIONAL_NULL_TRANCHE2_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #44 tranche-3: OPTIONAL MATCH / null-extension (triadic selection usecase cluster).
OPTIONAL_NULL_TRANCHE3_KEYS: Final[tuple[str, ...]] = (
    "usecase-triadicselection1-2",
    "usecase-triadicselection1-3",
    "usecase-triadicselection1-4",
    "usecase-triadicselection1-5",
    "usecase-triadicselection1-6",
    "usecase-triadicselection1-7",
    "usecase-triadicselection1-8",
    "usecase-triadicselection1-9",
    "usecase-triadicselection1-10",
    "usecase-triadicselection1-11",
    "usecase-triadicselection1-12",
    "usecase-triadicselection1-13",
    "usecase-triadicselection1-14",
    "usecase-triadicselection1-15",
    "usecase-triadicselection1-16",
    "usecase-triadicselection1-17",
    "usecase-triadicselection1-18",
    "usecase-triadicselection1-19",
)

OPTIONAL_NULL_TRANCHE3_EXPECTED_STATUS: Final[str] = "xfail"
OPTIONAL_NULL_TRANCHE3_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #44 tranche-4: OPTIONAL MATCH / null-extension (remaining residual slice).
OPTIONAL_NULL_TRANCHE4_KEYS: Final[tuple[str, ...]] = (
    "expr-aggregation5-1",
    "expr-aggregation5-2",
    "expr-graph9-3",
    "expr-list12-3",
    "expr-null1-3",
    "expr-null2-3",
    "expr-path1-1",
    "expr-path2-3",
    "match-where6-2",
    "match-where6-5",
    "match-where6-6",
    "match-where6-7",
    "match-where6-8",
    "match3-27",
    "match3-28",
    "match7-14",
    "match7-15",
    "match7-16",
    "match7-17",
    "match7-18",
    "match7-19",
    "match7-20",
    "match9-8",
    "match9-9",
    "with-where1-3",
    "with-where1-4",
    "with1-5",
    "with1-6",
)

OPTIONAL_NULL_TRANCHE4_EXPECTED_STATUS: Final[str] = "xfail"
OPTIONAL_NULL_TRANCHE4_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
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


# Issue #51 tranche-4: expression long-tail (Pattern1 + Pattern2 clusters).
EXPRESSION_LONG_TAIL_TRANCHE4_KEYS: Final[tuple[str, ...]] = (
    "expr-pattern1-12",
    "expr-pattern1-14",
    "expr-pattern1-15",
    "expr-pattern1-16",
    "expr-pattern1-17",
    "expr-pattern2-1",
    "expr-pattern2-2",
    "expr-pattern2-3",
    "expr-pattern2-4",
    "expr-pattern2-5",
    "expr-pattern2-7",
    "expr-pattern2-10",
)

EXPRESSION_LONG_TAIL_TRANCHE4_EXPECTED_STATUS: Final[str] = "xfail"
EXPRESSION_LONG_TAIL_TRANCHE4_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #51 tranche-5: expression long-tail (Comparison1 + Comparison2 clusters).
EXPRESSION_LONG_TAIL_TRANCHE5_KEYS: Final[tuple[str, ...]] = (
    "expr-comparison2-5-1",
    "expr-comparison2-5-2",
    "expr-comparison2-5-3",
    "expr-comparison2-5-4",
    "expr-comparison2-6-1",
    "expr-comparison2-6-2",
    "expr-comparison2-6-3",
    "expr-comparison2-6-4",
    "expr-comparison1-14",
    "expr-comparison1-6-5",
    "expr-comparison1-7-12",
    "expr-comparison1-7-13",
    "expr-comparison1-7-14",
    "expr-comparison1-7-15",
    "expr-comparison1-7-16",
)

EXPRESSION_LONG_TAIL_TRANCHE5_EXPECTED_STATUS: Final[str] = "xfail"
EXPRESSION_LONG_TAIL_TRANCHE5_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #51 tranche-6: expression long-tail
# (Literals5 + Null3 + Precedence3 + TypeConversion4 clusters).
EXPRESSION_LONG_TAIL_TRANCHE6_KEYS: Final[tuple[str, ...]] = (
    "expr-literals5-11",
    "expr-literals5-12",
    "expr-literals5-25",
    "expr-literals5-26",
    "expr-literals5-5",
    "expr-literals5-6",
    "expr-null3-4-1",
    "expr-null3-4-2",
    "expr-null3-4-3",
    "expr-null3-4-5",
    "expr-null3-4-6",
    "expr-null3-4-7",
    "expr-precedence3-6-1",
    "expr-precedence3-6-2",
    "expr-precedence3-6-3",
    "expr-precedence3-6-4",
    "expr-precedence3-6-5",
    "expr-precedence3-6-6",
    "expr-typeconversion4-10-1",
    "expr-typeconversion4-10-2",
    "expr-typeconversion4-2",
    "expr-typeconversion4-3",
    "expr-typeconversion4-4",
    "expr-typeconversion4-5",
)

EXPRESSION_LONG_TAIL_TRANCHE6_EXPECTED_STATUS: Final[str] = "xfail"
EXPRESSION_LONG_TAIL_TRANCHE6_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #51 tranche-7: expression long-tail
# (Quantifier7 + ExistentialSubquery1/3 + List5/List6 residual bundle).
EXPRESSION_LONG_TAIL_TRANCHE7_KEYS: Final[tuple[str, ...]] = (
    "expr-quantifier7-3-1",
    "expr-quantifier7-3-2",
    "expr-quantifier7-3-3",
    "expr-quantifier7-3-4",
    "expr-quantifier7-3-5",
    "expr-existentialsubquery1-1",
    "expr-existentialsubquery1-2",
    "expr-existentialsubquery1-3",
    "expr-existentialsubquery1-4",
    "expr-existentialsubquery3-1",
    "expr-existentialsubquery3-2",
    "expr-existentialsubquery3-3",
    "expr-list5-21",
    "expr-list5-29",
    "expr-list5-31",
    "expr-list5-34",
    "expr-list6-7",
    "expr-list6-8",
    "expr-list6-9",
    "expr-list6-10",
)

EXPRESSION_LONG_TAIL_TRANCHE7_EXPECTED_STATUS: Final[str] = "xfail"
EXPRESSION_LONG_TAIL_TRANCHE7_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #51 tranche-8: expression long-tail
# (List12 + Literals6/7/8 + Path2 + String10 residual bundle).
EXPRESSION_LONG_TAIL_TRANCHE8_KEYS: Final[tuple[str, ...]] = (
    "expr-list12-4",
    "expr-list12-6",
    "expr-literals6-5",
    "expr-literals7-7",
    "expr-literals7-18",
    "expr-literals8-11",
    "expr-literals8-18",
    "expr-path2-1",
    "expr-path2-2",
)

EXPRESSION_LONG_TAIL_TRANCHE8_EXPECTED_STATUS: Final[str] = "xfail"
EXPRESSION_LONG_TAIL_TRANCHE8_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #51 tranche-9: expression long-tail (final residual sweep).
EXPRESSION_LONG_TAIL_TRANCHE9_KEYS: Final[tuple[str, ...]] = (
    "expr-aggregation3-1",
    "expr-comparison4-1",
    "expr-existentialsubquery2-1",
    "expr-graph4-2",
    "expr-list3-7",
    "expr-map3-2",
    "expr-path3-1",
    "expr-temporal2-6-5",
    "expr-typeconversion2-6",
)

EXPRESSION_LONG_TAIL_TRANCHE9_EXPECTED_STATUS: Final[str] = "xfail"
EXPRESSION_LONG_TAIL_TRANCHE9_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
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


# Issue #54 tranche-1: write-clause lane (cross-clause anchor keys).
WRITE_CLAUSES_TRANCHE1_KEYS: Final[tuple[str, ...]] = (
    "create1-1",
    "create2-1",
    "create6-1",
    "merge1-1",
    "merge2-1",
    "set1-1",
    "set3-1",
    "delete1-1",
    "delete5-1",
    "remove1-1",
    "remove3-1",
)

WRITE_CLAUSES_TRANCHE1_EXPECTED_STATUS: Final[str] = "xfail"
WRITE_CLAUSES_TRANCHE1_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)


# Issue #53 tranche-1: procedures/CALL lane (registry + invocation + YIELD anchors).
PROCEDURES_CALL_TRANCHE1_KEYS: Final[tuple[str, ...]] = (
    "call1-1",
    "call1-13",
    "call2-1",
    "call2-3",
    "call3-2",
    "call5-3-1",
    "call5-4-1",
    "call5-8",
    "call6-1",
    "call6-2",
)

PROCEDURES_CALL_TRANCHE1_EXPECTED_STATUS: Final[str] = "xfail"
PROCEDURES_CALL_TRANCHE1_FORBIDDEN_TAGS: Final[tuple[str, ...]] = (
    "cypher-string",
    "phase1-executor",
)
