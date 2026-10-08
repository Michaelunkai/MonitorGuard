<# 
.SYNOPSIS
    MonitorGuard — PowerShell Launch Script
    Full-monitor isolation for Windows.

.DESCRIPTION
    Checks Python and dependencies, then launches MonitorGuard.
    Press Shift+S to toggle isolation, Shift+Q to quit.

.NOTES
    Project: F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  ╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║                                                            ║" -ForegroundColor Cyan
Write-Host "  ║           ◆ MonitorGuard v1.0 ◆                            ║" -ForegroundColor Cyan
Write-Host "  ║       Full-Monitor Isolation for Windows                   ║" -ForegroundColor Cyan
Write-Host "  ║                                                            ║" -ForegroundColor Cyan
Write-Host "  ║    Shift+S = Toggle isolation  |  Shift+Q = Quit           ║" -ForegroundColor Cyan
Write-Host "  ║                                                            ║" -ForegroundColor Cyan
Write-Host "  ╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Check Python ────────────────────────────────────────────────────

Write-Host "  [1/4] Checking Python..." -ForegroundColor Yellow

try {
    $pyVer = & python --version 2>&1
    Write-Host "        Python: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "        [ERROR] Python is not installed or not on PATH." -ForegroundColor Red
    Write-Host "        Install Python 3.8+ from https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host ""

# ── Ensure dependencies ────────────────────────────────────────────

Write-Host "  [2/4] Checking dependencies..." -ForegroundColor Yellow

$packages = @("pystray", "pillow", "keyboard")
foreach ($pkg in $packages) {
    $check = & python -c "import $pkg" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "        Installing $pkg..." -ForegroundColor Yellow
        & python -m pip install $pkg --quiet 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "        [ERROR] Failed to install $pkg" -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host "        All dependencies satisfied." -ForegroundColor Green
Write-Host ""

# ── Navigate to project ────────────────────────────────────────────

Write-Host "  [3/4] Locating project..." -ForegroundColor Yellow

$projectDir = "F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard"

if (-not (Test-Path "$projectDir\main.py")) {
    Write-Host "        [ERROR] MonitorGuard not found at: $projectDir" -ForegroundColor Red
    exit 1
}

Write-Host "        Project: $projectDir" -ForegroundColor Green
Write-Host ""

# ── Launch ─────────────────────────────────────────────────────────

Write-Host "  [4/4] Starting MonitorGuard..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  ┌──────────────────────────────────────────────────────────┐" -ForegroundColor Green
Write-Host "  │  MonitorGuard is now running!                            │" -ForegroundColor Green
Write-Host "  │                                                          │" -ForegroundColor Green
Write-Host "  │  • Green shield  = Isolation ACTIVE                      │" -ForegroundColor Green
Write-Host "  │  • Amber shield  = Standby (isolation OFF)               │" -ForegroundColor Green
Write-Host "  │  • Red shield    = Conflict detected                     │" -ForegroundColor Green
Write-Host "  │                                                          │" -ForegroundColor Green
Write-Host "  │  Shift+S  = Toggle isolation ON / OFF                    │" -ForegroundColor Green
Write-Host "  │  Shift+Q  = Quit MonitorGuard                            │" -ForegroundColor Green
Write-Host "  └──────────────────────────────────────────────────────────┘" -ForegroundColor Green
Write-Host ""

Push-Location $projectDir
try {
    & python main.py $args
    if ($LASTEXITCODE -ne 0) {
        Write-Host "        [!] main.py failed, trying package entry point..." -ForegroundColor Yellow
        Push-Location (Join-Path $projectDir "src")
        try {
            & python -m monitor_guard $args
        } finally {
            Pop-Location
        }
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   MonitorGuard has stopped." -ForegroundColor Cyan
Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Cyan
