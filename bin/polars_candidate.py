#!/usr/bin/env python3
"""Run candidate conformance using the selected product's route registry."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


PROBE = '''
import json
from pathlib import Path
import graphistry
from graphistry.tests.compute.gfql.routes import switch
root = Path(__import__('os').environ['PYGRAPHISTRY_PATH']).resolve()
for module in (graphistry, switch):
    if not Path(module.__file__).resolve().is_relative_to(root):
        raise RuntimeError(f"{module.__name__} imported outside selected checkout")
print(json.dumps(list(switch.ROUTES)))
'''


def run_candidate(product, mode, expected_sha=None):
    root = Path(product).resolve()
    env = {**os.environ, "TEST_POLARS": "1", "PYGRAPHISTRY_PATH": str(root),
           "PYTHON_BIN": sys.executable,
           "PYTHONPATH": str(root) + os.pathsep + os.environ.get("PYTHONPATH", "")}
    sha = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if expected_sha is not None and sha != expected_sha:
        raise ValueError(f"Candidate checkout is {sha}, expected {expected_sha}")
    routes = json.loads(subprocess.check_output([sys.executable, "-c", PROBE], env=env, text=True))
    if not routes or any(not isinstance(route, str) or not route for route in routes):
        raise ValueError("Candidate route registry must contain nonempty route names")
    env["GFQL_ROUTES_OFF"] = ",".join(routes) if mode == "all-off" else ""
    print(f"Candidate {sha}; mode={mode}; routes_off={env['GFQL_ROUTES_OFF']}", flush=True)
    return subprocess.run([str(Path(__file__).resolve().with_name("ci.sh"))], env=env,
                          cwd=Path(__file__).resolve().parents[1], check=False).returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", required=True)
    parser.add_argument("--mode", choices=("normal", "all-off"), required=True)
    parser.add_argument("--expected-sha")
    args = parser.parse_args()
    sys.exit(run_candidate(args.product, args.mode, args.expected_sha))
