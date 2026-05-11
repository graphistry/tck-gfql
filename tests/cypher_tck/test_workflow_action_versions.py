from __future__ import annotations

import re
from pathlib import Path


WORKFLOW_FILES = (
    Path(".github/workflows/ci.yml"),
    Path(".github/workflows/nightly.yml"),
)
LOCAL_GUIDANCE_FILES = (
    Path("bin/ci.sh"),
    Path("README.md"),
    Path("DEVELOP.md"),
    Path("tests/cypher_tck/analysis/phase-7.8-next-wave-plan.md"),
    Path("tests/cypher_tck/analysis/phase-7.8-post-wave-gap-inventory.md"),
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


def test_ci_preflight_checks_graphistry_row_expression_parser_backend() -> None:
    ci_script = Path("bin/ci.sh").read_text(encoding="utf-8")

    assert "graphistry.compute.gfql.expr_parser" in ci_script
    assert "graphistry.gfql.ref.enumerator" in ci_script
    assert "graphistry.tests.test_compute" in ci_script
    assert "full TCK harness modules" in ci_script
    assert 'parse_expr("1 = 1")' in ci_script
    assert "lark parser package" in ci_script
    assert "PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_PATH=/path/to/pygraphistry ./bin/ci.sh" in ci_script


def test_local_pygraphistry_full_harness_guidance_uses_editable_install() -> None:
    editable_install_command = re.compile(
        r"PYGRAPHISTRY_INSTALL=1\s+PYGRAPHISTRY_PATH=\S+\s+\./bin/ci\.sh"
    )
    source_only_full_harness_command = re.compile(
        r"(?<!PYGRAPHISTRY_INSTALL=1\s)PYGRAPHISTRY_PATH=\S+\s+\./bin/ci\.sh"
    )

    for path in LOCAL_GUIDANCE_FILES:
        text = path.read_text(encoding="utf-8")
        assert editable_install_command.search(text), (
            f"{path}: missing editable pygraphistry install guidance"
        )
        assert source_only_full_harness_command.search(text) is None, (
            f"{path}: full-harness sibling checkout guidance must install dependencies"
        )
