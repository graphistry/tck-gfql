from __future__ import annotations

from tests.cypher_tck.direct_cypher_xfail_contract import (
    DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY,
)
from tests.cypher_tck.scenarios import SCENARIOS
from tests.cypher_tck.test_tck_runner import _direct_cypher_xfail_outcome


def test_direct_cypher_nonvalidation_outcome_snapshot_fastfail() -> None:
    scenarios_by_key = {scenario.key: scenario for scenario in SCENARIOS}
    expected_by_key = DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY

    missing = sorted(set(expected_by_key) - set(scenarios_by_key))
    assert missing == [], (
        "direct-cypher non-validation contract tracks missing keys; "
        f"remove/rebaseline these keys in direct_cypher_xfail_contract.py: {missing}"
    )

    no_longer_xfail = sorted(
        key
        for key in expected_by_key
        if scenarios_by_key[key].status != "xfail"
    )
    assert no_longer_xfail == [], (
        "direct-cypher non-validation contract tracks keys that are no longer xfail; "
        "move these to promotion snapshot or remove them from non-validation debt: "
        f"{no_longer_xfail}"
    )

    mismatches: list[tuple[str, str, str]] = []
    for key in sorted(expected_by_key):
        expected_outcome = expected_by_key[key]
        actual_outcome = _direct_cypher_xfail_outcome(scenarios_by_key[key])
        if actual_outcome != expected_outcome:
            mismatches.append((key, expected_outcome, actual_outcome))

    mismatch_lines = [
        f"- {key}: expected={expected}, actual={actual}"
        for key, expected, actual in mismatches
    ]
    assert mismatches == [], (
        "direct-cypher non-validation outcome drift detected; "
        "rebaseline direct_cypher_xfail_contract.py buckets for sibling-target parity:\n"
        + "\n".join(mismatch_lines)
    )
