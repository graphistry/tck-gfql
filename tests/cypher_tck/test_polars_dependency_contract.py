"""An explicitly requested engine cannot silently disappear from validation."""
import pytest

from tests.cypher_tck import conftest


def test_requested_polars_import_failure_is_fatal(monkeypatch):
    monkeypatch.setenv("TEST_POLARS", "1")

    def unavailable(name):
        assert name == "polars"
        raise ImportError("broken installation")

    monkeypatch.setattr(conftest.importlib, "import_module", unavailable)
    with pytest.raises(pytest.UsageError, match="TEST_POLARS=1"):
        conftest.pytest_configure(None)


def test_unrequested_polars_does_not_require_dependency(monkeypatch):
    monkeypatch.setenv("TEST_POLARS", "0")

    def unexpected(name):
        raise AssertionError("should not import an unrequested engine")

    monkeypatch.setattr(conftest.importlib, "import_module", unexpected)
    conftest.pytest_configure(None)
