#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/docker-common.sh"

if [[ ! -f "${LLM_ENV_FILE:-secrets.txt}" ]]; then
  echo "Error: host environment file not found. Copy secrets.env.example and set LLM_ENV_FILE."
  exit 1
fi

if [[ "$LLM_BIND_ADDRESS" != 127.0.0.1 && "$(uname -s)" == Linux ]]; then
  if ! systemctl is-active --quiet llm-lecture-firewall.service \
    || ! grep -Fxq "HOST_IP=$LLM_BIND_ADDRESS" /etc/llm-lecture-firewall.conf \
    || ! grep -Fxq "PORT=$LLM_PORT" /etc/llm-lecture-firewall.conf; then
    echo "Error: configure the Docker firewall before enabling LAN access."
    echo "Run sudo bash docker-firewall.sh HOST_IP TRUSTED_SUBNET PORT."
    exit 1
  fi
fi

echo "Starting application container..."
"${COMPOSE[@]}" up --detach --no-build --pull never --force-recreate --wait --wait-timeout 180 app
"${COMPOSE[@]}" exec -T app python -m backend.warmup
echo "Application ready at http://${LLM_BIND_ADDRESS:-127.0.0.1}:${LLM_PORT:-8000}"
