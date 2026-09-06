#!/usr/bin/env bash
# Per-route conformance ledger (non-blocking): run the TCK once as baseline and once per
# routes-off mode, then diff outcomes (tests/cypher_tck/route_ledger.py). Same environment
# contract as bin/ci.sh (PYGRAPHISTRY_PATH / PYTHON_BIN). Always exits 0.
set -uo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python || command -v python3)}"
PYTHONPATH="${repo_root}${PYTHONPATH:+:${PYTHONPATH}}"
if [[ -n "${PYGRAPHISTRY_PATH:-}" ]]; then PYTHONPATH="${PYGRAPHISTRY_PATH}:${PYTHONPATH}"; fi
export PYTHONPATH
MODES="${MODES:-native-fast polars-seeded polars-plain index-hop indexed-kernel cypher-fast all-off}"
OUT="${OUT:-build/routes-off}"
mkdir -p "${OUT}"
run() {  # $1 = mode name, $2 = GFQL_ROUTES_OFF value ("" for baseline)
  GFQL_ROUTES_OFF="$2" "${PYTHON_BIN}" -m pytest tests/cypher_tck -q -p no:cacheprovider \
    --junitxml="${OUT}/$1.xml" > "${OUT}/$1.log" 2>&1
  echo "$1: $(tail -1 "${OUT}/$1.log")"
}
[[ -f "${OUT}/baseline.xml" && "${REUSE_BASELINE:-0}" == "1" ]] || run baseline ""
for mode in ${MODES}; do
  if [[ "${mode}" == all-off ]]; then routes=native-fast,polars-seeded,polars-plain,index-hop,indexed-kernel,cypher-fast; else routes="${mode}"; fi
  run "${mode}" "${routes}"
  "${PYTHON_BIN}" -m tests.cypher_tck.route_ledger "${OUT}/baseline.xml" "${OUT}/${mode}.xml" --mode "${mode}" | tee "${OUT}/${mode}.md"
done
exit 0
