#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/docker-common.sh"

echo "Building application image..."
"${COMPOSE[@]}" build app

echo "Downloading the selected model to the Docker volume..."
"${COMPOSE[@]}" run --rm --no-deps --pull never model-download

echo "Installation completed."
echo "Create a host-only environment file using secrets.env.example before running run.sh."
echo "Set LLM_ENV_FILE if it is not at secrets.txt. Do not mount it inside the container."
