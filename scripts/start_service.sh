#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "Missing virtualenv python at ${VENV_PYTHON}" >&2
  echo "Create/install dependencies first (example: uv sync --extra dev)." >&2
  exit 1
fi

cd "${PROJECT_ROOT}"
exec "${VENV_PYTHON}" -m uvicorn markitdown_server.main:app --host "${HOST}" --port "${PORT}" --app-dir src
