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
$pythonPath = ".venv\Scripts\python.exe"
$basePackages = @("fastapi", "uvicorn", "huggingface_hub", "transformers")
$cudaIndexUrl = "https://download.pytorch.org/whl/cu121"
$hasNvidiaGpu = $false
$nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidiaSmi) {
    & $nvidiaSmi.Source -L *> $null
    if ($LASTEXITCODE -eq 0) {
        $hasNvidiaGpu = $true
    }
}

if ($hasNvidiaGpu) {
    Write-Host "NVIDIA GPU detected. Installing CUDA-enabled PyTorch (cu121)..."
    uv pip install --python $pythonPath --extra-index-url $cudaIndexUrl @basePackages torch
}
else {
    Write-Host "No NVIDIA GPU detected. Installing default PyTorch build..."
    uv pip install --python $pythonPath @basePackages torch
}

Write-Host "Activating virtual environment..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Running Python installer (install.py)..."
python .\install.py --skip-deps

Write-Host ""
Write-Host "Installation completed."
Write-Host "Before running the app, create/update secrets.txt in the project root with this schema:"
Write-Host ""
Write-Host "# Azure OpenAI chat model (GPT-5-nano)"
Write-Host "AZURE_OPENAI_CHAT_ENDPOINT="
Write-Host "AZURE_OPENAI_CHAT_API_KEY="
Write-Host "AZURE_OPENAI_CHAT_DEPLOYMENT="
Write-Host "AZURE_OPENAI_CHAT_MODEL="
Write-Host "AZURE_OPENAI_CHAT_API_VERSION=2025-01-01-preview"
Write-Host ""
Write-Host "# Azure AI reasoning model (DeepSeek-R1-0528)"
Write-Host "AZURE_OPENAI_REASONING_ENDPOINT="
Write-Host "AZURE_OPENAI_REASONING_API_KEY="
Write-Host "AZURE_OPENAI_REASONING_DEPLOYMENT="
Write-Host "AZURE_OPENAI_REASONING_MODEL=DeepSeek-R1-0528"
Write-Host "AZURE_OPENAI_REASONING_API_VERSION=2024-05-01-preview"
