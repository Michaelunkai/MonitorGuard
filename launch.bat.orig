@echo off
REM ─────────────────────────────────────────────────────────────
REM  MonitorGuard — Launch Script (v1.1)
REM  Full-monitor isolation for Windows
REM  Shift+S to toggle, Shift+Q to quit
REM ─────────────────────────────────────────────────────────────

title MonitorGuard Launcher
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║           MonitorGuard v1.1 Launcher                 ║
echo  ║      Full-monitor isolation for Windows              ║
echo  ║  Shift+S = toggle isolation  |  Shift+Q = quit      ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

REM Check Python is available
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not on PATH.
    echo         Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Show Python version
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Python: %PYVER%
echo.

REM Check and install required packages
echo [1/3] Checking dependencies...

python -c "import pystray" >nul 2>&1
if %errorlevel% neq 0 (
    echo       Installing pystray...
    python -m pip install pystray --quiet 2>nul
)

python -c "from PIL import Image" >nul 2>&1
if %errorlevel% neq 0 (
    echo       Installing Pillow...
    python -m pip install pillow --quiet 2>nul
)

python -c "import keyboard" >nul 2>&1
if %errorlevel% neq 0 (
    echo       Installing keyboard...
    python -m pip install keyboard --quiet 2>nul
)

echo       All dependencies satisfied.
echo.

REM Determine script directory and set working directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Launch MonitorGuard via main.py (primary entry point)
echo [2/3] Starting MonitorGuard...
echo [3/3] Press Shift+S to toggle isolation, Shift+Q to quit
echo.

python main.py %*

REM Fallback: if main.py fails, try the package entry point
if %errorlevel% neq 0 (
    echo.
    echo [!] main.py exited with error. Trying package entry point...
    set "SRC_DIR=%SCRIPT_DIR%src"
    cd /d "%SRC_DIR%"
    python -m monitor_guard %*
)

echo.
echo  MonitorGuard has stopped.
pause
