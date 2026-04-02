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

Write-Host "Starting server at http://0.0.0.0:8000"
$warmupJob = Start-Job -ScriptBlock {
    $uri = "http://127.0.0.1:8000/api/text-complete"
    $body = '{"text":"Warmup","max_new_tokens":1}'
    for ($attempt = 1; $attempt -le 60; $attempt++) {
        try {
            Invoke-RestMethod -Method Post -Uri $uri -ContentType "application/json" -Body $body | Out-Null
            Write-Output "Model warm-up request completed."
            return
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    Write-Output "Warning: model warm-up request did not complete in time."
}

python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

Receive-Job -Job $warmupJob -Keep | Out-Host
Remove-Job -Job $warmupJob -Force
