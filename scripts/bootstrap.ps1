<#
.SYNOPSIS
    One-command developer onboarding for the CareerOS product (ORION Platform).

.DESCRIPTION
    Verifies the local machine has what it needs, creates a local .env if
    one doesn't exist yet, builds and starts the Docker Compose stack,
    confirms migrations applied and the backend is actually reachable, and
    prints next steps. Safe to re-run: every step is idempotent.

    Written for Windows PowerShell 5.1+ and PowerShell 7+. Does not require
    admin rights (beyond whatever Docker Desktop itself requires).

.NOTES
    This repository is designed to be independent of where it's cloned or
    what else is running on the machine -- see
    docs/REPOSITORY_INDEPENDENCE_REPORT.md. This script therefore never
    assumes a fixed drive letter or parent folder name: it always resolves
    paths relative to its own location.

.EXAMPLE
    .\scripts\bootstrap.ps1
#>

[CmdletBinding()]
param(
    # Skip the (slow) `docker compose build` step if images already exist.
    [switch]$SkipBuild,

    # How long to wait for the backend health endpoint before giving up.
    [int]$HealthTimeoutSeconds = 90
)

$ErrorActionPreference = "Stop"

# PowerShell 7.3+ defaults to treating any stderr output from native
# commands (docker, git, etc.) as a terminating error, via
# $PSNativeCommandUseErrorActionPreference. Docker/BuildKit routinely
# writes normal progress output to stderr, which then gets misread as a
# script-stopping failure even on success. This script already checks
# $LASTEXITCODE explicitly after every native command, which is the
# correct and sufficient signal -- so disable this PS7 behavior here
# rather than relying on stderr content.
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

# --- Resolve paths relative to this script, not the caller's cwd ---
# This is what makes the script work whether the repo lives at
# C:\Projects\Career OS, D:\Development\CareerOS, E:\Source\CareerOS, or
# anywhere else -- see docs/REPOSITORY_INDEPENDENCE_REPORT.md Task 4.
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "    OK: $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "    WARN: $Message" -ForegroundColor Yellow
}

function Write-Fail {
    param([string]$Message)
    Write-Host "    FAIL: $Message" -ForegroundColor Red
}

function Stop-Bootstrap {
    param([string]$Reason)
    Write-Fail $Reason
    Write-Host ""
    Write-Host "Bootstrap stopped. Fix the issue above and re-run this script -- every step is safe to repeat." -ForegroundColor Red
    exit 1
}

# Runs a docker/docker-compose command while shielding it from PowerShell's
# native-stderr-as-terminating-error behavior. Docker/BuildKit/Compose
# routinely write normal progress output to stderr; depending on PS
# edition/version/host, that can otherwise be misread as a script-stopping
# error even on success. All output still streams to the console live;
# only $LASTEXITCODE (returned here) is treated as the real signal.
function Invoke-DockerCompose {
    param([Parameter(Mandatory)][string[]]$Arguments)
    $previousEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & docker @Arguments 2>&1 | ForEach-Object { Write-Host $_ }
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousEap
    return $exitCode
}

Write-Host "ORION Platform / CareerOS -- developer bootstrap" -ForegroundColor Magenta
Write-Host "Repository root: $RepoRoot"

# --- 1. Git ---
Write-Step "Checking for Git"
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Warn "Git was not found on PATH. Not required to run the stack, but you'll want it to make changes."
} else {
    $gitVersion = git --version
    Write-Ok $gitVersion
}

# --- 2. Docker Desktop / Docker Engine ---
Write-Step "Checking Docker Desktop is running"
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Stop-Bootstrap "Docker was not found on PATH. Install Docker Desktop: https://www.docker.com/products/docker-desktop/"
}
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Stop-Bootstrap "Docker Desktop does not appear to be running. Start Docker Desktop, wait for it to finish starting, then re-run this script."
}
Write-Ok "Docker Desktop is running"

