Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
. "$PSScriptRoot\docker-common.ps1"

Write-Host "Building application image..."
Invoke-DockerCompose -Arguments @("build", "app")

Write-Host "Downloading the selected model to the Docker volume..."
Invoke-DockerCompose -Arguments @(
    "run", "--rm", "--no-deps", "--pull", "never", "model-download"
)

Write-Host "Installation completed."
Write-Host "Create a host-only environment file using secrets.env.example before running run.ps1."
Write-Host "Set LLM_ENV_FILE if it is not at secrets.txt. Do not mount it inside the container."
