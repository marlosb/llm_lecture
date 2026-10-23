#!/usr/bin/env bash

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: Docker is not installed."
  exit 1
fi
docker compose version >/dev/null
docker info >/dev/null

export LLM_MODEL_ID="${LLM_MODEL_ID-marlosb/ArthurFriedenreich}"
export LLM_ENV_FILE="${LLM_ENV_FILE:-$SCRIPT_DIR/secrets.txt}"
export LLM_BIND_ADDRESS="${LLM_BIND_ADDRESS:-127.0.0.1}"
export LLM_PORT="${LLM_PORT:-8000}"

COMPOSE=(docker compose --project-name llm-lecture --file "$SCRIPT_DIR/compose.yaml")
GPU_MODE="${LLM_USE_GPU:-auto}"
case "$GPU_MODE" in
  auto)
    if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then
      GPU_MODE=1
    else
      GPU_MODE=0
    fi
    ;;
  0|1) ;;
  *)
    echo "Error: LLM_USE_GPU must be auto, 0, or 1."
    exit 1
    ;;
esac

if [[ "$GPU_MODE" == 1 ]]; then
  COMPOSE+=(--file "$SCRIPT_DIR/compose.gpu.yaml")
  echo "Using CUDA 12.6 containers. NVIDIA Container Toolkit must be configured."
else
  echo "Using CPU containers."
fi
