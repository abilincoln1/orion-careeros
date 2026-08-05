<#
.SYNOPSIS
    Sets BACKEND_PORT=8010 in .env, to avoid a port collision with another
    project (e.g. NDIP) on the same machine.

.DESCRIPTION
    Safe to re-run. If BACKEND_PORT already exists in .env, its value is
    updated in place. If it doesn't exist yet, the line is appended.
    Leaves every other line in .env untouched.

.EXAMPLE
    cd "C:\Projects\Career OS"
    .\scripts\set-backend-port.ps1
#>

[CmdletBinding()]
param(
    [int]$Port = 8010
)

$ErrorActionPreference = "Stop"

$envPath = Join-Path (Get-Location) ".env"

if (-not (Test-Path $envPath)) {
    Write-Host "FAIL: .env not found at $envPath -- run this from the repo root (C:\Projects\Career OS)." -ForegroundColor Red
    exit 1
}

$lines = Get-Content $envPath
$pattern = '^\s*BACKEND_PORT\s*='
$found = $false

$newLines = foreach ($line in $lines) {
    if ($line -match $pattern) {
        $found = $true
        "BACKEND_PORT=$Port"
    } else {
        $line
    }
}

if (-not $found) {
    $newLines += "BACKEND_PORT=$Port"
}

Set-Content -Path $envPath -Value $newLines

Write-Host "OK: BACKEND_PORT set to $Port in $envPath" -ForegroundColor Green
Write-Host ""
Write-Host "Next: re-run .\scripts\bootstrap.ps1 -- it will pick up the new port automatically." -ForegroundColor Cyan
Write-Host "The backend will then be reachable at http://localhost:$Port"
