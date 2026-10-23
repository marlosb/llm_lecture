Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is not installed."
}
docker compose version *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose is unavailable."
}
docker info > $null
if ($LASTEXITCODE -ne 0) {
    throw "The Docker engine is unavailable or this account cannot access it."
}

if (-not (Test-Path Env:LLM_MODEL_ID)) {
    $env:LLM_MODEL_ID = "marlosb/ArthurFriedenreich"
}
if (-not $env:LLM_ENV_FILE) {
    $env:LLM_ENV_FILE = Join-Path $PSScriptRoot "secrets.txt"
}
if (-not $env:LLM_BIND_ADDRESS) {
    $env:LLM_BIND_ADDRESS = "127.0.0.1"
}
if (-not $env:LLM_PORT) {
    $env:LLM_PORT = "8000"
}

$script:ComposeArguments = @(
    "compose", "--project-name", "llm-lecture",
    "--file", (Join-Path $PSScriptRoot "compose.yaml")
)
$gpuMode = if ($env:LLM_USE_GPU) { $env:LLM_USE_GPU } else { "auto" }
if ($gpuMode -notin @("auto", "0", "1")) {
    throw "LLM_USE_GPU must be auto, 0, or 1."
}
if ($gpuMode -eq "auto") {
    $gpuMode = "0"
    $nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($nvidiaSmi) {
        & $nvidiaSmi.Source -L *> $null
        if ($LASTEXITCODE -eq 0) {
            $gpuMode = "1"
        }
    }
}
if ($gpuMode -eq "1") {
    $script:ComposeArguments += @(
        "--file", (Join-Path $PSScriptRoot "compose.gpu.yaml")
    )
    Write-Host "Using CUDA 12.6 containers. NVIDIA Container Toolkit must be configured."
}
else {
    Write-Host "Using CPU containers."
}

function Invoke-DockerCompose {
    param([string[]]$Arguments)

    & docker @script:ComposeArguments @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose failed (exit code $LASTEXITCODE)."
    }
}
