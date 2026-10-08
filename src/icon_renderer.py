"""
Dynamic tray icon renderer using Pillow.
Generates a clean shield icon for system tray with state-dependent coloring.
Optimized for 16x16, 20x20, 24x24, 32x32, 48x48 tray sizes.
"""

from PIL import Image, ImageDraw
import math


def _lerp(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def generate_icon(size=64, active=True, frame=0):
    """Generate a clean shield tray icon with proper transparency.

    Args:
        size: Target icon size in pixels.
        active: True=green shield (active), False=amber shield (paused).
        frame: Animation frame for subtle pulse.

    Returns:
        PIL Image in RGBA mode with transparent background.
    """
    # Render at 2x for anti-aliasing, then downsample
    rs = size * 2
    cx, cy = rs // 2, rs // 2

    img = Image.new("RGBA", (rs, rs), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Colors
    if active:
        fill = (34, 197, 94, 255)        # emerald
        fill_light = (74, 222, 128, 200)  # lighter emerald
        border = (22, 101, 52, 255)       # dark green
        check_color = (255, 255, 255, 240)
        dot_color = (220, 38, 38, 255)    # red status dot
    else:
        fill = (245, 158, 11, 255)        # amber
        fill_light = (252, 211, 77, 200)  # lighter amber
        border = (180, 83, 9, 255)        # dark amber
        check_color = (255, 255, 255, 240)
        dot_color = (107, 114, 128, 255)  # gray status dot

    # Subtle pulse on size
    pulse = 1.0 + 0.015 * math.sin(frame * 0.4)
    s = rs * 0.38 * pulse  # half-size of shield

    # ── Shield body ──
    # Modern shield: flat top, curved sides, pointed bottom
    shield_pts = [
        (cx - s * 0.95, cy - s * 0.65),   # top-left
        (cx + s * 0.95, cy - s * 0.65),   # top-right
        (cx + s * 1.0,  cy - s * 0.20),   # right upper
        (cx + s * 0.65, cy + s * 0.45),   # right mid
        (cx,            cy + s * 1.05),    # bottom point
        (cx - s * 0.65, cy + s * 0.45),   # left mid
        (cx - s * 1.0,  cy - s * 0.20),   # left upper
    ]

    # Subtle glow behind shield
    for i in range(3, 0, -1):
        glow_pts = [(x + (1 if x > cx else -1) * i * 0.8,
                     y + (1 if y > cy else -1) * i * 0.8) for x, y in shield_pts]
        draw.polygon(glow_pts, fill=(*fill[:3], 25 + i * 8))

    # Main shield fill
    draw.polygon(shield_pts, fill=fill, outline=border)

    # Inner gradient highlight (top-left shine)
    highlight_pts = [
        (cx - s * 0.60, cy - s * 0.50),
        (cx + s * 0.10, cy - s * 0.50),
        (cx + s * 0.10, cy + s * 0.10),
        (cx - s * 0.60, cy - s * 0.10),
    ]
    draw.polygon(highlight_pts, fill=fill_light)

    # ── Status mark ──
    lw = max(2, rs // 28)  # line width scales with size
    if active:
        # Checkmark
        check_pts = [
            (cx - s * 0.50, cy - s * 0.05),
            (cx - s * 0.15, cy + s * 0.35),
            (cx + s * 0.55, cy - s * 0.30),
        ]
        draw.line(check_pts, fill=check_color, width=lw, joint="curve")
    else:
        # X mark
        off = s * 0.28
        draw.line([(cx - off, cy - off), (cx + off, cy + off)],
                  fill=check_color, width=lw)
        draw.line([(cx + off, cy - off), (cx - off, cy + off)],
                  fill=check_color, width=lw)

    # ── Status dot (top-right) ──
    dr = max(3, rs // 16)
    dx = cx + int(s * 0.72)
    dy = cy - int(s * 0.55)
    draw.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], fill=dot_color)

    # Downsample with LANCZOS for crisp small sizes
    img = img.resize((size, size), Image.LANCZOS)
    return img


def generate_icon_set(size=64):
    """Generate both active and inactive icons."""
    return {
        "active": generate_icon(size, active=True),
        "inactive": generate_icon(size, active=False),
    }
