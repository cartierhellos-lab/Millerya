Param(
    [switch]$Rebuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot

if ($Rebuild) {
    docker build -t sms-register:latest .
}

if (-not (Test-Path ".\logs")) {
    New-Item -ItemType Directory -Path ".\logs" | Out-Null
}

docker run --rm `
  -v "${PWD}\config.yaml:/app/config.yaml:ro" `
  -v "${PWD}\phone_numbers.csv:/app/phone_numbers.csv:ro" `
  -v "${PWD}\logs:/app/logs" `
  -v "${PWD}\registration_results.csv:/app/registration_results.csv" `
  sms-register:latest

Pop-Location
