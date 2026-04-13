#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
STAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE="${DIST_DIR}/lucy-build-${STAMP}.tar.gz"

mkdir -p "${DIST_DIR}"

tar -czf "${ARCHIVE}" \
  -C "${ROOT_DIR}" \
  README.md \
  backend \
  scripts \
  tauri

echo "${ARCHIVE}"
