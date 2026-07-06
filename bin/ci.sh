#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -z "${PYTHON_BIN:-}" ]]; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    echo "python not found; install Python 3.12 or set PYTHON_BIN=/path/to/python" >&2
    exit 1
  fi
fi

PYTHONPATH="${repo_root}${PYTHONPATH:+:${PYTHONPATH}}"

if [[ -n "${PYGRAPHISTRY_PATH:-}" ]]; then
  PYTHONPATH="${PYGRAPHISTRY_PATH}:${PYTHONPATH}"
fi

export PYTHONPATH

if [[ "${PYGRAPHISTRY_INSTALL:-0}" == "1" ]]; then
  if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found; install it first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
  fi
  if [[ -n "${PYGRAPHISTRY_PATH:-}" ]]; then
    uv pip install --python "${PYTHON_BIN}" -e "${PYGRAPHISTRY_PATH}"
  else
    repo="${PYGRAPHISTRY_REPO:-https://github.com/graphistry/pygraphistry.git}"
    ref="${PYGRAPHISTRY_REF:-master}"
    if [[ "${repo}" == git+* ]]; then
      repo="${repo#git+}"
    fi
    tmp_dir="$(mktemp -d)"
    trap 'rm -rf "${tmp_dir}"' EXIT
    git clone --depth 1 "${repo}" "${tmp_dir}/pygraphistry"
    (
      cd "${tmp_dir}/pygraphistry"
      git fetch --depth 1 origin "${ref}"
      git checkout FETCH_HEAD
    )
    uv pip install --python "${PYTHON_BIN}" -e "${tmp_dir}/pygraphistry"
  fi
fi

"${PYTHON_BIN}" - <<'PY'
import sys
import importlib
import importlib.util

required = (
    "contains",
    "distinct",
    "endswith",
    "eq",
    "e_forward",
    "e_reverse",
    "e_undirected",
    "ge",
    "group_by",
    "gt",
    "is_in",
    "isna",
    "le",
    "limit",
    "lt",
    "n",
    "ne",
    "notna",
    "order_by",
    "rows",
    "select",
    "skip",
    "startswith",
    "unwind",
    "where_rows",
    "with_",
)

try:
    import graphistry
    import graphistry.compute as compute
except Exception as exc:
    print(f"graphistry import failed: {exc}", file=sys.stderr)
    print("Set PYGRAPHISTRY_PATH=/path/to/pygraphistry or run PYGRAPHISTRY_INSTALL=1 ./bin/ci.sh", file=sys.stderr)
    raise SystemExit(1) from exc

missing = [name for name in required if not hasattr(compute, name)]
if missing:
    version = getattr(graphistry, "__version__", "unknown")
    path = getattr(graphistry, "__file__", "unknown")
    print(
        "graphistry.compute is missing required GFQL row-pipeline symbols: "
        + ", ".join(missing),
        file=sys.stderr,
    )
    print(f"Imported graphistry {version} from {path}", file=sys.stderr)
    print(
        "Use a newer pygraphistry checkout, for example: "
        "PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_PATH=/path/to/pygraphistry ./bin/ci.sh",
        file=sys.stderr,
    )
    print(
        "Or install a specific ref with: "
        "PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_REF=master ./bin/ci.sh",
        file=sys.stderr,
    )
    raise SystemExit(1)

required_modules = (
    "graphistry.gfql.ref.enumerator",
    "graphistry.tests.test_compute",
)
missing_modules = []
for module_name in required_modules:
    try:
        importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report exact blocker class/message
        missing_modules.append(f"{module_name} ({type(exc).__name__}: {exc})")
if missing_modules:
    version = getattr(graphistry, "__version__", "unknown")
    path = getattr(graphistry, "__file__", "unknown")
    print(
        "graphistry is missing full TCK harness modules: "
        + ", ".join(missing_modules),
        file=sys.stderr,
    )
    print(f"Imported graphistry {version} from {path}", file=sys.stderr)
    print(
        "Use a newer pygraphistry checkout, for example: "
        "PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_PATH=/path/to/pygraphistry ./bin/ci.sh",
        file=sys.stderr,
    )
    print(
        "Or install a specific ref with: "
        "PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_REF=master ./bin/ci.sh",
        file=sys.stderr,
    )
    raise SystemExit(1)

try:
    from graphistry.compute.gfql.expr_parser import parse_expr

    parse_expr("1 = 1")
except Exception as exc:
    version = getattr(graphistry, "__version__", "unknown")
    path = getattr(graphistry, "__file__", "unknown")
    lark_status = (
        "installed" if importlib.util.find_spec("lark") is not None else "not installed"
    )
    print(
        "graphistry GFQL row expression parser backend is unavailable: "
        f"{exc}",
        file=sys.stderr,
    )
    print(f"Imported graphistry {version} from {path}", file=sys.stderr)
    print(f"lark parser package: {lark_status}", file=sys.stderr)
    print(
        "If using a local checkout, install pygraphistry dependencies with: "
        "PYGRAPHISTRY_INSTALL=1 PYGRAPHISTRY_PATH=/path/to/pygraphistry ./bin/ci.sh",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc

print(
    "Using graphistry "
    f"{getattr(graphistry, '__version__', 'unknown')} from "
    f"{getattr(graphistry, '__file__', 'unknown')}"
)
PY

# Fast-fail preflight: catch direct-Cypher contract drift (common sibling-target
# bump) before running the full TCK suite.
"${PYTHON_BIN}" -m pytest tests/cypher_tck/test_direct_cypher_contract_fastfail.py -xvs

"${PYTHON_BIN}" -m pytest tests/cypher_tck -xvs
"${PYTHON_BIN}" -m tests.cypher_tck.report
