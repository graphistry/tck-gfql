"""Dispatch the Slack-subscribed alert workflow for a failed scheduled nightly."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


ALERT_EVENT = "nightly_conformance_failed"
NIGHTLY_NAME = "Nightly Master Conformance"
ERROR_CONCLUSIONS = frozenset({"failure", "timed_out"})


def alert_payload(event: dict) -> dict | None:
    run = event.get("workflow_run") or {}
    if (
        run.get("name") != NIGHTLY_NAME
        or run.get("event") != "schedule"
        or run.get("head_branch") != "main"
        or run.get("status") != "completed"
        or run.get("conclusion") not in ERROR_CONCLUSIONS
    ):
        return None

    return {
        "event_type": ALERT_EVENT,
        "client_payload": {
            "run_number": run["run_number"],
            "run_url": run["html_url"],
            "conclusion": run["conclusion"],
        },
    }


def dispatch(payload: dict, repository: str, token: str) -> None:
    request = Request(
        f"https://api.github.com/repos/{repository}/dispatches",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        if response.status != 204:
            raise RuntimeError(f"Unexpected dispatch status: {response.status}")


def main() -> None:
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    payload = alert_payload(event)
    if payload is None:
        print("No nightly failure; no alert dispatched.")
        return

    dispatch(payload, os.environ["GITHUB_REPOSITORY"], os.environ["GH_TOKEN"])
    print(f"Dispatched alert for nightly run #{payload['client_payload']['run_number']}.")


if __name__ == "__main__":
    main()
