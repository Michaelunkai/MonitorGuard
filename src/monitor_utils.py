"""
Monitor enumeration and geometry utilities.
Uses Win32 API to discover all connected monitors and their bounds.
"""

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from typing import List, Optional

# Win32 constants
MONITOR_DEFAULTTONEAREST = 2
MONITOR_DEFAULTTOPRIMARY = 1
ENUM_CURRENT_SETTINGS = -1
DISPLAY_DEVICE_ACTIVE = 0x00000001


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class MONITORINFOEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", ctypes.c_wchar * 32),
    ]


MonitorEnumProc = ctypes.WINFUNCTYPE(
    ctypes.c_bool,
    wintypes.HMONITOR,
    wintypes.HDC,
    ctypes.POINTER(RECT),
    wintypes.LPARAM,
)


@dataclass
class MonitorInfo:
    """Information about a single monitor."""
    handle: int
    x: int
    y: int
    width: int
    height: int
    name: str
    is_primary: bool

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def center_x(self) -> int:
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        return self.y + self.height // 2

    def contains_point(self, px: int, py: int) -> bool:
        return self.x <= px < self.right and self.y <= py < self.bottom

    def clamp_rect(self, x: int, y: int, w: int, h: int) -> tuple:
        new_x = max(self.x, min(x, self.right - w))
        new_y = max(self.y, min(y, self.bottom - h))
        if w > self.width:
            new_x = self.x
        if h > self.height:
            new_y = self.y
        return new_x, new_y, w, h

    def __str__(self) -> str:
        p = " [PRIMARY]" if self.is_primary else ""
        return f"Monitor '{self.name}': {self.width}x{self.height} at ({self.x},{self.y}){p}"


def get_all_monitors() -> List[MonitorInfo]:
    """Enumerate all connected monitors."""
    monitors = []

    def callback(h_monitor, hdc, lprc_monitor, l_param):
        info = MONITORINFOEX()
        info.cbSize = ctypes.sizeof(MONITORINFOEX)
        if ctypes.windll.user32.GetMonitorInfoW(h_monitor, ctypes.byref(info)):
            is_primary = bool(info.dwFlags & 1)
            monitors.append(MonitorInfo(
                handle=h_monitor,
                x=info.rcMonitor.left,
                y=info.rcMonitor.top,
                width=info.rcMonitor.right - info.rcMonitor.left,
                height=info.rcMonitor.bottom - info.rcMonitor.top,
                name=info.szDevice,
                is_primary=is_primary,
            ))
        return True

    ctypes.windll.user32.EnumDisplayMonitors(None, None, MonitorEnumProc(callback), 0)
    return monitors


def get_monitor_from_point(x: int, y: int) -> Optional[MonitorInfo]:
    """Get the monitor containing the given point."""
    pt = wintypes.POINT(x, y)
    h = ctypes.windll.user32.MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST)
    if h:
        for m in get_all_monitors():
            if m.handle == h:
                return m
    return None


def get_monitor_for_window(hwnd: int) -> Optional[MonitorInfo]:
    """Get the monitor a window's center is on."""
    rect = RECT()
    if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        cx = (rect.left + rect.right) // 2
        cy = (rect.top + rect.bottom) // 2
        return get_monitor_from_point(cx, cy)
    return None
