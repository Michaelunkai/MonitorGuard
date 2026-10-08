"""
MonitorGuard — System Tray Application
Full-monitor isolation for Windows. One monitor, one world, no crossover.

This is the main entry point. It creates:
- A system tray icon with dynamic status
- Global hotkey (Shift+S) for toggle
- Context menu with status, monitor info, toggle, and quit
- Core isolation engine that enforces display boundaries
"""

import sys
import os
import ctypes
import ctypes.wintypes as wintypes
import logging
import threading
import time
from ctypes import byref, sizeof

# Add the src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor_guard.display import DisplayManager
from monitor_guard.isolation import IsolationEngine
from monitor_guard.icon import draw_active_icon, draw_standby_icon, draw_conflict_icon, pil_to_hicon

try:
    import pystray
    from pystray import MenuItem
    from PIL import Image
except ImportError:
    print("[MonitorGuard] ERROR: Required packages not installed.")
    print("  pip install pystray pillow keyboard")
    sys.exit(1)

try:
    import keyboard
except ImportError:
    keyboard = None

# ── Logging ─────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="[MonitorGuard] %(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("MonitorGuard")

# ── Single instance mutex ───────────────────────────────────────────

MUTEX_NAME = "Global\\MonitorGuard_SingleInstance_{E4B3F2A1-7C9D-4E6F-8A2B-1D3C5E7F9A0B}"

def ensure_single_instance():
    """Return True if this is the only instance; exit if another is running."""
    mutex = ctypes.windll.kernel32.CreateMutexW(None, True, MUTEX_NAME)
    error = ctypes.windll.kernel32.GetLastError()
    ERROR_ALREADY_EXISTS = 183
    if error == ERROR_ALREADY_EXISTS:
        log.warning("Another instance is already running. Exiting.")
        return None
    return mutex


# ── Application class ───────────────────────────────────────────────

