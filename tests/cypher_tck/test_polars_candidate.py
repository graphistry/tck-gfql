"""Candidate route discovery must track the selected product and preserve failures."""
import importlib.util
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location("polars_candidate", Path(__file__).resolve().parents[2] / "bin/polars_candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


@pytest.mark.parametrize("mode", ["normal", "all-off"])
@pytest.mark.parametrize("exit_code", [0, 7])
def test_candidate_uses_product_registry_and_propagates_status(monkeypatch, tmp_path, mode, exit_code):
    discovered = ["existing-route", "future-specialization"]
    calls = []

    def output(argv, **kwargs):
        calls.append(argv)
        if argv[0] == "git":
            return "a" * 40 + "\n"
        assert kwargs["env"]["PYGRAPHISTRY_PATH"] == str(tmp_path)
        return json.dumps(discovered)

    def run(argv, **kwargs):
        env = kwargs["env"]
        assert env["TEST_POLARS"] == "1"
        assert env["GFQL_ROUTES_OFF"] == (",".join(discovered) if mode == "all-off" else "")
        return SimpleNamespace(returncode=exit_code)

    monkeypatch.setenv("GFQL_ROUTES_OFF", "stale-route")
    monkeypatch.setattr(candidate.subprocess, "check_output", output)
    monkeypatch.setattr(candidate.subprocess, "run", run)
    assert candidate.run_candidate(tmp_path, mode, "a" * 40) == exit_code
    assert len(calls) == 2


def test_wrong_candidate_sha_stops_before_route_discovery(monkeypatch, tmp_path):
    monkeypatch.setattr(candidate.subprocess, "check_output", lambda *a, **k: "wrong\n")
    with pytest.raises(ValueError, match="expected"):
        candidate.run_candidate(tmp_path, "all-off", "expected")


def test_route_probe_failure_is_fatal(monkeypatch, tmp_path):
    def output(argv, **kwargs):
        if argv[0] == "git":
            return "a" * 40
        raise subprocess.CalledProcessError(3, argv)
    monkeypatch.setattr(candidate.subprocess, "check_output", output)
    with pytest.raises(subprocess.CalledProcessError):
        candidate.run_candidate(tmp_path, "all-off")


@pytest.mark.parametrize("wrong_checkout", [False, True])
def test_probe_checks_product_and_registry_import_paths(tmp_path, wrong_checkout):
    import os
    import sys
    product = tmp_path / "product"
    imported = tmp_path / "other" if wrong_checkout else product
    package = imported / "graphistry/tests/compute/gfql/routes"
    package.mkdir(parents=True)
    current = package
    while current != imported:
        (current / "__init__.py").write_text("")
        current = current.parent
    (package / "switch.py").write_text("ROUTES = ('new-route',)\n")
    env = {**os.environ, "PYGRAPHISTRY_PATH": str(product), "PYTHONPATH": str(imported)}
    result = subprocess.run([sys.executable, "-c", candidate.PROBE], env=env, cwd=tmp_path,
                            text=True, capture_output=True)
    if wrong_checkout:
        assert result.returncode != 0
        assert "outside selected checkout" in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == ["new-route"]
