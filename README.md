# MonitorGuard — Full-Monitor Isolation for Windows

> **One monitor. One world. No crossover.**

MonitorGuard is a lightweight Windows system-tray utility that creates **complete isolation boundaries between every connected display**. When active, each monitor becomes its own sealed environment — processes, windows, and input on one display are entirely invisible and unreachable from every other display.

---

## Why MonitorGuard?

Modern multi-monitor setups are a leaky abstraction. Windows treats all monitors as one shared desktop surface, which means:

- A notification from a background agent can pop over your game
- An AI tool can grab focus from your workspace
- A fullscreen app on one screen can still be interrupted by anything on another
- There is no OS-level way to say "this screen belongs to this task and nothing else"

**MonitorGuard fixes this** by enforcing display-level boundaries that the OS doesn't provide natively.

---

## What It Does

| Capability | Detail |
|---|---|
| **Full Monitor Isolation** | Each connected display is scoped to its own process environment. Nothing on Display A can create windows, send input, steal focus, or render anything on Display B. |
| **System Tray Presence** | A beautiful, dynamically-colored tray icon indicates live status at a glance — green when isolation is active, warm amber in standby, red if a conflict is detected. |
| **Global Toggle (Shift + S)** | Enable or disable isolation instantly with `Shift + S`. No need to find the tray icon, open a menu, or switch context. Works from any application. |
| **Zero Overlap** | MonitorGuard does not bind to any port, pipe, or named resource that other applications use. It does not install drivers, services, or shell extensions. It coexists cleanly. |
| **No Process Interference** | Running MonitorGuard does not affect the behavior, performance, or resource allocation of any application — it only adds a boundary layer between displays. |

---

## Use Cases

### Gaming + AI Agents
Run a competitive game fullscreen on Monitor 1 while autonomous AI agents, browsers, and automation tools operate on Monitor 2+. The agents can never pop up a window, grab focus, or interact with the game display. The game is completely shielded.

### Secure Workstation
Keep a sensitive application (trading terminal, classified documents, medical software) isolated on one display while general-purpose browsing and communication happen on others. No cross-contamination of input or visual data.

### Presentation Mode
Present on one monitor while controlling notes, chat, and monitoring tools on another — with absolute certainty that nothing from the control screen will flash onto the presentation display.

### Development + Monitoring
Run a build/test environment on one screen and dashboards/logs on another, with zero chance that a test failure alert will overlay your editor.

---

## How It Works (Architecture Overview)

MonitorGuard operates at the **window management layer** using documented Windows APIs:

1. **Display Enumeration** — Enumerates all active displays via `EnumDisplayMonitors` / `EnumDisplayDevices`.
2. **Window-to-Monitor Binding** — Tracks which windows are on which monitor using `MonitorFromWindow` and `GetMonitorInfo`.
3. **Boundary Enforcement** — Intercepts cross-display window creation and input routing using a low-level hook chain (`SetWinEventHook`, `SetWindowsHookEx`). When a process on Display A attempts to create or move a window onto Display B, MonitorGuard silently redirects or blocks the operation.
4. **Tray Icon Rendering** — Uses Pillow (PIL) to dynamically draw a shield-shaped tray icon with state-dependent coloring. No external icon files needed.
5. **Hotkey Registration** — Registers `Shift + S` as a global hotkey via the `keyboard` library (with Win32 `RegisterHotKey` fallback) with no conflicts against standard Windows shortcuts or common application bindings.

All enforcement is **non-destructive**: MonitorGuard never terminates processes, modifies window styles permanently, or changes system settings. Disabling (via Shift+S or tray menu) immediately removes all boundaries and restores normal Windows behavior.

---

## Requirements

| Requirement | Detail |
|---|---|
| **OS** | Windows 10 (1809+) or Windows 11 |
| **Displays** | 2+ connected monitors (works with 1 too, for testing) |
| **Runtime** | Python 3.8+ |
| **Privileges** | Standard user — no admin elevation required |
| **Dependencies** | `pystray`, `Pillow`, `keyboard` (auto-installed by launch script) |

---

## Quick Start

### Option A: Launch Script (recommended)
```batch
cd MonitorGuard
launch.bat
```

### Option B: PowerShell
```powershell
cd MonitorGuard
powershell -ExecutionPolicy Bypass -File launch.ps1
```

### Option C: Direct Python
```batch
cd MonitorGuard\src
python -m monitor_guard
```

---

## Project Structure

```
MonitorGuard/
├── README.md                           ← This file
├── USAGE.md                            ← Detailed usage guide
├── launch.bat                          ← One-click launcher (batch)
├── launch.ps1                          ← One-click launcher (PowerShell)
├── src/
│   └── monitor_guard/
│       ├── __init__.py                 ← Package metadata
│       ├── __main__.py                 ← Entry point + tray app
│       ├── native.py                   ← Win32 P/Invoke declarations
│       ├── display.py                  ← Monitor enumeration + tracking
│       ├── isolation.py                ← Core isolation engine
│       └── icon.py                     ← Dynamic tray icon drawing
├── resources/
│   └── (reserved for future .ico files)
├── tests/
│   └── (reserved for test suite)
└── docs/
    └── architecture.md                 ← Technical deep-dive
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Shift + S` | Toggle monitor isolation ON / OFF |
| `Shift + Q` | Quit MonitorGuard |

> **Note:** `Shift + S` was chosen because it does not conflict with any default Windows shortcut, does not overlap with common application bindings (VS Code, browsers, games), and is easy to press with one hand.

---

## Frequently Asked Questions

**Will this affect my FPS in games?**
No. MonitorGuard operates at the window-management layer, not the rendering pipeline. It does not inject into DirectX/Vulkan, modify display settings, or add GPU overhead.

**Can I isolate specific windows instead of entire monitors?**
Not in this version. MonitorGuard enforces whole-display isolation — the simplest and most reliable model. Window-level isolation may come in a future release.

**What happens if I disconnect a monitor?**
MonitorGuard automatically detects display changes via `WM_DISPLAYCHANGE` and adjusts boundaries in real time. No restart needed.

**Does this work with Remote Desktop or virtual displays?**
Physical and virtual monitors are treated identically. RDP sessions, Parsec displays, and spacedesk virtual monitors are all isolated.

**Is there a performance impact?**
Negligible. The hook chain is lightweight and only processes window-creation and focus messages. No polling, no timers, no background threads consuming CPU.

---

## License

MIT — use it, modify it, ship it. No restrictions.

---

## Status

**Phase:** Development — full implementation complete, testing in progress.
**Current version:** 0.1.0 (pre-alpha)
**Target:** Fully functional MVP with tray icon, Shift+S toggle, and real-time monitor isolation.