class MonitorGuardApp:
    """Main application: tray icon, hotkeys, isolation engine."""

    def __init__(self):
        self._display = DisplayManager()
        self._isolation = IsolationEngine(self._display)
        self._icon = None
        self._running = False

        # Wire events
        self._isolation.on_state_changed(self._on_state_changed)
        self._isolation.on_conflict(self._on_conflict)
        self._display.on_displays_changed(self._on_displays_changed)

    def run(self):
        """Start the application — blocking."""
        log.info("Starting MonitorGuard v0.1.0")
        log.info("Press Shift+S to toggle isolation, Shift+Q to quit")

        # Initial display enumeration
        self._display.refresh()

        # Create tray icon
        self._icon = pystray.Icon(
            name="MonitorGuard",
            icon=self._create_pil_icon("standby"),
            title="MonitorGuard — Shift+S to toggle",
            menu=self._build_menu(),
        )

        # Register global hotkeys
        self._register_hotkeys()

        self._running = True
        log.info("MonitorGuard running. Tray icon active.")

        try:
            self._icon.run()
        except KeyboardInterrupt:
            log.info("Interrupted by user.")
        finally:
            self._cleanup()

    def _create_pil_icon(self, state: str) -> Image.Image:
        """Create a PIL Image for the given state."""
        if state == "active":
            return draw_active_icon(64)
        elif state == "conflict":
            return draw_conflict_icon(64)
        else:
            return draw_standby_icon(64)

    def _build_menu(self) -> pystray.Menu:
        """Build the right-click context menu."""
        return pystray.Menu(
            MenuItem(
                lambda: f"{'✅ ISOLATION ACTIVE' if self._isolation.active else '⏸ Standby'}",
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            MenuItem(
                lambda: "Disable Isolation (Shift+S)" if self._isolation.active
                         else "Enable Isolation (Shift+S)",
                self._toggle_isolation,
            ),
            pystray.Menu.SEPARATOR,
            *self._build_monitor_menu_items(),
            pystray.Menu.SEPARATOR,
            MenuItem("About MonitorGuard", self._show_about),
            MenuItem("Quit (Shift+Q)", self._quit),
        )

    def _build_monitor_menu_items(self):
        """Build menu items showing monitor info."""
        items = []
        for m in self._display.monitors:
            prim = " (primary)" if m.is_primary else ""
            text = f"{m.device_name} — {m.bounds.width}×{m.bounds.height}{prim} [{len(m.assigned_pids)} proc]"
            items.append(MenuItem(text, None, enabled=False))
        if not self._display.monitors:
            items.append(MenuItem("No monitors detected", None, enabled=False))
        return items

    def _register_hotkeys(self):
        """Register global hotkeys using the keyboard library or Win32 directly."""
        if keyboard:
            try:
                keyboard.add_hotkey("shift+s", self._toggle_isolation, suppress=False)
                log.info("Hotkey registered: Shift+S (toggle)")
            except Exception as e:
                log.warning("Failed to register Shift+S via keyboard lib: %s", e)
                self._register_hotkeys_win32()

            try:
                keyboard.add_hotkey("shift+q", self._quit, suppress=False)
                log.info("Hotkey registered: Shift+Q (quit)")
            except Exception as e:
                log.warning("Failed to register Shift+Q via keyboard lib: %s", e)
        else:
            self._register_hotkeys_win32()

    def _register_hotkeys_win32(self):
        """Fallback: register hotkeys using raw Win32 RegisterHotKey."""
        # Create a hidden message window to receive WM_HOTKEY
        log.info("Using Win32 RegisterHotKey fallback for hotkeys")
        # We'll use a background thread with a message pump
        self._hotkey_thread = threading.Thread(
            target=self._hotkey_message_pump, daemon=True
        )
        self._hotkey_thread.start()

    def _hotkey_message_pump(self):
        """Hidden window message pump for receiving WM_HOTKEY."""
        # Register a window class
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        WNDPROC = ctypes.WINFUNCTYPE(
            ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
        )

        def wndproc(hwnd, msg, wparam, lparam):
            if msg == 0x0312:  # WM_HOTKEY
                hotkey_id = wparam
                if hotkey_id == 1:  # Toggle
                    self._toggle_isolation()
                elif hotkey_id == 2:  # Quit
                    self._quit()
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self._wndproc_ref = WNDPROC(wndproc)  # prevent GC

        # Register window class
        wc = wintypes.WNDCLASSEXW()
        wc.cbSize = sizeof(wintypes.WNDCLASSEXW)
        wc.lpfnWndProc = self._wndproc_ref
        wc.hInstance = kernel32.GetModuleHandleW(None)
        wc.lpszClassName = "MonitorGuard_HotkeyWnd"

        atom = user32.RegisterClassExW(byref(wc))

        # Create hidden window
        hwnd = user32.CreateWindowExW(
            0, atom, "MonitorGuard Hotkey Receiver",
            0, 0, 0, 0, 0,
            None, None, kernel32.GetModuleHandleW(None), None
        )

        if not hwnd:
            log.error("Failed to create hotkey window")
            return

        self._hotkey_hwnd = hwnd

        # Register hotkeys
        user32.RegisterHotKey(hwnd, 1, 0x0002, 0x53)  # Shift+S
        user32.RegisterHotKey(hwnd, 2, 0x0002, 0x51)  # Shift+Q
        log.info("Win32 hotkeys registered: Shift+S (toggle), Shift+Q (quit)")

        # Message loop
        msg = wintypes.MSG()
        while user32.GetMessageW(byref(msg), None, 0, 0):
            user32.TranslateMessage(byref(msg))
            user32.DispatchMessageW(byref(msg))

    # ── Actions ──────────────────────────────────────────────────────

    def _toggle_isolation(self, icon=None, item=None):
        """Toggle isolation on/off."""
        self._isolation.toggle()

    def _show_about(self, icon=None, item=None):
        """Show about info as a notification."""
        if self._icon:
            self._icon.notify(
                "MonitorGuard v0.1.0\n"
                "Full-monitor isolation for Windows.\n"
                "One monitor, one world, no crossover.\n\n"
                "Shift+S — Toggle isolation\n"
                "Shift+Q — Quit",
                title="About MonitorGuard"
            )

    def _quit(self, icon=None, item=None):
        """Stop the application."""
        log.info("Quitting MonitorGuard...")
        self._running = False
        if self._icon:
            self._icon.stop()

    # ── Event handlers ──────────────────────────────────────────────

    def _on_state_changed(self, active: bool):
        """Update tray icon when isolation state changes."""
        state = "active" if active else "standby"
        if self._icon:
            self._icon.icon = self._create_pil_icon(state)

            status = "ISOLATION ACTIVE" if active else "Standby"
            monitor_count = len(self._display.monitors)
            title = f"MonitorGuard [{status}] — {monitor_count} monitor{'s' if monitor_count != 1 else ''}"
            self._icon.title = title

            # Rebuild menu to reflect new toggle text
            self._icon.menu = self._build_menu()

            # Show notification
            msg = "Monitor isolation ENABLED — all displays are sealed." if active \
                  else "Monitor isolation DISABLED — normal behaviour restored."
            self._icon.notify(msg, title="MonitorGuard")

    def _on_conflict(self, message: str):
        """Flash the conflict icon briefly."""
        if self._icon:
            self._icon.icon = self._create_pil_icon("conflict")
            # Reset after brief flash
            def reset():
                time.sleep(0.8)
                if self._running and self._icon:
                    state = "active" if self._isolation.active else "standby"
                    self._icon.icon = self._create_pil_icon(state)
            threading.Thread(target=reset, daemon=True).start()

    def _on_displays_changed(self):
        """Refresh when monitors change."""
        self._display.refresh()
        if self._icon:
            self._icon.menu = self._build_menu()

    # ── Cleanup ──────────────────────────────────────────────────────

    def _cleanup(self):
        log.info("Cleaning up...")
        self._isolation.cleanup()

        # Unregister Win32 hotkeys if we created the hidden window
        if hasattr(self, '_hotkey_hwnd') and self._hotkey_hwnd:
            try:
                user32 = ctypes.windll.user32
                user32.UnregisterHotKey(self._hotkey_hwnd, 1)
                user32.UnregisterHotKey(self._hotkey_hwnd, 2)
                user32.DestroyWindow(self._hotkey_hwnd)
            except Exception:
                pass

        if keyboard:
            try:
                keyboard.unhook_all()
            except Exception:
                pass

        log.info("MonitorGuard stopped.")


# ── Main ────────────────────────────────────────────────────────────

def main():
    # Single instance check
    mutex = ensure_single_instance()
    if mutex is None:
        return

    try:
        app = MonitorGuardApp()
        app.run()
    except Exception as ex:
        log.error("Fatal error: %s", ex, exc_info=True)
        ctypes.windll.user32.MessageBoxW(
            0,
            f"MonitorGuard encountered a fatal error:\n\n{ex}",
            "MonitorGuard",
            0x10  # MB_ICONERROR
        )
    finally:
        if mutex:
            ctypes.windll.kernel32.ReleaseMutex(mutex)
            ctypes.windll.kernel32.CloseHandle(mutex)


if __name__ == "__main__":
    main()
