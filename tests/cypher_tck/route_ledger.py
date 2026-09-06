"""Per-route conformance ledger: diff a routes-off TCK run against the baseline run.

Two lists come out of each pair of junit files:

* ``masked`` — scenarios that pass at baseline and fail with the route off: the general
  path is wrong there and the route was hiding it.
* ``route-wrong`` — scenarios that fail (or are expected failures) at baseline and pass with
  the route off: the route admits the shape and answers it differently from the general
  path, which conformance says is right.

Usage: ``python -m tests.cypher_tck.route_ledger BASELINE.xml MODE.xml [--mode NAME]``.
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict


def outcomes(junit: Path) -> Dict[str, str]:
    """Map ``classname::name`` to passed / failed / error / skipped / xfailed / xpassed."""
    out: Dict[str, str] = {}
    for case in ET.parse(junit).getroot().iter("testcase"):
        key = f"{case.get('classname')}::{case.get('name')}"
        status = "passed"
        for child in case:
            if child.tag in ("failure", "error"):
                status = "failed" if child.tag == "failure" else "error"
                break
            if child.tag == "skipped":
                message = (child.get("message") or "").lower()
                status = "xfailed" if child.get("type") == "pytest.xfail" or message.startswith("expected") else "skipped"
                break
        if status == "passed" and "xpass" in (case.get("name") or "").lower():
            status = "xpassed"
        out[key] = status
    return out


def ledger(baseline: Path, mode: Path, name: str) -> str:
    base, off = outcomes(baseline), outcomes(mode)
    masked = sorted(k for k, s in off.items() if s in ("failed", "error") and base.get(k) == "passed")
    route_wrong = sorted(k for k, s in off.items() if s == "passed" and base.get(k) in ("failed", "error", "xfailed"))
    lines = [f"## routes-off ledger: {name}", "",
             f"baseline: {sum(1 for s in base.values() if s == 'passed')} passed / {sum(1 for s in base.values() if s == 'xfailed')} xfailed; "
             f"{name} off: {sum(1 for s in off.values() if s == 'passed')} passed / {sum(1 for s in off.values() if s in ('failed', 'error'))} failed",
             "", f"### masked general-path failures ({len(masked)})"]
    lines += [f"- {k}" for k in masked] or ["- none"]
    lines += ["", f"### route answers the general path does not ({len(route_wrong)})"]
    lines += [f"- {k}" for k in route_wrong] or ["- none"]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("baseline", type=Path)
    parser.add_argument("mode", type=Path)
    parser.add_argument("--mode", dest="name", default=None)
    args = parser.parse_args(argv)
    sys.stdout.write(ledger(args.baseline, args.mode, args.name or args.mode.stem))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
