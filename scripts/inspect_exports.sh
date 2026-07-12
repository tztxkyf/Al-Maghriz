#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SO_PATH="${PROJECT_ROOT}/dist/libal_maghriz.so"

if [[ ! -f "${SO_PATH}" ]]; then
    echo "error: ${SO_PATH} not found. Run scripts/build_release.sh first."
    exit 1
fi

echo "Dynamic symbols defined by ${SO_PATH}:"
nm -D --defined-only "${SO_PATH}"

echo ""
echo "Shared library dependencies:"
ldd "${SO_PATH}"