# --- 3. Docker Compose v2 ---
Write-Step "Checking Docker Compose"
docker compose version *> $null
if ($LASTEXITCODE -ne 0) {
    Stop-Bootstrap "'docker compose' (v2, plugin form) is not available. Update Docker Desktop to a recent version."
}
$composeVersion = docker compose version
Write-Ok $composeVersion

# --- 4. Python (optional -- only needed for running things outside Docker) ---
Write-Step "Checking Python (optional -- only needed if you run tests/scripts outside Docker)"
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $pythonCmd) {
    Write-Warn "Python was not found on PATH. Not required for 'docker compose up' -- only for running the backend or its tests outside Docker."
} else {
    $pythonVersion = & $pythonCmd.Source --version 2>&1
    Write-Ok "$pythonVersion ($($pythonCmd.Source))"
}

# --- 5. Required folders exist (catches a partial/corrupt clone early) ---
Write-Step "Validating repository layout"
$requiredPaths = @(
    "docker-compose.yml",
    "platform\kernel\orion_kernel",
    "products\careeros\backend",
    "products\careeros\frontend",
    ".env.example"
)
$missing = @()
foreach ($p in $requiredPaths) {
    $full = Join-Path $RepoRoot $p
    if (-not (Test-Path $full)) {
        $missing += $p
    }
}
if ($missing.Count -gt 0) {
    Stop-Bootstrap "Missing expected paths: $($missing -join ', '). This doesn't look like a complete clone of the repository."
}
Write-Ok "All expected top-level paths are present"

# --- 6. .env from .env.example ---
Write-Step "Checking for .env"
$envPath = Join-Path $RepoRoot ".env"
$envExamplePath = Join-Path $RepoRoot ".env.example"
if (Test-Path $envPath) {
    Write-Ok ".env already exists -- leaving it untouched"
} else {
    Copy-Item $envExamplePath $envPath
    Write-Ok "Created .env from .env.example"
    Write-Warn "Edit .env and set a real SECRET_KEY before anything beyond local development: openssl rand -hex 32"
}

# --- Read port overrides (if any) out of .env so we know what to poll/print later ---
function Get-EnvValue {
    param([string]$Name, [string]$Default)
    $line = Get-Content $envPath -ErrorAction SilentlyContinue | Where-Object { $_ -match "^\s*$Name\s*=" } | Select-Object -Last 1
    if (-not $line) { return $Default }
    $value = ($line -split "=", 2)[1].Trim()
    if ([string]::IsNullOrWhiteSpace($value)) { return $Default }
    return $value
}
$BackendPort = Get-EnvValue -Name "BACKEND_PORT" -Default "8000"
$FrontendPort = Get-EnvValue -Name "FRONTEND_PORT" -Default "5173"
$PostgresPort = Get-EnvValue -Name "POSTGRES_PORT" -Default "5432"

# --- 7. Build containers ---
if (-not $SkipBuild) {
    Write-Step "Building containers (docker compose build) -- this can take a few minutes the first time"
    # Force BuildKit's plain-text progress output. Its default animated/TTY
    # renderer can get garbled or truncated when captured by PowerShell,
    # which then sometimes surfaces as a confusing NativeCommandError
    # instead of the actual build output.
    $env:BUILDKIT_PROGRESS = "plain"
    # NOTE: --progress is a global `docker compose` flag in current Compose
    # versions (v5+), not a `build`-subcommand flag -- it must come before
    # the subcommand, not after it.
    $buildExitCode = Invoke-DockerCompose -Arguments @("compose", "--progress=plain", "build")
    if ($buildExitCode -ne 0) {
        Stop-Bootstrap "'docker compose build' failed (exit code $buildExitCode). See the output above for the failing step."
    }
    Write-Ok "Images built"
} else {
    Write-Step "Skipping build (-SkipBuild passed)"
}

