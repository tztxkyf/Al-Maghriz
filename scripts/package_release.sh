#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${PROJECT_ROOT}/dist"
VERSION="1.0.0"
PKG_DIR="${DIST_DIR}/al_maghriz_release-${VERSION}"

echo "Packaging release ${VERSION}..."

rm -rf "${PKG_DIR}"
mkdir -p "${PKG_DIR}"/{lib,include,python,examples,docs,certificate}

cp "${DIST_DIR}/libal_maghriz.so" "${PKG_DIR}/lib/"
cp "${PROJECT_ROOT}/include/al_maghriz_api.h" "${PKG_DIR}/include/"
cp "${PROJECT_ROOT}/python/al_maghriz.py" "${PKG_DIR}/python/"
cp "${PROJECT_ROOT}/examples/example_config.json" "${PKG_DIR}/examples/"

# Only copy the CSV if it exists (examples/*.csv is gitignored).
if [[ -f "${PROJECT_ROOT}/examples/eth_hourly.csv" ]]; then
    cp "${PROJECT_ROOT}/examples/eth_hourly.csv" "${PKG_DIR}/examples/"
fi

cp "${PROJECT_ROOT}/docs/END_USER_GUIDE.md" "${PKG_DIR}/docs/"
cp "${PROJECT_ROOT}/docs/API_REFERENCE.md" "${PKG_DIR}/docs/"
cp "${PROJECT_ROOT}/docs/BUILD_GUIDE.md" "${PKG_DIR}/docs/"

cd "${DIST_DIR}"
find "al_maghriz_release-${VERSION}" -type f -exec sha256sum {} \; > SHA256SUMS

echo "Release package created: ${PKG_DIR}"
cat SHA256SUMS
