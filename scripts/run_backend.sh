#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
VENV_DIR="${LUCY_VENV_DIR:-${BACKEND_DIR}/.venv}"
HOST="${LUCY_HOST:-127.0.0.1}"
PORT="${LUCY_PORT:-8000}"
PYTHON_BIN="${PYTHON:-python3}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python executable not found: ${PYTHON_BIN}" >&2
  exit 1
fi

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "${BACKEND_DIR}/requirements.txt"

if [[ "${LUCY_INSTALL_LLAMA:-0}" == "1" ]]; then
  python -m pip install -r "${BACKEND_DIR}/requirements-llama.txt"
fi

if [[ "${LUCY_INSTALL_VLLM:-0}" == "1" ]]; then
  python -m pip install -r "${BACKEND_DIR}/requirements-vllm.txt"
fi

if [[ "${LUCY_SKIP_SERVER:-0}" == "1" ]]; then
  echo "Lucy backend environment is ready at ${VENV_DIR}"
  exit 0
fi

cd "${BACKEND_DIR}"
exec uvicorn app.main:app --host "${HOST}" --port "${PORT}"
