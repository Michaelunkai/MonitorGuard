<# 
.SYNOPSIS
    MonitorGuard — Launch Script (v1.1)
    Full-monitor isolation for Windows.

.DESCRIPTION
    Checks dependencies, then starts MonitorGuard.
    Press Shift+S to toggle isolation, Shift+Q to quit.

.NOTES
    Run from the MonitorGuard project root:
    powershell -ExecutionPolicy Bypass -File launch.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║           MonitorGuard v1.1 Launcher                 ║" -ForegroundColor Cyan
Write-Host "  ║      Full-monitor isolation for Windows              ║" -ForegroundColor Cyan
Write-Host "  ║  Shift+S = toggle isolation  |  Shift+Q = quit      ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Check Python ────────────────────────────────────────────────────

Write-Host "[1/3] Checking dependencies..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "       Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "       [ERROR] Python is not installed or not on PATH." -ForegroundColor Red
    Write-Host "       Install Python 3.8+ from https://python.org" -ForegroundColor Red
    exit 1
}

# ── Ensure required packages ────────────────────────────────────────

$packages = @("pystray", "pillow", "keyboard")
foreach ($pkg in $packages) {
    $check = python -c "import $pkg" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "       Installing $pkg..." -ForegroundColor Yellow
        python -m pip install $pkg --quiet 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "       [ERROR] Failed to install $pkg" -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host "       All dependencies satisfied." -ForegroundColor Green
Write-Host ""

# ── Launch ──────────────────────────────────────────────────────────

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[2/3] Starting MonitorGuard..." -ForegroundColor Yellow
Write-Host "[3/3] Press Shift+S to toggle isolation, Shift+Q to quit" -ForegroundColor Yellow
Write-Host ""

Push-Location $scriptDir
try {
    python main.py $args
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "       [!] main.py failed. Trying package entry point..." -ForegroundColor Yellow
        Push-Location (Join-Path $scriptDir "src")
        try {
            python -m monitor_guard $args
        } finally {
            Pop-Location
        }
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "  MonitorGuard has stopped." -ForegroundColor Cyan
