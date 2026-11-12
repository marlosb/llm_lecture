#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/docker-common.sh"

echo "Stopping application container..."
"${COMPOSE[@]}" stop app
echo "Application stopped."
