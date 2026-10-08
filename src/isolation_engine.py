"""
Core isolation engine — enforces that each window stays confined to its monitor.
Blocks cross-monitor focus theft and input routing.
"""

import ctypes
import ctypes.wintypes as wt
import threading
import time
import logging
from typing import Dict, Optional, Set, Callable
from collections import defaultdict

from .monitor_utils import (
    get_all_monitors, get_monitor_for_window, MonitorInfo, RECT,
)

log = logging.getLogger("MonitorGuard.isolation")

# Win32 constants
EVENT_SYSTEM_FOREGROUND     = 0x0003
EVENT_OBJECT_LOCATIONCHANGE = 0x800B
WINEVENT_OUTOFCONTEXT       = 0x0000
WINEVENT_SKIPOWNTHREAD      = 0x0001

WH_MOUSE_LL    = 14
WM_LBUTTONDOWN = 0x0201
WM_RBUTTONDOWN = 0x0204
WM_MBUTTONDOWN = 0x0207

GW_OWNER       = 4
WS_EX_TOOLWINDOW = 0x00000080
GWL_EXSTYLE    = -20

SWP_NOMOVE     = 0x0002
SWP_NOSIZE     = 0x0001
SWP_NOZORDER   = 0x0004
SWP_NOACTIVATE = 0x0010

