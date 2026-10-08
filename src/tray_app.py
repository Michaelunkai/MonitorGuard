"""
System tray application — ties together the isolation engine, tray icon,
global hotkey, and user interaction.
"""

import sys
import os
import time
import threading
import logging

import pystray
from PIL import Image
import keyboard

from .isolation_engine import IsolationEngine
from .icon_renderer import generate_icon
from .monitor_utils import get_all_monitors

log = logging.getLogger("MonitorGuard")


class TrayApp:
    """System tray application with isolation toggle."""

    ICON_SIZE = 64
    HOTKEY = "shift+s"
    POLL_INTERVAL = 2  # seconds between icon animations

    def __init__(self):
        self.engine = IsolationEngine()
        self.engine.set_state_change_callback(self._on_state_change)

        self._icon: pystray.Icon = None
        self._active_icon = None
        self._inactive_icon = None
        self._anim_thread = None
        self._running = False
        self._frame = 0

        self._generate_icons()

    def _generate_icons(self):
        """Pre-render active and inactive icons."""
        self._active_icon = generate_icon(self.ICON_SIZE, active=True)
        self._inactive_icon = generate_icon(self.ICON_SIZE, active=False)

    def _on_state_change(self, enabled: bool):
        """Called by engine when isolation is toggled."""
        status = "ACTIVE" if enabled else "INACTIVE"
        log.info(f"Isolation {status}")
        if self._icon:
            self._update_icon()
            self._icon.title = f"MonitorGuard — {status}"

    def _update_icon(self):
        """Swap the tray icon to reflect current state."""
        if not self._icon:
            return
        if self.engine.enabled:
            self._icon.icon = self._active_icon
        else:
            self._icon.icon = self._inactive_icon

    def _build_menu(self):
        """Build the right-click context menu."""
        status_text = "✅ Isolation: ACTIVE" if self.engine.enabled else "⏸️ Isolation: PAUSED"

        monitors = get_all_monitors()
        monitor_lines = []
        for i, m in enumerate(monitors):
            tag = " ★" if m.is_primary else ""
            monitor_lines.append(f"Monitor {i+1}: {m.width}x{m.height}{tag}")

        menu = pystray.Menu(
            pystray.MenuItem(status_text, None, enabled=False),
            pystray.MenuItem(f"Monitors: {len(monitors)}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Toggle Isolation (Shift+S)",
                lambda: self._toggle(),
            ),
            pystray.MenuItem(
                "Refresh Monitors",
                lambda: self._refresh_monitors(),
            ),
            pystray.Menu.SEPARATOR,
            *[pystray.MenuItem(line, None, enabled=False) for line in monitor_lines],
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Quit",
                lambda: self._quit(),
            ),
        )
        return menu

    def _toggle(self):
        """Toggle isolation on/off."""
        self.engine.toggle()
        self._update_icon()
        # Rebuild menu to show updated status
        if self._icon:
            self._icon.menu = self._build_menu()

    def _refresh_monitors(self):
        """Force re-enumerate monitors."""
        monitors = get_all_monitors()
        log.info(f"Detected {len(monitors)} monitor(s):")
        for m in monitors:
            log.info(f"  {m}")
        # Rebuild window map if enabled
        if self.engine.enabled:
            self.engine._build_window_map()

    def _quit(self):
        """Shutdown the application."""
        log.info("Quitting MonitorGuard...")
        self._running = False
        self.engine.stop()
        if self._icon:
            self._icon.stop()
        # Unregister hotkey
        try:
            keyboard.remove_hotkey(self.HOTKEY)
        except Exception:
            pass

    def _animation_loop(self):
        """Subtle icon animation loop (pulse effect)."""
        while self._running:
            try:
                self._frame += 1
                new_icon = generate_icon(
                    self.ICON_SIZE,
                    active=self.engine.enabled,
                    frame=self._frame,
                )
                if self._icon:
                    self._icon.icon = new_icon
            except Exception:
                pass
            time.sleep(self.POLL_INTERVAL)

    def _setup_hotkey(self):
        """Register global Shift+S hotkey."""
        keyboard.add_hotkey(self.HOTKEY, self._toggle, suppress=False)
        log.info(f"Registered hotkey: {self.HOTKEY}")

    def run(self):
        """Start the tray app and isolation engine."""
        self._running = True

        # Start the isolation engine (installs hooks)
        self.engine.start()

        # Register the global hotkey
        self._setup_hotkey()

        # Enumerate monitors on startup
        self._refresh_monitors()

        # Start animation thread
        self._anim_thread = threading.Thread(target=self._animation_loop, daemon=True, name="MG-Anim")
        self._anim_thread.start()

        # Create and run tray icon
        self._icon = pystray.Icon(
            "MonitorGuard",
            self._active_icon,
            "MonitorGuard — Isolation ACTIVE",
            menu=self._build_menu(),
        )

        log.info("MonitorGuard is running. Press Shift+S to toggle. Right-click tray icon for options.")

        try:
            self._icon.run()
        except KeyboardInterrupt:
            pass
        finally:
            self._quit()
