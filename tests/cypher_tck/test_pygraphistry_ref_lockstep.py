"""Every default pygraphistry ref in this repo must name the same integration branch.

pygraphistry integrates on ``develop`` and ``master`` only moves at release time, so a harness
promotion paired with a develop-merged product change is red against ``master`` (nightly run
45123528567 failed on expr-map2-1 for exactly this reason). The defaults live in four places that
drifted apart once already (#224 moved ci.yml only); this test keeps them in lockstep.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

INTEGRATION_BRANCH = "develop"
WORKFLOWS = Path(".github/workflows")


def _text(path: Path) -> str:
    return path.read_text()


def _nightly_env_block() -> str:
    return _text(WORKFLOWS / "nightly.yml").split("    env:\n", 1)[1].split("    steps:\n", 1)[0]


def test_ci_workflow_falls_back_to_the_integration_branch() -> None:
    ci = _text(WORKFLOWS / "ci.yml")
    assert f'pygraphistry_ref="{INTEGRATION_BRANCH}"' in ci
    assert f'candidate_ref="{INTEGRATION_BRANCH}"' in ci


def test_nightly_defaults_to_the_integration_branch() -> None:
    nightly = _text(WORKFLOWS / "nightly.yml")
    assert (
        f"PYGRAPHISTRY_REF: ${{{{ github.event.inputs.pygraphistry_ref || '{INTEGRATION_BRANCH}' }}}}" in nightly
    )
    dispatch_input = nightly.split("      pygraphistry_ref:\n", 1)[1].split("      pygraphistry_repo:", 1)[0]
    assert f'default: "{INTEGRATION_BRANCH}"' in dispatch_input
    assert "'master'" not in _nightly_env_block()


def test_pr_conformance_summary_uses_the_integration_branch_as_base_and_fallback() -> None:
    summary = _text(WORKFLOWS / "pr-conformance-summary.yml")
    assert f'base_ref="{INTEGRATION_BRANCH}"' in summary
    assert f'candidate_ref="{INTEGRATION_BRANCH}"' in summary
    assert 'base_ref="master"' not in summary


def test_local_ci_script_defaults_to_the_integration_branch() -> None:
    script = _text(Path("bin/ci.sh"))
    assert f'ref="${{PYGRAPHISTRY_REF:-{INTEGRATION_BRANCH}}}"' in script
    assert "PYGRAPHISTRY_REF:-master" not in script


@pytest.mark.parametrize(
    "path",
    [WORKFLOWS / "ci.yml", WORKFLOWS / "nightly.yml", WORKFLOWS / "pr-conformance-summary.yml", Path("bin/ci.sh")],
)
def test_no_default_ref_assignment_names_master(path: Path) -> None:
    """Catch a new master default introduced in a spelling the specific tests above do not know."""
    assignments = re.findall(
        r"""(?:ref|base_ref|candidate_ref|pygraphistry_ref|PYGRAPHISTRY_REF)(?:=|: )["']?(?:\$\{[^}]*:-)?master\b""",
        _text(path),
    )
    assert assignments == []
