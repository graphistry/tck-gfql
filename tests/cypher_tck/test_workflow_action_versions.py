from __future__ import annotations

import re
from pathlib import Path


WORKFLOW_FILES = (
    Path(".github/workflows/ci.yml"),
    Path(".github/workflows/nightly.yml"),
)

MIN_ACTION_MAJORS = {
    "actions/checkout": 6,
    "actions/setup-python": 6,
    "astral-sh/setup-uv": 7,
}

USES_RE = re.compile(r"uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@v(\d+)")


def _workflow_action_majors(path: Path) -> dict[str, int]:
    majors: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = USES_RE.search(line)
        if match is None:
            continue
        action, major = match.group(1), int(match.group(2))
        majors[action] = major
    return majors


def test_target_workflows_exist() -> None:
    for workflow_path in WORKFLOW_FILES:
        assert workflow_path.exists(), f"Missing workflow: {workflow_path}"


def test_ci_action_majors_meet_minimums() -> None:
    for workflow_path in WORKFLOW_FILES:
        action_majors = _workflow_action_majors(workflow_path)
        for action, min_major in MIN_ACTION_MAJORS.items():
            assert action in action_majors, (
                f"{workflow_path}: missing required action pin for {action}@v{min_major}+"
            )
            observed = action_majors[action]
            assert observed >= min_major, (
                f"{workflow_path}: {action}@v{observed} is below required v{min_major}"
            )
