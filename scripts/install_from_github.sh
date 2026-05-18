#!/usr/bin/env bash
set -euo pipefail

REPO="${LUCY_GITHUB_REPO:-happygolucky19922-star/gauntlet}"
REF="${LUCY_GITHUB_REF:-main}"
INSTALL_ROOT="${LUCY_INSTALL_ROOT:-${HOME}/.local/share/lucy}"
SOURCE_DIR="${INSTALL_ROOT}/source"
REPO_URL="https://github.com/${REPO}.git"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required to download Lucy from GitHub." >&2
  exit 1
fi

mkdir -p "${INSTALL_ROOT}"

if [[ -d "${SOURCE_DIR}/.git" ]]; then
  git -C "${SOURCE_DIR}" fetch --depth 1 origin "${REF}"
  git -C "${SOURCE_DIR}" checkout --force FETCH_HEAD
else
  rm -rf "${SOURCE_DIR}"
  git clone --depth 1 --branch "${REF}" "${REPO_URL}" "${SOURCE_DIR}"
fi

PROJECT_DIR="${SOURCE_DIR}" bash "${SOURCE_DIR}/scripts/install_desktop.sh"

echo "Lucy downloaded from https://github.com/${REPO} (${REF})."
echo "Source path: ${SOURCE_DIR}"
echo "Start the backend with:"
echo "  ${SOURCE_DIR}/scripts/run_backend.sh"

if [[ "${LUCY_START_AFTER_INSTALL:-0}" == "1" ]]; then
  exec "${SOURCE_DIR}/scripts/run_backend.sh"
fi
