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
