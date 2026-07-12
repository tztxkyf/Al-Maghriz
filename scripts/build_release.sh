#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"
DIST_DIR="${PROJECT_ROOT}/dist"

mkdir -p "${BUILD_DIR}"
mkdir -p "${DIST_DIR}"

cd "${BUILD_DIR}"
cmake -DCMAKE_BUILD_TYPE=Release "${PROJECT_ROOT}"
cmake --build . --config Release --parallel "$(nproc)"

# Copy the resulting shared library into dist/ and strip debug symbols.
cp "${BUILD_DIR}/libal_maghriz.so" "${DIST_DIR}/libal_maghriz.so"
strip --strip-unneeded "${DIST_DIR}/libal_maghriz.so"

echo "Built release artifact: ${DIST_DIR}/libal_maghriz.so"
ls -lh "${DIST_DIR}/libal_maghriz.so"
