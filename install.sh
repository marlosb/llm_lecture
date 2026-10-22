#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is not installed. Install uv first: https://docs.astral.sh/uv/"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Creating Python 3.12 virtual environment with uv..."
uv venv --python 3.12

echo "Installing dependencies with uv..."
PYTHON_BIN=".venv/bin/python"
CUDA_INDEX_URL="https://download.pytorch.org/whl/cu126"
BASE_PACKAGES=(fastapi uvicorn huggingface_hub 'transformers>=4.57.3,<5' safetensors tiktoken)
TORCH_PACKAGE='torch==2.9.1'
TORCH_CUDA_PACKAGE='torch==2.9.1+cu126'

if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then
  echo "NVIDIA GPU detected. Installing PyTorch 2.9.1 (cu126)..."
  uv pip install --python "$PYTHON_BIN" --extra-index-url "$CUDA_INDEX_URL" "${BASE_PACKAGES[@]}" "$TORCH_CUDA_PACKAGE"
else
  echo "No NVIDIA GPU detected. Installing default PyTorch build..."
  uv pip install --python "$PYTHON_BIN" "${BASE_PACKAGES[@]}" "$TORCH_PACKAGE"
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Running Python installer (install.py)..."
python install.py --skip-deps

cat <<'EOF'

Installation completed.
Before running the app, create/update secrets.txt in the project root with this schema:

# Azure OpenAI chat model (GPT-5-nano)
AZURE_OPENAI_CHAT_ENDPOINT=
AZURE_OPENAI_CHAT_API_KEY=
AZURE_OPENAI_CHAT_DEPLOYMENT=
AZURE_OPENAI_CHAT_MODEL=
AZURE_OPENAI_CHAT_API_VERSION=2025-01-01-preview

# Azure AI reasoning model (DeepSeek-R1-0528)
AZURE_OPENAI_REASONING_ENDPOINT=
AZURE_OPENAI_REASONING_API_KEY=
AZURE_OPENAI_REASONING_DEPLOYMENT=
AZURE_OPENAI_REASONING_MODEL=DeepSeek-R1-0528
AZURE_OPENAI_REASONING_API_VERSION=2024-05-01-preview
EOF
