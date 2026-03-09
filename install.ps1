Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is not installed. Install uv first: https://docs.astral.sh/uv/"
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "Creating virtual environment with uv..."
uv venv

Write-Host "Installing dependencies with uv..."
uv pip install --python .venv\Scripts\python.exe fastapi uvicorn huggingface_hub transformers torch

Write-Host "Activating virtual environment..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Running Python installer (install.py)..."
python .\install.py

Write-Host ""
Write-Host "Installation completed."
Write-Host "Before running the app, create/update secrets.txt in the project root with this schema:"
Write-Host ""
Write-Host "# Azure OpenAI configuration"
Write-Host "AZURE_OPENAI_CHAT_ENDPOINT="
Write-Host "AZURE_OPENAI_CHAT_API_KEY="
Write-Host "AZURE_OPENAI_CHAT_DEPLOYMENT="
Write-Host "AZURE_OPENAI_CHAT_API_VERSION=2025-01-01-preview"
Write-Host ""
Write-Host "# Azure OpenAI reasoning model (o3-mini)"
Write-Host "AZURE_OPENAI_REASONING_ENDPOINT="
Write-Host "AZURE_OPENAI_REASONING_API_KEY="
Write-Host "AZURE_OPENAI_REASONING_DEPLOYMENT="
Write-Host "AZURE_OPENAI_REASONING_API_VERSION=2025-01-01-preview"
