Param(
    [switch]$Rebuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot

if ($Rebuild) {
    docker build -t sms-lock:latest .
}

if (-not (Test-Path ".\logs")) {
    New-Item -ItemType Directory -Path ".\logs" | Out-Null
}

docker run --rm `
  -v "${PWD}\config.yaml:/app/config.yaml:ro" `
  -v "${PWD}\logs:/app/logs" `
  -v "${PWD}\registration_results.csv:/app/registration_results.csv" `
  sms-lock:latest python lock_accounts.py

Pop-Location
