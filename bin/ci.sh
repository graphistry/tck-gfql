#!/usr/bin/env bash
set -euo pipefail

pytest tests/cypher_tck -xvs
