"""Pytest hooks for the Cypher TCK runner.

Surfaces the native-polars-engine coverage that the runner tolerates: under
``TEST_POLARS=1`` a scenario whose polars execution raises ``NotImplementedError``
is an HONEST partial-coverage decline (NO-CHEATING: no pandas fallback), not a
conformance failure. Those declines are collected by the runner; this hook reports
the count at session end so polars coverage is transparent rather than silent.
"""
from __future__ import annotations

import os
import sys

import pytest


@pytest.fixture(autouse=True, scope="session")
def _gfql_routes_off():
    """``GFQL_ROUTES_OFF=<route,...>`` replays the whole TCK with the named pygraphistry hot
    paths declined, so conformance is measured on the general path the routes normally mask
    (``bin/routes-off.sh``). The switch is pygraphistry's own test-side route switch; a run
    that cannot apply it must fail rather than report a ledger for the wrong configuration."""
    raw = os.environ.get("GFQL_ROUTES_OFF", "")
    routes = [r.strip() for r in raw.split(",") if r.strip()]
    if not routes:
        yield
        return
    try:
        from graphistry.tests.compute.gfql.routes.switch import routes_off
    except ImportError as exc:  # pragma: no cover - configuration error
        raise RuntimeError(
            "GFQL_ROUTES_OFF is set but the pygraphistry checkout on PYTHONPATH has no "
            "graphistry.tests.compute.gfql.routes.switch (needs pygraphistry >= the "
            "chain-specializations layout)"
        ) from exc
    with routes_off(routes):
        yield


def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:  # noqa: ANN001
    # The runner module may be imported under a bare name (no package __init__),
    # so locate whichever loaded module instance actually carries the collector
    # rather than importing by a guessed dotted path (which yields a fresh, empty
    # copy).
    for module in list(sys.modules.values()):
        declined = getattr(module, "_POLARS_NOT_IMPLEMENTED", None)
        if declined is None or not getattr(module, "_TEST_POLARS", False):
            continue
        if declined:
            terminalreporter.write_sep(
                "-",
                f"polars engine: {len(declined)} scenarios honestly declined "
                f"(NotImplementedError — NO-CHEATING, no pandas fallback)",
            )
        return
