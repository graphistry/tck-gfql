from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

WORKFLOW = Path(".github/workflows/nightly.yml")


def _step_script(name: str) -> str:
    for step in WORKFLOW.read_text().split("      - name: ")[1:]:
        title, _, body = step.partition("\n")
        if title == name:
            _, marker, script = body.partition("        run: |\n")
            assert marker
            return "\n".join(line[10:] for line in script.splitlines() if line)
    raise AssertionError(f"Missing workflow step: {name}")


def _job_env() -> dict[str, str]:
    block = WORKFLOW.read_text().split("    env:\n", 1)[1].split("    steps:\n", 1)[0]
    values = dict(line.strip().split(": ", 1) for line in block.splitlines() if ": " in line)
    return {**os.environ, "PYGRAPHISTRY_PATH": values["PYGRAPHISTRY_PATH"],
            "PYTHONPATH": values["PYTHONPATH"],
            "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"]}


def test_nightly_checkout_keeps_resolved_revision_after_branch_advances(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "init", str(source)], check=True, capture_output=True)
    package = source / "graphistry"
    package.mkdir()
    (package / "__init__.py").write_text('__version__ = "0.60.0"\n')
    subprocess.run(["git", "-C", str(source), "add", "."], check=True)
    commit = ["git", "-C", str(source), "-c", "user.name=TCK test",
              "-c", "user.email=tck@example.invalid", "commit", "-m"]
    subprocess.run(commit + ["resolved product"], check=True, capture_output=True)
    resolved = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    (package / "__init__.py").write_text('__version__ = "0.61.0"\n')
    subprocess.run(["git", "-C", str(source), "add", "."], check=True)
    subprocess.run(commit + ["advanced branch"], check=True, capture_output=True)
    runner = tmp_path / "runner"
    runner.mkdir()
    env = {**_job_env(), "PYGRAPHISTRY_REPO": source.as_uri(), "PYGRAPHISTRY_SHA": resolved,
           "PYGRAPHISTRY_REF": "master"}
    subprocess.run(["bash", "-e", "-c", _step_script("Checkout pygraphistry")],
                   cwd=runner, env=env, check=True, capture_output=True)
    actual = subprocess.check_output(["git", "-C", str(runner / "pygraphistry"),
                                      "rev-parse", "HEAD"], text=True).strip()
    assert actual == resolved
    subprocess.run(["bash", "-e", "-c", _step_script("Update pygraphistry badge")],
                   cwd=runner, env=env, check=True, capture_output=True)
    badge = json.loads((runner / "badges/pygraphistry-version.json").read_text())
    assert badge["message"] == "master @ 0.60.0"


def test_nightly_badge_imports_product_in_a_separate_shell(tmp_path: Path) -> None:
    package = tmp_path / "pygraphistry/graphistry"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('__version__ = "0.60.0"\n')
    env = {**_job_env(), "PYGRAPHISTRY_REF": "master"}
    subprocess.run(["bash", "-e", "-c", _step_script("Update pygraphistry badge")],
                   cwd=tmp_path, env=env, check=True, capture_output=True)
    badge = json.loads((tmp_path / "badges/pygraphistry-version.json").read_text())
    assert badge == {"schemaVersion": 1, "label": "pygraphistry",
                     "message": "master @ 0.60.0", "color": "blue"}
