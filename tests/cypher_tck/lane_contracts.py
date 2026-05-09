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
