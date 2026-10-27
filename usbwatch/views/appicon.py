"""Generate the app icon (.ico) at runtime with no third-party libraries.

Draws a 32x32 white USB-flash-drive silhouette on a rounded blue tile, writes it as a
32-bpp .ico. Used for both the window title-bar icon and the system-tray icon.
"""
import os
import struct

from .. import config

_ICO = os.path.join(config.DATA, "usbwatch_icon_v2.ico")
_SIZE = 32

_BLUE = (0xF6, 0x82, 0x3B, 0xFF)      # #3b82f6 as B,G,R,A
_WHITE = (0xFF, 0xFF, 0xFF, 0xFF)
_TRANS = (0, 0, 0, 0)


def _pixels():
    n = _SIZE
    px = [[_BLUE for _ in range(n)] for _ in range(n)]

    def put(x, y, color):
        if 0 <= x < n and 0 <= y < n:
            px[y][x] = color

    def rect(x0, x1, y0, y1, color):
        for y in range(y0, y1):
            for x in range(x0, x1):
                put(x, y, color)

    def disc(cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    put(x, y, color)

    def line(x0, y0, x1, y1, color, wt=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx - dy
        while True:
            for oy in range(wt):
                for ox in range(wt):
                    put(x0 + ox, y0 + oy, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    # rounded corners (transparent)
    r = 6
    corners = [(r, r), (n - 1 - r, r), (r, n - 1 - r), (n - 1 - r, n - 1 - r)]
    for y in range(n):
        for x in range(n):
            if ((x < r or x > n - 1 - r) and (y < r or y > n - 1 - r)):
                cx, cy = min(corners, key=lambda c: (c[0] - x) ** 2 + (c[1] - y) ** 2)
                if (x - cx) ** 2 + (y - cy) ** 2 > r * r:
                    put(x, y, _TRANS)

    # white USB "trident" symbol (horizontal): circle + shaft + square prong + arrow prong
    W = _WHITE
    disc(8, 16, 3, W)                 # left round knob
    rect(8, 25, 15, 18, W)            # main shaft (center prong to the right tip)
    line(15, 16, 21, 9, W, 2)         # upper branch
    rect(19, 25, 6, 11, W)            # square end on the upper prong
    line(14, 16, 21, 23, W, 2)        # lower branch
    # arrowhead (triangle) on the lower prong, pointing down-right
    for i in range(6):
        rect(20 - i, 26, 18 + i, 19 + i, W)
    return px


def _build_ico():
    n = _SIZE
    px = _pixels()
    xor = bytearray()
    for y in range(n - 1, -1, -1):     # bottom-up
        for x in range(n):
            xor += bytes(px[y][x])
    and_mask = b"\x00" * (4 * n)        # 32-bpp uses alpha; AND mask all-opaque
    dib = struct.pack("<IiiHHIIiiII", 40, n, n * 2, 1, 32, 0, 0, 0, 0, 0, 0) + bytes(xor) + and_mask
    icondir = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", n, n, 0, 0, 1, 32, len(dib), 22)
    return icondir + entry + dib


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
