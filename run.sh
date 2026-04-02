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

echo "Starting server at http://0.0.0.0:8000"
(
  for attempt in {1..60}; do
    if curl -sS -X POST "http://127.0.0.1:8000/api/text-complete" \
      -H "Content-Type: application/json" \
      -d '{"text":"Warmup","max_new_tokens":1}' >/dev/null; then
      echo "Model warm-up request completed."
      exit 0
    fi
    sleep 1
  done
  echo "Warning: model warm-up request did not complete in time."
) &

python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
