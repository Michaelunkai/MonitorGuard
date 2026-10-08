@echo off
:: MonitorGuard — Quick Launch
:: Double-click this file to start monitor isolation with tray icon.
:: Press Shift+S to toggle isolation ON/OFF.
:: Press Shift+Q to quit.
:: Right-click the tray icon for options.

echo.
echo  Starting MonitorGuard...
echo  (Shift+S = toggle  |  Shift+Q = quit  |  Right-click tray icon for menu)
echo.

python "%~dp0main.py" %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo  [!] MonitorGuard exited with error code %ERRORLEVEL%
    echo      Make sure you have Python 3.8+ and dependencies installed:
    echo      pip install pystray pillow keyboard
    echo.
    pause
)
