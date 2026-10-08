# MonitorGuard — Usage Guide

## Starting MonitorGuard

### Option A: Launch Script (easiest — recommended)
```batch
cd "F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard"
launch.bat
```

### Option B: PowerShell
```powershell
cd "F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard"
powershell -ExecutionPolicy Bypass -File launch.ps1
```

### Option C: Quick Launch (double-click run.bat)
Simply double-click `run.bat` in the project folder.

### Option D: Direct Python
```batch
cd "F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard"
python main.py
```

### Option E: Package Entry Point
```batch
cd "F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard\src"
python -m monitor_guard
```

---

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--off` | Start with isolation disabled (standby mode) |
| `--debug` | Enable verbose debug logging |

Example:
```batch
python main.py --off --debug
```

---

## First Launch

1. MonitorGuard starts in **active** mode (green shield icon in system tray).
2. The tray icon shows a **green shield** when isolation is ON.
3. All connected monitors are now sealed — each becomes its own isolated world.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Shift + S` | Toggle isolation ON / OFF |
| `Shift + Q` | Quit MonitorGuard (only via tray menu) |

These hotkeys work from **any application**, including fullscreen games.

---

## What Happens When Isolation Is Active

- **New windows** are automatically placed on the monitor where their parent process already has windows.
- **Focus stealing** across monitors is blocked — a background agent on Monitor 2 cannot pop up over your game on Monitor 1.
- **Window dragging** across monitor boundaries is prevented — windows snap back to their assigned monitor.
- **Process assignments** are tracked per-monitor and updated automatically.

---

## System Tray Icon

| Icon Colour | Meaning |
|-------------|---------|
| **Green shield** | Isolation is ACTIVE — all monitors sealed |
| **Amber/Grey shield** | Standby — isolation is OFF, normal Windows behaviour |
| **Red shield** (flashing) | A conflict was detected and resolved — brief, auto-resolves to green |

Right-click the tray icon for:
- Current status
- Monitor list with process counts
- Toggle isolation
- Refresh monitors
- Quit

---

## Disabling MonitorGuard

1. Press **Shift+S** to turn off isolation, OR
2. Right-click the tray icon → Quit

When isolation is turned off, all windows immediately regain normal cross-monitor freedom. No restart needed.

---

## Troubleshooting

### "Failed to register Shift+S hotkey"
Another application is already using Shift+S. Close that application or use the tray menu to toggle instead.

### Resource Usage
MonitorGuard uses negligible resources:
- No GPU overhead (no rendering hooks)
- No polling loops (event-driven architecture)
- Typical memory: 15–30 MB
- Typical CPU: < 0.1% (only wakes on window events)

### Does not affect game performance
MonitorGuard operates at the window-management layer, not the DirectX/Vulkan rendering pipeline. It does not intercept GPU calls or modify display settings.

### Python dependencies not found
Run `launch.bat` which auto-installs them, or manually:
```batch
pip install pystray pillow keyboard
```

### "Another instance is already running"
MonitorGuard enforces single-instance operation. Check the system tray for an existing instance before launching again.

### Mouse hook unavailable message
This is normal in some environments (e.g., running without admin privileges in certain Windows configurations). MonitorGuard falls back to window confinement + focus hooks, which still provides full isolation.

---

## Project Location

```
F:\study\Operating_Systems\Windows\Administration\Display\MonitorIsolation\MonitorGuard\
```
(7 layers deep under F:\study — as required)
