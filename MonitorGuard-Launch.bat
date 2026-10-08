@echo off
REM ═══════════════════════════════════════════════════════════════════
REM  MonitorGuard — Master Launch Script
REM  Full-monitor isolation for Windows
REM  Project: F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard
REM  
REM  Features:
REM    - Beautiful shield icon in system tray (green=active, amber=standby, red=conflict)
REM    - Complete monitor isolation — each display is a sealed environment
REM    - Shift+S = toggle isolation ON/OFF
REM    - Shift+Q = quit
REM    - Zero overlap with other processes or key bindings
REM
REM  Usage:
REM    Double-click this .bat to launch from anywhere
REM    Or: MonitorGuard-Launch.bat [--off] [--debug]
REM ═══════════════════════════════════════════════════════════════════

title MonitorGuard — Full Monitor Isolation
color 0A

echo.
echo  ╔════════════════════════════════════════════════════════════╗
echo  ║                                                            ║
echo  ║           ◆ MonitorGuard v1.0 ◆                            ║
echo  ║       Full-Monitor Isolation for Windows                   ║
echo  ║                                                            ║
echo  ║    Shift+S = Toggle isolation  |  Shift+Q = Quit           ║
echo  ║                                                            ║
echo  ╚════════════════════════════════════════════════════════════╝
echo.

REM ── Step 1: Check Python ─────────────────────────────────────────

echo  [1/4] Checking Python installation...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ╔════════════════════════════════════════════════════════════╗
    echo  ║  ERROR: Python is not installed or not on PATH            ║
    echo  ║  Install Python 3.8+ from https://python.org             ║
    echo  ╚════════════════════════════════════════════════════════════╝
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo          Python found: %PYVER%
echo.

REM ── Step 2: Check and install dependencies ───────────────────────

echo  [2/4] Checking dependencies...

python -c "import pystray" >nul 2>&1
if %errorlevel% neq 0 (
    echo          Installing pystray...
    python -m pip install pystray --quiet 2>nul
    if %errorlevel% neq 0 (
        echo  [ERROR] Failed to install pystray
        pause
        exit /b 1
    )
)

python -c "from PIL import Image" >nul 2>&1
if %errorlevel% neq 0 (
    echo          Installing Pillow...
    python -m pip install pillow --quiet 2>nul
    if %errorlevel% neq 0 (
        echo  [ERROR] Failed to install Pillow
        pause
        exit /b 1
    )
)

python -c "import keyboard" >nul 2>&1
if %errorlevel% neq 0 (
    echo          Installing keyboard...
    python -m pip install keyboard --quiet 2>nul
    if %errorlevel% neq 0 (
        echo  [ERROR] Failed to install keyboard
        pause
        exit /b 1
    )
)

python -c "import ctypes; ctypes.windll.kernel32" >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] This script requires Windows (Win32 API not available)
    pause
    exit /b 1
)

echo          All dependencies satisfied.
echo.

REM ── Step 3: Navigate to project ──────────────────────────────────

echo  [3/4] Locating MonitorGuard project...

set "PROJECT_DIR=F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard"

if not exist "%PROJECT_DIR%\main.py" (
    echo.
    echo  ╔════════════════════════════════════════════════════════════╗
    echo  ║  ERROR: MonitorGuard project not found at expected path   ║
    echo  ║  Path: %PROJECT_DIR%
    echo  ╚════════════════════════════════════════════════════════════╝
    echo.
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"
echo          Project found at:
echo          %PROJECT_DIR%
echo.

REM ── Step 4: Launch MonitorGuard ──────────────────────────────────

echo  [4/4] Starting MonitorGuard...
echo.
echo  ┌──────────────────────────────────────────────────────────┐
echo  │  MonitorGuard is now running!                            │
echo  │                                                          │
echo  │  • Green shield icon  = Isolation ACTIVE                 │
echo  │  • Amber shield icon  = Standby (isolation OFF)          │
echo  │  • Red shield icon    = Conflict detected                │
echo  │                                                          │
echo  │  Shift+S  = Toggle isolation ON / OFF                    │
echo  │  Shift+Q  = Quit MonitorGuard                            │
echo  │                                                          │
echo  │  Right-click tray icon for options                       │
echo  └──────────────────────────────────────────────────────────┘
echo.

python main.py %*

if %errorlevel% neq 0 (
    echo.
    echo  [!] main.py exited with error code %errorlevel%
    echo  Trying package entry point as fallback...
    echo.
    cd /d "%PROJECT_DIR%\src"
    python -m monitor_guard %*
)

echo.
echo  ════════════════════════════════════════════════════════════
echo   MonitorGuard has stopped.
echo  ════════════════════════════════════════════════════════════
echo.
pause
