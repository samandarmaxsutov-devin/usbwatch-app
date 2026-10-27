"""Generate the app icon (.ico) at runtime with no third-party libraries.

Draws a bold white "U" on a rounded blue tile using signed-distance shapes, so every
edge is anti-aliased. Each size is rendered natively (geometry snapped to whole pixels)
instead of scaled, which keeps the 16/24/32 px icons sharp. Writes a multi-size .ico
used for the window title-bar, taskbar and system-tray icon.

    python -m usbwatch.views.appicon assets\\usbwatch.ico   # regenerate the exe icon
"""
import math
import os
import struct
import sys
import zlib

from .. import config

_ICO = os.path.join(config.DATA, "usbwatch_icon_v3.ico")
_SIZES = (16, 20, 24, 32, 40, 48, 64, 256)

_TOP = (0x3B, 0x82, 0xF6)       # #3b82f6  gradient top (theme ACCENT)
_BOTTOM = (0x1D, 0x4E, 0xD8)    # #1d4ed8  gradient bottom
_WHITE = (0xFF, 0xFF, 0xFF)


def _clamp01(v):
    return 0.0 if v < 0 else 1.0 if v > 1 else v


def _rounded_square_sd(x, y, n, r):
    """Signed distance (pixels) to a rounded square filling 0..n."""
    h = n / 2.0
    qx = abs(x - h) - (h - r)
    qy = abs(y - h) - (h - r)
    out = math.hypot(max(qx, 0.0), max(qy, 0.0))
    return out + min(max(qx, qy), 0.0) - r


def _u_geometry(n):
    """Pixel-snapped geometry of the "U": (center x, half spacing, stroke, top, bowl y)."""
    stroke = max(2, round(n * 0.14))
    outer = round(n * 0.50)
    if (n - outer) % 2:                     # keep left/right edges on whole pixels
        outer += 1
    top = round(n * 0.22)
    bottom = n - round(n * 0.20)
    cx = n / 2.0
    a = (outer - stroke) / 2.0              # centerline offset of each bar
    bowl = bottom - outer / 2.0             # center of the lower half-circle
    return cx, a, stroke, top, bowl


def _u_sd(x, y, geo):
    """Signed distance to the "U": a stroked U-shaped centerline with flat top caps."""
    cx, a, stroke, top, bowl = geo
    dx = x - cx
    if y <= bowl:
        d = abs(abs(dx) - a)                # distance to the nearer vertical bar
    else:
        d = abs(math.hypot(dx, y - bowl) - a)
    return max(d - stroke / 2.0, top - y)


def _render(n):
    """Return rows (top-down) of (r, g, b, a) tuples for an n x n icon."""
    radius = n * 0.22
    geo = _u_geometry(n)
    rows = []
    for py in range(n):
        y = py + 0.5
        t = py / max(n - 1, 1)
        bg = tuple(round(_TOP[i] + (_BOTTOM[i] - _TOP[i]) * t) for i in range(3))
        row = []
        for px in range(n):
            x = px + 0.5
            tile = _clamp01(0.5 - _rounded_square_sd(x, y, n, radius))
            if tile <= 0:
                row.append((0, 0, 0, 0))
                continue
            glyph = _clamp01(0.5 - _u_sd(x, y, geo))
            rgb = tuple(round(bg[i] + (_WHITE[i] - bg[i]) * glyph) for i in range(3))
            row.append(rgb + (round(tile * 255),))
        rows.append(row)
    return rows


def _png(n, rows):
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in rows)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def _dib(n, rows):
    xor = b"".join(bytes((b, g, r, a)) for row in reversed(rows) for (r, g, b, a) in row)
    and_mask = b"\x00" * (((n + 31) // 32) * 4 * n)   # 32-bpp uses alpha; mask all-opaque
    header = struct.pack("<IiiHHIIiiII", 40, n, n * 2, 1, 32, 0, 0, 0, 0, 0, 0)
    return header + xor + and_mask


def _build_ico():
    images = []
    for n in _SIZES:
        rows = _render(n)
        images.append((n, _png(n, rows) if n >= 256 else _dib(n, rows)))
    out = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    for n, data in images:
        out += struct.pack("<BBBBHHII", n % 256, n % 256, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    return out + b"".join(data for _, data in images)


def ico_path():
    """Return a path to the generated .ico (written once), or None on failure."""
    try:
        if not os.path.exists(_ICO):
            with open(_ICO, "wb") as f:
                f.write(_build_ico())
        return _ICO
    except OSError:
        return None


def apply_window_icon(window):
    """Set the window's title-bar/taskbar icon (works around customtkinter's default)."""
    ico = ico_path()
    if not ico:
        return
    try:
        window.iconbitmap(ico)
        window.after(300, lambda: window.iconbitmap(ico))   # re-apply after ctk sets its own
    except Exception:
        pass


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "usbwatch.ico"
    with open(target, "wb") as f:
        f.write(_build_ico())
    print("wrote", target)
