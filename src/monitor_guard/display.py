"""
Display adapter — wraps the monitor_utils module into a DisplayManager
with change detection and per-monitor PID tracking.
"""

import ctypes
import ctypes.wintypes as wintypes
import threading
import logging
import sys
import os
from typing import List, Optional, Callable, Set
from dataclasses import dataclass

# Ensure MonitorGuard root is on path so we can import src.* as a package
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.monitor_utils import get_all_monitors, MonitorInfo, RECT

log = logging.getLogger("MonitorGuard.display")


@dataclass
class MonitorBounds:
    width: int
    height: int


@dataclass
class MonitorEntry:
    handle: int
    device_name: str
    bounds: MonitorBounds
    is_primary: bool
    assigned_pids: Set[int]


class DisplayManager:
    """Enumerates monitors, detects display changes, and tracks per-monitor PIDs."""

    def __init__(self):
        self.monitors: List[MonitorEntry] = []
        self._on_displays_changed: Optional[Callable] = None
        self._observer_thread: Optional[threading.Thread] = None
        self._running = False

    def refresh(self):
        """Re-enumerate all connected monitors."""
        raw = get_all_monitors()
        self.monitors = []
        for m in raw:
            self.monitors.append(MonitorEntry(
                handle=m.handle,
                device_name=m.name,
                bounds=MonitorBounds(width=m.width, height=m.height),
                is_primary=m.is_primary,
                assigned_pids=set(),
            ))
        log.info(f"Refreshed: {len(self.monitors)} monitor(s)")
        for m in self.monitors:
            log.info(f"  {m.device_name}: {m.bounds.width}x{m.bounds.height}"
                     f"{' [PRIMARY]' if m.is_primary else ''}")

    def on_displays_changed(self, callback: Callable):
        """Register a callback for when display configuration changes."""
        self._on_displays_changed = callback

    def get_monitor_for_point(self, x: int, y: int) -> Optional[MonitorEntry]:
        """Return the monitor containing the given screen point."""
        for m in self.monitors:
            raw_monitors = get_all_monitors()
            for rm in raw_monitors:
                if rm.handle == m.handle and rm.contains_point(x, y):
                    return m
        return None

    def cleanup(self):
        """Stop observer threads and release resources."""
        self._running = False
        if self._observer_thread and self._observer_thread.is_alive():
            self._observer_thread.join(timeout=2)
