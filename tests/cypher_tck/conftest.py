"""Pytest hooks for the Cypher TCK runner.

Surfaces the native-polars-engine coverage that the runner tolerates: under
``TEST_POLARS=1`` a scenario whose polars execution raises ``NotImplementedError``
is an HONEST partial-coverage decline (NO-CHEATING: no pandas fallback), not a
conformance failure. Those declines are collected by the runner; this hook reports
the count at session end so polars coverage is transparent rather than silent.
"""
from __future__ import annotations

import sys


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
