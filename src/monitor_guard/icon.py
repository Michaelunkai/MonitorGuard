"""
Icon adapter — provides the icon-drawing functions expected by __main__.py,
wrapping the Pillow-based renderer from icon_renderer.
"""

import ctypes
import ctypes.wintypes as wintypes
import logging
import sys
import os

# Ensure MonitorGuard root is on path so we can import src.* as a package
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.icon_renderer import generate_icon

log = logging.getLogger("MonitorGuard.icon")


def draw_active_icon(size: int = 64):
    """Generate the green 'isolation active' shield icon."""
    return generate_icon(size, active=True)


def draw_standby_icon(size: int = 64):
    """Generate the amber 'standby / paused' shield icon."""
    return generate_icon(size, active=False)


def draw_conflict_icon(size: int = 64):
    """Generate the red 'conflict detected' shield icon."""
    from PIL import Image, ImageDraw

    rs = size * 2
    cx, cy = rs // 2, rs // 2

    img = Image.new("RGBA", (rs, rs), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Red conflict colors
    fill = (220, 38, 38, 255)         # red
    fill_light = (248, 113, 113, 200) # lighter red
    border = (153, 27, 27, 255)       # dark red
    check_color = (255, 255, 255, 240)

    s = rs * 0.38

    shield_pts = [
        (cx - s * 0.95, cy - s * 0.65),
        (cx + s * 0.95, cy - s * 0.65),
        (cx + s * 1.0,  cy - s * 0.20),
        (cx + s * 0.65, cy + s * 0.45),
        (cx,            cy + s * 1.05),
        (cx - s * 0.65, cy + s * 0.45),
        (cx - s * 1.0,  cy - s * 0.20),
    ]

    # Glow
    for i in range(3, 0, -1):
        glow_pts = [(x + (1 if x > cx else -1) * i * 0.8,
                     y + (1 if y > cy else -1) * i * 0.8) for x, y in shield_pts]
        draw.polygon(glow_pts, fill=(*fill[:3], 25 + i * 8))

    # Shield
    draw.polygon(shield_pts, fill=fill, outline=border)

    # Highlight
    highlight_pts = [
        (cx - s * 0.60, cy - s * 0.50),
        (cx + s * 0.10, cy - s * 0.50),
        (cx + s * 0.10, cy + s * 0.10),
        (cx - s * 0.60, cy - s * 0.10),
    ]
    draw.polygon(highlight_pts, fill=fill_light)

    # Exclamation mark
    lw = max(2, rs // 28)
    bar_top = (cx, cy - s * 0.40)
    bar_bot = (cx, cy + s * 0.05)
    draw.line([bar_top, bar_bot], fill=check_color, width=lw + 1)
    dot_y = cy + s * 0.30
    dr = max(2, rs // 32)
    draw.ellipse([cx - dr, dot_y - dr, cx + dr, dot_y + dr], fill=check_color)

    # Status dot (top-right)
    dot_r = max(3, rs // 16)
    dx = cx + int(s * 0.72)
    dy = cy - int(s * 0.55)
    draw.ellipse([dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r], fill=fill)

    img = img.resize((size, size), Image.LANCZOS)
    return img


def pil_to_hicon(img):
    """Convert a PIL Image to a Windows HICON handle for pystray."""
    try:
        # pystray on Windows can accept PIL images directly
        return img
    except Exception:
        return img
