from tests.cypher_tck.scenarios import SCENARIOS


IS_NOT_IN_KEYS = {
    "firstparty-predicates-isnotin1-1": "positive-match",
    "firstparty-predicates-isnotin1-2": "negative-match",
    "firstparty-predicates-isnotin1-3": "empty-list",
    "firstparty-predicates-isnotin1-4": "none-handling",
    "firstparty-predicates-isnotin1-5": "mixed-types",
}


def test_is_not_in_first_party_smoke_inventory() -> None:
    scenarios = {
        scenario.key: scenario
        for scenario in SCENARIOS
        if scenario.key in IS_NOT_IN_KEYS
    }

    assert set(scenarios) == set(IS_NOT_IN_KEYS)

    for key, case_tag in IS_NOT_IN_KEYS.items():
        scenario = scenarios[key]
        assert scenario.status == "skip"
        assert scenario.gfql is None
        assert scenario.reason is not None
        assert "pygraphistry#966" in scenario.reason
        assert scenario.feature_path == "tck/features/firstParty/predicates/IsNotIn1.feature"
        assert scenario.return_alias == "n"
        assert "first-party" in scenario.tags
        assert "predicate" in scenario.tags
        assert "is-not-in" in scenario.tags
        assert "not-yet-implemented" in scenario.tags
        assert case_tag in scenario.tags


def test_is_not_in_first_party_smoke_expected_results() -> None:
    scenarios = {
        scenario.key: scenario
        for scenario in SCENARIOS
        if scenario.key in IS_NOT_IN_KEYS
    }

    assert scenarios["firstparty-predicates-isnotin1-1"].expected.node_ids == [
        "keep",
        "other",
    ]
    assert scenarios["firstparty-predicates-isnotin1-2"].expected.node_ids == ["drop"]
    assert scenarios["firstparty-predicates-isnotin1-3"].expected.node_ids == [
        "keep",
        "drop",
        "other",
    ]
    assert scenarios["firstparty-predicates-isnotin1-4"].expected.node_ids == [
        "keep",
        "other",
    ]
    assert scenarios["firstparty-predicates-isnotin1-5"].expected.node_ids == ["other"]
