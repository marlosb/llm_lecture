Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

if (-not (Test-Path ".\.venv")) {
    Write-Error ".venv not found. Run install.ps1 first."
    exit 1
}

$venvPath = (Resolve-Path ".\.venv").Path
if (-not $env:VIRTUAL_ENV -or $env:VIRTUAL_ENV -ne $venvPath) {
    Write-Host "Activating virtual environment..."
    . .\.venv\Scripts\Activate.ps1
}

Write-Host "Starting server at http://127.0.0.1:8000"
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