# --- 8. Start services ---
Write-Step "Starting services (docker compose up -d)"
$upExitCode = Invoke-DockerCompose -Arguments @("compose", "up", "-d")
if ($upExitCode -ne 0) {
    Stop-Bootstrap "'docker compose up -d' failed (exit code $upExitCode). See the output above."
}
Write-Ok "Containers started"

# --- 9. Run migrations explicitly ---
# The backend container already runs 'alembic upgrade head' as part of its
# startup command, but we run it again here, explicitly, so bootstrap has
# its own clear pass/fail signal for this step. Alembic migrations are
# idempotent -- upgrading an already-current database is a no-op.
Write-Step "Running database migrations"
$migrationOk = $false
for ($attempt = 1; $attempt -le 10; $attempt++) {
    $previousEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    docker compose exec -T backend alembic upgrade head *> $null
    $migrationExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousEap
    if ($migrationExitCode -eq 0) {
        $migrationOk = $true
        break
    }
    Start-Sleep -Seconds 3
}
if ($migrationOk) {
    Write-Ok "Migrations applied (alembic upgrade head)"
} else {
    Write-Warn "Could not confirm migrations via 'docker compose exec backend alembic upgrade head' -- the backend may still be starting. Check with: docker compose logs backend"
}

# --- 10. Verify health endpoints ---
Write-Step "Waiting for the backend health endpoint (up to $HealthTimeoutSeconds seconds)"
$healthUrl = "http://localhost:$BackendPort/api/v1/health"
$readyUrl = "http://localhost:$BackendPort/api/v1/health/ready"
$deadline = (Get-Date).AddSeconds($HealthTimeoutSeconds)
$healthy = $false
while ((Get-Date) -lt $deadline) {
    try {
        $resp = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5
        if ($resp.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    } catch {
        # Not up yet -- keep polling.
    }
    Start-Sleep -Seconds 2
}

if (-not $healthy) {
    Write-Fail "Backend did not become healthy within $HealthTimeoutSeconds seconds."
    Write-Host "    Check logs with: docker compose logs backend" -ForegroundColor Red
    exit 1
}
Write-Ok "Backend is up: $healthUrl"

try {
    $readyResp = Invoke-WebRequest -Uri $readyUrl -UseBasicParsing -TimeoutSec 5
    if ($readyResp.StatusCode -eq 200) {
        Write-Ok "Backend readiness check passed (database connectivity confirmed): $readyUrl"
    } else {
        Write-Warn "Readiness check returned HTTP $($readyResp.StatusCode) -- database may not be fully ready yet."
    }
} catch {
    Write-Warn "Could not reach readiness endpoint yet: $readyUrl -- it may need a few more seconds."
}

# --- 11. Next steps ---
Write-Host ""
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host " CareerOS (ORION Platform) is up." -ForegroundColor Magenta
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "  Backend API:      http://localhost:$BackendPort"
Write-Host "  API docs:         http://localhost:$BackendPort/docs"
Write-Host "  Frontend:         http://localhost:$FrontendPort"
Write-Host "  Postgres (host):  localhost:$PostgresPort"
Write-Host ""
Write-Host "  Useful commands:"
Write-Host "    docker compose logs -f backend      # tail backend logs"
Write-Host "    docker compose logs -f frontend     # tail frontend logs"
Write-Host "    docker compose down                 # stop the stack"
Write-Host "    docker compose down -v               # stop and wipe the database volume"
Write-Host "    .\scripts\bootstrap.ps1 -SkipBuild   # restart without rebuilding images"
Write-Host ""
Write-Host "  If ports $BackendPort, $FrontendPort, or $PostgresPort are already used by another"
Write-Host "  project on this machine (e.g. NDIP), set BACKEND_PORT / FRONTEND_PORT /"
Write-Host "  POSTGRES_PORT in .env to different values and re-run this script."
Write-Host ""
Write-Host "  Docs: README.md, docs/ARCHITECTURE.md, docs/DEVELOPER_GUIDE.md"
Write-Host ""
