<#
.SYNOPSIS
    Sets BACKEND_PORT, FRONTEND_PORT, and/or POSTGRES_PORT in .env, to avoid
    port collisions with another project (e.g. NDIP) on the same machine.

.DESCRIPTION
    Safe to re-run. For each port you pass, if the variable already exists
    in .env its value is updated in place; if it doesn't exist yet, the
    line is appended. Every other line in .env is left untouched. Only
    pass the ports you actually need to change -- omit the rest to leave
    them at their current value.

.EXAMPLE
    cd "C:\Projects\Career OS"
    .\scripts\set-ports.ps1 -BackendPort 8010 -PostgresPort 5433
#>

[CmdletBinding()]
param(
    [int]$BackendPort,
    [int]$FrontendPort,
    [int]$PostgresPort
)

$ErrorActionPreference = "Stop"

$envPath = Join-Path (Get-Location) ".env"

if (-not (Test-Path $envPath)) {
    Write-Host "FAIL: .env not found at $envPath -- run this from the repo root (C:\Projects\Career OS)." -ForegroundColor Red
    exit 1
}

$targets = @{}
if ($PSBoundParameters.ContainsKey("BackendPort"))  { $targets["BACKEND_PORT"]  = $BackendPort }
if ($PSBoundParameters.ContainsKey("FrontendPort")) { $targets["FRONTEND_PORT"] = $FrontendPort }
if ($PSBoundParameters.ContainsKey("PostgresPort")) { $targets["POSTGRES_PORT"] = $PostgresPort }

if ($targets.Count -eq 0) {
    Write-Host "FAIL: pass at least one of -BackendPort, -FrontendPort, -PostgresPort." -ForegroundColor Red
    exit 1
}

$lines = Get-Content $envPath
$foundKeys = @{}

$newLines = foreach ($line in $lines) {
    $matched = $false
    foreach ($key in $targets.Keys) {
        if ($line -match "^\s*$key\s*=") {
            $foundKeys[$key] = $true
            "$key=$($targets[$key])"
            $matched = $true
            break
        }
    }
    if (-not $matched) { $line }
}

foreach ($key in $targets.Keys) {
    if (-not $foundKeys.ContainsKey($key)) {
        $newLines += "$key=$($targets[$key])"
    }
}

Set-Content -Path $envPath -Value $newLines

foreach ($key in $targets.Keys) {
    Write-Host "OK: $key set to $($targets[$key]) in $envPath" -ForegroundColor Green
}
Write-Host ""
Write-Host "Next: re-run .\scripts\bootstrap.ps1 -- it will pick up the new port(s) automatically." -ForegroundColor Cyan
