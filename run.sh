#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/docker-common.sh"

if [[ ! -f "${LLM_ENV_FILE:-secrets.txt}" ]]; then
  echo "Error: host environment file not found. Copy secrets.env.example and set LLM_ENV_FILE."
  exit 1
fi

echo "Starting application container..."
"${COMPOSE[@]}" up --detach --no-build --pull never --force-recreate --wait --wait-timeout 180 app
"${COMPOSE[@]}" exec -T app python -m backend.warmup
echo "Application ready at http://${LLM_BIND_ADDRESS:-0.0.0.0}:${LLM_PORT:-8000}"
