from __future__ import annotations

import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

import pytest

WORKFLOW = Path(".github/workflows/nightly.yml")


def _step_script(name: str) -> str:
    for step in WORKFLOW.read_text().split("      - name: ")[1:]:
        title, _, body = step.partition("\n")
        if title == name:
            _, marker, script = body.partition("        run: |\n")
            assert marker
            lines: list[str] = []
            for line in script.splitlines():
                if line and not line.startswith("          "):
                    break
                lines.append(line[10:])
            return "\n".join(lines)
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


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(cwd), *args], text=True,
                                   stderr=subprocess.STDOUT).strip()


@pytest.mark.parametrize("default_branch,ref,publishes", [
    ("main", "refs/heads/main", True),
    ("trunk", "refs/heads/trunk", True),
    ("main", "refs/heads/feature", False),
    ("main", "refs/heads/main-copy", False),
    ("main", "refs/tags/main", False),
    ("main", "refs/pull/203/merge", False),
])
@pytest.mark.parametrize("changed", [True, False])
def test_nightly_badge_pushes_only_changed_default_branch(
    tmp_path: Path, default_branch: str, ref: str, publishes: bool, changed: bool,
) -> None:
    workflow = WORKFLOW.read_text()
    commit_step = workflow.split("      - name: Commit badge\n", 1)[1]
    assert "DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}" in commit_step
    update_step = workflow.split("      - name: Update pygraphistry badge\n", 1)[1]
    assert "github.event_name == 'pull_request'" in update_step.split("        run:", 1)[0]
    branch = ref.removeprefix("refs/heads/") if ref.startswith("refs/heads/") else default_branch
    remote = tmp_path / "remote.git"
    remote.mkdir()
    _git(remote, "init", "--bare")
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _git(checkout, "init", "-b", branch)
    _git(checkout, "remote", "add", "origin", str(remote))
    badge = checkout / "badges/pygraphistry-version.json"
    badge.parent.mkdir()
    original = '{"schemaVersion":1,"label":"pygraphistry","message":"old","color":"blue"}\n'
    badge.write_text(original)
    _git(checkout, "add", ".")
    _git(checkout, "-c", "user.name=TCK test", "-c", "user.email=tck@example.invalid",
         "commit", "-m", "initial badge")
    _git(checkout, "push", "-u", "origin", branch)
    before = _git(checkout, "rev-parse", "HEAD")
    if changed:
        badge.write_text(original.replace('"old"', '"new"'))
    env = {**os.environ, "DEFAULT_BRANCH": default_branch, "GITHUB_REF": ref}
    subprocess.run(["bash", "-e", "-c", _step_script("Commit badge")],
                   cwd=checkout, env=env, check=True, capture_output=True)
    after = _git(checkout, "rev-parse", "HEAD")
    assert (after != before) == (publishes and changed)
    assert _git(remote, "rev-parse", f"refs/heads/{branch}") == after
    assert _git(checkout, "show", "HEAD:badges/pygraphistry-version.json") == (
        badge.read_text().strip() if publishes and changed else original.strip())


@pytest.mark.parametrize("configured,curl_exit", [(True, 0), (True, 22), (False, 0)])
def test_nightly_slack_failure_delivery(
    tmp_path: Path, configured: bool, curl_exit: int,
) -> None:
    notification = WORKFLOW.read_text().split("  notify-slack:\n", 1)[1]
    assert "needs: nightly" in notification
    assert "if: ${{ always() && github.event_name == 'schedule' && needs.nightly.result == 'failure' }}" in notification
    assert "permissions: {}" in notification
    assert "SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}" in notification
    requests: list[tuple[str, str, bytes]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            requests.append((self.path, self.headers["Content-Type"],
                             self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(403 if curl_exit else 200)
            self.end_headers()
            self.wfile.write(b"invalid_payload" if curl_exit else b"ok")

        def log_message(self, format: str, *args: object) -> None:
            pass

    run_url = "https://github.com/graphistry/tck-gfql/actions/runs/123"
    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        webhook = f"http://127.0.0.1:{server.server_port}/alerts" if configured else ""
        env = {**os.environ, "SLACK_WEBHOOK_URL": webhook, "RUN_URL": run_url,
               "NO_PROXY": "127.0.0.1", "no_proxy": "127.0.0.1"}
        try:
            result = subprocess.run(["bash", "-e", "-c", _step_script("Alert Slack")],
                                    cwd=tmp_path, env=env, capture_output=True, text=True,
                                    check=False, timeout=20)
        finally:
            server.shutdown()
            worker.join(timeout=2)
    assert result.returncode == curl_exit
    if not configured:
        assert requests == []
        assert result.stdout.startswith("::warning::")
        return
    assert len(requests) == 1
    path, content_type, payload = requests[0]
    assert path == "/alerts"
    assert content_type == "application/json"
    assert json.loads(payload) == {
        "text": "GFQL nightly failed: " + run_url,
    }
    assert webhook not in result.stdout + result.stderr
