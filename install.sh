#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is not installed. Install uv first: https://docs.astral.sh/uv/"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Creating virtual environment with uv..."
uv venv

echo "Installing dependencies with uv..."
uv pip install --python .venv/bin/python fastapi uvicorn huggingface_hub transformers torch

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Running Python installer (install.py)..."
python install.py

cat <<'EOF'

Installation completed.
Before running the app, create/update secrets.txt in the project root with this schema:

# Azure OpenAI configuration
AZURE_OPENAI_CHAT_ENDPOINT=
AZURE_OPENAI_CHAT_API_KEY=
AZURE_OPENAI_CHAT_DEPLOYMENT=
AZURE_OPENAI_CHAT_API_VERSION=2025-01-01-preview

# Azure OpenAI reasoning model (o3-mini)
AZURE_OPENAI_REASONING_ENDPOINT=
AZURE_OPENAI_REASONING_API_KEY=
AZURE_OPENAI_REASONING_DEPLOYMENT=
AZURE_OPENAI_REASONING_API_VERSION=2025-01-01-preview
EOF