WM_QUIT = 0x0012


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wt.POINT),
        ("mouseData", wt.DWORD),
        ("flags", wt.DWORD),
        ("time", wt.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class IsolationEngine:
    """Per-monitor window isolation on Windows."""

    def __init__(self):
        self._enabled = False
        self._lock = threading.RLock()
        self._window_monitor: Dict[int, int] = {}
        self._skip_hwnds: Set[int] = set()
        self._on_state_change: Optional[Callable[[bool], None]] = None

        # Hook handles
        self._loc_hook = None
        self._fg_hook = None
        self._mouse_hook = None
        self._loc_callback = None
        self._fg_callback = None
        self._mouse_callback = None
        self._hook_thread_id = 0

        self._running = False
        self._hook_thread: Optional[threading.Thread] = None
        self._enforcement_thread: Optional[threading.Thread] = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_state_change_callback(self, cb):
        self._on_state_change = cb

    def enable(self):
        with self._lock:
            if self._enabled:
                return
            log.info("Enabling monitor isolation")
            self._build_window_map()
            self._enabled = True
            self._install_hooks()
            if self._on_state_change:
                self._on_state_change(True)

    def disable(self):
        with self._lock:
            if not self._enabled:
                return
            log.info("Disabling monitor isolation")
            self._enabled = False
            self._remove_hooks()
            if self._on_state_change:
                self._on_state_change(False)

    def toggle(self):
        if self._enabled:
            self.disable()
        else:
            self.enable()

    def start(self):
        """Start hook thread and enforcement loop."""
        if self._running:
            return
        self._running = True
        self._hook_thread = threading.Thread(target=self._hook_loop, daemon=True, name="MG-Hooks")
        self._hook_thread.start()
        self._enforcement_thread = threading.Thread(target=self._enforcement_loop, daemon=True, name="MG-Enforce")
        self._enforcement_thread.start()
        log.info("Isolation engine started")

    def stop(self):
        self._running = False
        self.disable()
        if self._hook_thread and self._hook_thread.is_alive():
            try:
                ctypes.windll.user32.PostThreadMessageW(self._hook_thread_id, WM_QUIT, 0, 0)
            except Exception:
                pass
            self._hook_thread.join(timeout=3)
        self._hook_thread = None
        self._enforcement_thread = None
        log.info("Isolation engine stopped")

    def add_skip_window(self, hwnd: int):
        self._skip_hwnds.add(hwnd)

    def get_window_count_per_monitor(self) -> Dict[str, int]:
        result: Dict[str, int] = defaultdict(int)
        if not self._enabled:
            return dict(result)
        monitors = {m.handle: m for m in get_all_monitors()}
        for hwnd, mon_handle in self._window_monitor.items():
            mon = monitors.get(mon_handle)
            if mon:
                result[mon.name] += 1
        return dict(result)

    # ── Window mapping ────────────────────────────────────────────────

    def _is_window_valid(self, hwnd: int) -> bool:
        if not hwnd:
            return False
        if hwnd in self._skip_hwnds:
            return False
        if not ctypes.windll.user32.IsWindowVisible(hwnd):
            return False
        ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if ex_style & WS_EX_TOOLWINDOW:
            return False
        if ctypes.windll.user32.GetWindow(hwnd, GW_OWNER):
            return False
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return False
        return True

    def _enum_managed_windows(self) -> list:
        windows = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
        def enum_callback(hwnd, lparam):
            if self._is_window_valid(hwnd):
                windows.append(hwnd)
            return True

        ctypes.windll.user32.EnumWindows(enum_callback, 0)
        return windows

    def _build_window_map(self):
        self._window_monitor.clear()
        for hwnd in self._enum_managed_windows():
            mon = get_monitor_for_window(hwnd)
            if mon:
                self._window_monitor[hwnd] = mon.handle

    def _isolate_window(self, hwnd: int):
        if hwnd not in self._window_monitor:
            return
        mon_handle = self._window_monitor[hwnd]
        monitors = {m.handle: m for m in get_all_monitors()}
        mon = monitors.get(mon_handle)
        if not mon:
            return
        rect = RECT()
        if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return
        win_w = rect.right - rect.left
        win_h = rect.bottom - rect.top
        cx = (rect.left + rect.right) // 2
        cy = (rect.top + rect.bottom) // 2
        if not mon.contains_point(cx, cy):
            new_x, new_y, _, _ = mon.clamp_rect(rect.left, rect.top, win_w, win_h)
            log.debug(f"Clamping hwnd={hwnd} to ({new_x},{new_y}) on monitor {mon.name}")
            ctypes.windll.user32.SetWindowPos(
                hwnd, 0, new_x, new_y, 0, 0,
                SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE,
            )

    def _reassign_window(self, hwnd: int):
        mon = get_monitor_for_window(hwnd)
        if mon:
            self._window_monitor[hwnd] = mon.handle

    # ── Hook thread ───────────────────────────────────────────────────

    def _hook_loop(self):
        self._hook_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        log.debug(f"Hook thread running, thread_id={self._hook_thread_id}")
        msg = wt.MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
        log.debug("Hook thread message loop ended")

    def _install_hooks(self):
        if self._loc_hook:
            return

        WINEVENTPROC = ctypes.WINFUNCTYPE(
            None, wt.HANDLE, wt.DWORD, wt.HWND, wt.LONG, wt.LONG, wt.DWORD, wt.DWORD
        )
        HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wt.WPARAM, wt.LPARAM)

        # Location-change hook
        self._loc_callback = WINEVENTPROC(self._on_location_change)
        self._loc_hook = ctypes.windll.user32.SetWinEventHook(
            EVENT_OBJECT_LOCATIONCHANGE, EVENT_OBJECT_LOCATIONCHANGE,
            None, self._loc_callback, 0, 0,
            WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNTHREAD,
        )

        # Foreground hook
        self._fg_callback = WINEVENTPROC(self._on_foreground)
        self._fg_hook = ctypes.windll.user32.SetWinEventHook(
            EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND,
            None, self._fg_callback, 0, 0,
            WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNTHREAD,
        )

        # Low-level mouse hook — with fallback for compatibility
        self._mouse_callback = HOOKPROC(self._on_mouse_ll)
        h_mod = ctypes.windll.kernel32.GetModuleHandleW(None)
        if h_mod:
            self._mouse_hook = ctypes.windll.user32.SetWindowsHookExW(
                WH_MOUSE_LL, self._mouse_callback, h_mod, 0,
            )
        if not self._mouse_hook:
            try:
                h_user32 = ctypes.windll.kernel32.GetModuleHandleW("user32.dll")
                if h_user32:
                    self._mouse_hook = ctypes.windll.user32.SetWindowsHookExW(
                        WH_MOUSE_LL, self._mouse_callback, h_user32, 0,
                    )
            except Exception:
                pass
        if not self._mouse_hook:
            log.warning("Mouse hook unavailable; isolation enforced via window confinement + focus hooks")
        else:
            log.info("Mouse hook installed — full cross-monitor input blocking active")

        log.info("Hooks installed: loc=%s fg=%s mouse=%s",
                 bool(self._loc_hook), bool(self._fg_hook), bool(self._mouse_hook))

    def _remove_hooks(self):
        if self._loc_hook:
            ctypes.windll.user32.UnhookWinEvent(self._loc_hook)
            self._loc_hook = None
        if self._fg_hook:
            ctypes.windll.user32.UnhookWinEvent(self._fg_hook)
            self._fg_hook = None
        if self._mouse_hook:
            ctypes.windll.user32.UnhookWindowsHookEx(self._mouse_hook)
            self._mouse_hook = None
        log.info("Hooks removed")

    # ── Hook callbacks ────────────────────────────────────────────────

    def _on_location_change(self, h_event, event, hwnd, id_object, id_child, dw_thread, ms_time):
        if not self._enabled or not hwnd or not self._is_window_valid(hwnd):
            return
        try:
            if hwnd not in self._window_monitor:
                mon = get_monitor_for_window(hwnd)
                if mon:
                    self._window_monitor[hwnd] = mon.handle
                return
            self._reassign_window(hwnd)
            self._isolate_window(hwnd)
        except Exception as e:
            log.debug(f"Location hook error: {e}")

    def _on_foreground(self, h_event, event, hwnd, id_object, id_child, dw_thread, ms_time):
        if not self._enabled or not hwnd or not self._is_window_valid(hwnd):
            return
        try:
            if hwnd not in self._window_monitor:
                mon = get_monitor_for_window(hwnd)
                if mon:
                    self._window_monitor[hwnd] = mon.handle
            self._reassign_window(hwnd)
        except Exception as e:
            log.debug(f"Foreground hook error: {e}")

    def _on_mouse_ll(self, n_code, w_param, l_param):
        if not self._enabled or n_code < 0:
            return ctypes.windll.user32.CallNextHookEx(self._mouse_hook, n_code, w_param, l_param)
        try:
            hs = MSLLHOOKSTRUCT.from_address(l_param)
            cursor_x, cursor_y = hs.pt.x, hs.pt.y
            cursor_mon = None
            for m in get_all_monitors():
                if m.contains_point(cursor_x, cursor_y):
                    cursor_mon = m
                    break
            if not cursor_mon:
                return ctypes.windll.user32.CallNextHookEx(self._mouse_hook, n_code, w_param, l_param)

            fg_hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not fg_hwnd:
                return ctypes.windll.user32.CallNextHookEx(self._mouse_hook, n_code, w_param, l_param)

            fg_mon = get_monitor_for_window(fg_hwnd)
            if not fg_mon:
                return ctypes.windll.user32.CallNextHookEx(self._mouse_hook, n_code, w_param, l_param)

            if cursor_mon.handle != fg_mon.handle and w_param in (WM_LBUTTONDOWN, WM_RBUTTONDOWN, WM_MBUTTONDOWN):
                log.debug(f"Blocked cross-monitor click at ({cursor_x},{cursor_y})")
                return 1  # Block
        except Exception as e:
            log.debug(f"Mouse hook error: {e}")

        return ctypes.windll.user32.CallNextHookEx(self._mouse_hook, n_code, w_param, l_param)

    # ── Periodic enforcement ──────────────────────────────────────────

    def _enforcement_loop(self):
        while self._running:
            time.sleep(0.5)
            if not self._enabled:
                continue
            try:
                self.enforcement_tick()
            except Exception as e:
                log.debug(f"Enforcement error: {e}")

    def enforcement_tick(self):
        if not self._enabled:
            return
        # Remove dead windows
        for hwnd in list(self._window_monitor.keys()):
            if not ctypes.windll.user32.IsWindow(hwnd) or not self._is_window_valid(hwnd):
                self._window_monitor.pop(hwnd, None)
                continue
            self._reassign_window(hwnd)
            self._isolate_window(hwnd)
        # Discover new windows
        for hwnd in self._enum_managed_windows():
            if hwnd not in self._window_monitor:
                mon = get_monitor_for_window(hwnd)
                if mon:
                    self._window_monitor[hwnd] = mon.handle
                    self._isolate_window(hwnd)
