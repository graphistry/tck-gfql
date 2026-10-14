from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "bin/nightly_failure_dispatch.py"
ALERT_WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/nightly-failure-alert.yml"
spec = importlib.util.spec_from_file_location("nightly_failure_dispatch", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def nightly_event(conclusion: str) -> dict:
    return {
        "workflow_run": {
            "name": "Nightly Master Conformance",
            "event": "schedule",
            "head_branch": "main",
            "status": "completed",
            "conclusion": conclusion,
            "run_number": 362,
            "html_url": "https://github.com/graphistry/tck-gfql/actions/runs/38521912723",
        }
    }


def test_alert_workflow_has_stable_name_for_slack_filter() -> None:
    workflow = ALERT_WORKFLOW.read_text(encoding="utf-8")
    assert workflow.startswith("name: Nightly Conformance Failed\n")
    assert "run-name:" not in workflow


@pytest.mark.parametrize("conclusion", ["failure", "timed_out"])
def test_failed_nightly_dispatches_once(tmp_path, monkeypatch, conclusion: str) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(nightly_event(conclusion)), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_REPOSITORY", "graphistry/tck-gfql")
    monkeypatch.setenv("GH_TOKEN", "test-token")

    class Response:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    with patch.object(module, "urlopen", return_value=Response()) as post:
        module.main()

    post.assert_called_once()
    request = post.call_args.args[0]
    assert request.full_url == "https://api.github.com/repos/graphistry/tck-gfql/dispatches"
    assert request.get_method() == "POST"
    assert json.loads(request.data) == {
        "event_type": "nightly_conformance_failed",
        "client_payload": {
            "run_number": 362,
            "run_url": "https://github.com/graphistry/tck-gfql/actions/runs/38521912723",
            "conclusion": conclusion,
        },
    }


@pytest.mark.parametrize("conclusion", ["success", "cancelled", "skipped", "neutral"])
def test_non_errors_do_not_dispatch(tmp_path, monkeypatch, conclusion: str) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(nightly_event(conclusion)), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)

    with patch.object(module, "urlopen") as post:
        module.main()

    post.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", "Other Workflow"),
        ("event", "workflow_dispatch"),
        ("head_branch", "feature"),
        ("status", "in_progress"),
    ],
)
def test_other_runs_do_not_dispatch(field: str, value: str) -> None:
    event = nightly_event("failure")
    event["workflow_run"][field] = value
    assert module.alert_payload(event) is None
