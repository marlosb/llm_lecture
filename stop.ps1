Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
. "$PSScriptRoot\docker-common.ps1"

Write-Host "Stopping application container..."
Invoke-DockerCompose -Arguments @("stop", "app")
Write-Host "Application stopped."
