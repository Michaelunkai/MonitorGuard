"""
Isolation adapter — wraps the core IsolationEngine from isolation_engine
with a state-change/callback interface expected by __main__.py.
"""

import logging
import sys
import os
from typing import Optional, Callable

# Ensure MonitorGuard root is on path so we can import src.* as a package
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.isolation_engine import IsolationEngine as _CoreEngine

log = logging.getLogger("MonitorGuard.isolation")


class IsolationEngine:
    """High-level isolation controller wrapping the core engine."""

    def __init__(self, display_manager=None):
        self._core = _CoreEngine()
        self._active = False
        self._on_state_changed: Optional[Callable[[bool], None]] = None
        self._on_conflict: Optional[Callable[[str], None]] = None
        self._display = display_manager

        # Wire the core engine's callback
        self._core.set_state_change_callback(self._on_core_state_change)

    def _on_core_state_change(self, enabled: bool):
        """Forward state changes from the core engine."""
        self._active = enabled
        if self._on_state_changed:
            self._on_state_changed(enabled)

    @property
    def active(self) -> bool:
        return self._active

    def on_state_changed(self, callback: Callable[[bool], None]):
        """Register a callback for when isolation state changes."""
        self._on_state_changed = callback

    def on_conflict(self, callback: Callable[[str], None]):
        """Register a callback for conflict detection."""
        self._on_conflict = callback

    def toggle(self):
        """Toggle isolation on/off."""
        self._core.toggle()
        self._active = self._core.enabled
        log.info(f"Isolation toggled: {'ACTIVE' if self._active else 'INACTIVE'}")

    def enable(self):
        """Enable isolation."""
        self._core.enable()
        self._active = True

    def disable(self):
        """Disable isolation."""
        self._core.disable()
        self._active = False

    def cleanup(self):
        """Stop the core engine and remove all hooks."""
        self._core.stop()
        self._active = False
        log.info("Isolation engine cleaned up")
