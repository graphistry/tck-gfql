#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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
    uv pip install --python "$(command -v python)" -e "${PYGRAPHISTRY_PATH}"
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
    uv pip install --python "$(command -v python)" -e "${tmp_dir}/pygraphistry"
  fi
fi

pytest tests/cypher_tck -xvs
python -m tests.cypher_tck.report
