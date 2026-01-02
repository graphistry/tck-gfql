#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="${repo_root}${PYTHONPATH:+:${PYTHONPATH}}"

if [[ -n "${PYGRAPHISTRY_PATH:-}" ]]; then
  PYTHONPATH="${PYGRAPHISTRY_PATH}:${PYTHONPATH}"
fi

export PYTHONPATH

if [[ "${PYGRAPHISTRY_INSTALL:-0}" == "1" ]]; then
  if [[ -n "${PYGRAPHISTRY_PATH:-}" ]]; then
    python -m pip install -e "${PYGRAPHISTRY_PATH}"
  else
    repo="${PYGRAPHISTRY_REPO:-https://github.com/graphistry/pygraphistry.git}"
    ref="${PYGRAPHISTRY_REF:-master}"
    if [[ "${repo}" == git+* ]]; then
      repo_url="${repo}"
    else
      repo_url="git+${repo}"
    fi
    python -m pip install "${repo_url}@${ref}"
  fi
fi

pytest tests/cypher_tck -xvs
python -m tests.cypher_tck.report
