#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -d ".venv" ]]; then
  echo "Error: .venv not found. Run install.sh first."
  exit 1
fi

if [[ "${VIRTUAL_ENV:-}" != "$SCRIPT_DIR/.venv" ]]; then
  echo "Activating virtual environment..."
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

echo "Starting server at http://127.0.0.1:8000"
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
