Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
. "$PSScriptRoot\docker-common.ps1"

$environmentFile = if ($env:LLM_ENV_FILE) { $env:LLM_ENV_FILE } else { "secrets.txt" }
if (-not (Test-Path -LiteralPath $environmentFile -PathType Leaf)) {
    throw "Host environment file not found. Copy secrets.env.example and set LLM_ENV_FILE."
}

Write-Host "Starting application container..."
Invoke-DockerCompose -Arguments @(
    "up", "--detach", "--no-build", "--pull", "never", "--force-recreate",
    "--wait", "--wait-timeout", "180", "app"
)
Invoke-DockerCompose -Arguments @(
    "exec", "-T", "app", "python", "-m", "backend.warmup"
)
$bindAddress = if ($env:LLM_BIND_ADDRESS) { $env:LLM_BIND_ADDRESS } else { "127.0.0.1" }
$port = if ($env:LLM_PORT) { $env:LLM_PORT } else { "8000" }
Write-Host "Application ready at http://${bindAddress}:$port"
