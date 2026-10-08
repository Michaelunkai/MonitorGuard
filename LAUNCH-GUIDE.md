# MonitorGuard — Launch Steps & Quick Reference

## Project Location

```
F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard
```
(7 layers deep under `F:\study`)

---

## Quick Launch (Pick One)

### Option 1: Double-click the .bat (easiest)
```
MonitorGuard-Launch.bat
```
- Checks Python, installs dependencies, launches with status banner
- Works from anywhere — path is hardcoded in the script

### Option 2: PowerShell
```powershell
powershell -ExecutionPolicy Bypass -File "F:\study\...\MonitorGuard\launch.ps1"
```

### Option 3: Silent launch (no console window)
```
MonitorGuard-Silent.vbs
```
- Runs `pythonw.exe` hidden — only the tray icon appears
- Perfect for putting in Startup folder

### Option 4: Direct Python
```batch
cd "F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard"
python main.py
```

### Option 5: Package entry point
```batch
cd "F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard\src"
python -m monitor_guard
```

---

## Command-Line Options

| Flag | Description |
|------|-------------|
| `--off` | Start with isolation disabled (standby mode) |
| `--debug` | Enable verbose debug logging |

Examples:
```batch
python main.py --off --debug
python main.py --off
python main.py --debug
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Shift + S** | Toggle isolation ON / OFF |
| **Shift + Q** | Quit MonitorGuard |

These work from **any application**, including fullscreen games.

---

## System Tray Icon Guide

| Icon | Meaning |
|------|---------|
| 🟢 Green shield with checkmark | Isolation **ACTIVE** — all monitors sealed |
| 🟡 Amber shield with X | **Standby** — isolation OFF, normal Windows behavior |
| 🔴 Red shield with ! | **Conflict** detected (auto-resolves to green) |

Right-click the tray icon for:
- Current status
- Monitor list with process counts
- Toggle isolation
- Refresh monitors
- Quit

---

## Dependencies

All auto-installed by `launch.bat` / `launch.ps1`:

| Package | Purpose |
|---------|---------|
| `pystray` | System tray icon |
| `Pillow` | Dynamic icon rendering (shield shapes) |
| `keyboard` | Global hotkey registration (Shift+S, Shift+Q) |
| `pywin32` | Win32 API for window management |

Install manually if needed:
```batch
pip install pystray pillow keyboard
```

---

## How to Auto-Start on Login

### Method 1: Windows Startup Folder
1. Press `Win+R`, type `shell:startup`, press Enter
2. Copy `MonitorGuard-Silent.vbs` into the opened folder
3. MonitorGuard will start silently on every login

### Method 2: Task Scheduler (recommended for reliability)
1. Open Task Scheduler
2. Create Basic Task → "MonitorGuard"
3. Trigger: "When I log on"
4. Action: "Start a program"
   - Program: `pythonw.exe`
   - Arguments: `main.py`
   - Start in: `F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard`

---

## Testing

Run the integration test suite:
```batch
cd "F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard"
python test_engine.py
```

Expected output: all PASS (11 tests covering monitor detection, icon generation, engine lifecycle, hotkey registration, tray app creation).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Python not found" | Install Python 3.8+ from python.org and add to PATH |
| "Another instance already running" | Check system tray for existing instance, or press Shift+Q on it |
| "Shift+S not working" | Another app may own that hotkey. Use tray menu instead. |
| "Mouse hook unavailable" | Normal in some environments. Window confinement + focus hooks still provide full isolation. |
| "Failed to install dependency" | Run `pip install pystray pillow keyboard` manually |
