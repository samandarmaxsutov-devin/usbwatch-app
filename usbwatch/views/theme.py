"""Colours, light/dark palettes and shared ttk styling.

IMPORTANT: ttk.Style() must only be called once a Tk root exists, otherwise Tkinter
creates a blank default "tk" window. So apply() only sets palette globals + the ctk
appearance; the ttk styling (style_tree) is invoked from a window's __init__.
"""
from tkinter import ttk

import customtkinter as ctk

from ..core import Observable
from ..services import settings_service

_PALETTES = {
    "dark": dict(BG="#16181d", PANEL="#1e2128", SIDE="#12141a", ACCENT="#3b82f6",
                 TEXT="#e5e7eb", MUTED="#9ca3af", HEAD="#272b34", HEAD_ACTIVE="#323744",
                 EVEN="#1e2128", ODD="#23272f", SEL="#3b82f6", SELFG="white", SCROLL="#2b303b",
                 BTN2="#2b303b", BTN2H="#374151", DANGER="#7f1d1d", DANGERH="#991b1b",
                 SIDE_HOVER="#242833", ACCENT_HOVER="#2f6fd6"),
    "light": dict(BG="#f4f5f7", PANEL="#ffffff", SIDE="#eceef1", ACCENT="#2563eb",
                  TEXT="#111827", MUTED="#6b7280", HEAD="#e5e7eb", HEAD_ACTIVE="#d8dbe0",
                  EVEN="#ffffff", ODD="#f3f4f6", SEL="#2563eb", SELFG="white", SCROLL="#c7ccd4",
                  BTN2="#e5e7eb", BTN2H="#d1d5db", DANGER="#dc2626", DANGERH="#b91c1c",
                  SIDE_HOVER="#dde1e6", ACCENT_HOVER="#1d4ed8"),
}

TAG_COLORS = {
    "Created": "#10b981", "Modified": "#d97706", "Deleted": "#ef4444",
    "Renamed/Moved": "#7c3aed", "Deleted (offline)": "#ea580c",
    "Blocked": "#dc2626", "Block failed": "#d97706", "Unblocked": "#0d9488",
    "Unblock failed": "#d97706", "Mounted": "#2563eb", "Unmounted": "#6b7280",
    "connected": "#059669", "disabled": "#dc2626", "allow": "#059669", "block": "#dc2626",
    "deleted": "#dc2626", "offline": "#ea580c",
}

# current palette (module globals; reassigned by apply())
BG = PANEL = SIDE = ACCENT = TEXT = MUTED = EVEN = ODD = ""
BTN2 = BTN2H = DANGER = DANGERH = SIDE_HOVER = ACCENT_HOVER = ""
_cur = _PALETTES["dark"]


def apply(m):
    """Set the active palette globals + ctk appearance. Does NOT touch ttk (no root needed)."""
    global _cur
    _cur = _PALETTES.get(m, _PALETTES["dark"])
    globals().update(_cur)
    try:
        ctk.set_appearance_mode("light" if m == "light" else "dark")
    except Exception:
        pass


def style_tree():
    """Apply ttk styling for the current palette. Call only after a Tk root exists."""
    p = _cur
    st = ttk.Style()
    st.theme_use("clam")
    st.configure("Treeview", background=p["PANEL"], fieldbackground=p["PANEL"], foreground=p["TEXT"],
                 rowheight=27, borderwidth=0, font=("Segoe UI", 10))
    st.configure("Treeview.Heading", background=p["HEAD"], foreground=p["TEXT"], relief="flat",
                 font=("Segoe UI", 10, "bold"), padding=(6, 6))
    st.map("Treeview", background=[("selected", p["SEL"])], foreground=[("selected", p["SELFG"])])
    st.map("Treeview.Heading", background=[("active", p["HEAD_ACTIVE"])])
    for bar in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        st.configure(bar, background=p["SCROLL"], troughcolor=p["PANEL"], bordercolor=p["PANEL"],
                     arrowcolor=p["MUTED"], lightcolor=p["SCROLL"], darkcolor=p["SCROLL"])


def set_mode(m):
    """Switch theme (palette + ttk) and notify so the main window rebuilds."""
    apply(m)
    style_tree()
    mode.set(m)


_startup = settings_service.load_cfg().get("appearance", "dark")
mode = Observable(_startup if _startup in _PALETTES else "dark")
apply(mode.value)
