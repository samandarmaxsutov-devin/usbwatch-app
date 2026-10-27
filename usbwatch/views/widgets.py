"""Reusable UI building blocks shared by the page views."""
import re
from tkinter import ttk

import customtkinter as ctk

from . import theme

_NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")


def header(parent, title):
    """Title row with a right-aligned tools frame (returned)."""
    h = ctk.CTkFrame(parent, fg_color="transparent")
    h.grid(row=0, column=0, sticky="ew", pady=(0, 14))
    ctk.CTkLabel(h, text=title, font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
    tools = ctk.CTkFrame(h, fg_color="transparent")
    tools.pack(side="right")
    return tools


def make_tree(parent, cols, widths, stretch=(), sortable=True):
    fr = ctk.CTkFrame(parent, fg_color=theme.PANEL, corner_radius=12)
    t = ttk.Treeview(fr, columns=cols, show="headings", selectmode="extended")
    t._base_head = {c: c for c in cols}            # heading text without sort arrow
    t._sort = {"col": None, "desc": False}
    for c, w in zip(cols, widths):
        if sortable:
            t.heading(c, text=c, anchor="w", command=lambda col=c: _sort(t, col))
        else:
            t.heading(c, text=c, anchor="w")
        t.column(c, width=w, minwidth=max(45, w // 2), anchor="w", stretch=c in stretch)
    vsb = ttk.Scrollbar(fr, orient="vertical", command=t.yview)
    hsb = ttk.Scrollbar(fr, orient="horizontal", command=t.xview)
    t.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    t.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
    vsb.grid(row=0, column=1, sticky="ns", pady=(8, 0), padx=(0, 6))
    hsb.grid(row=1, column=0, sticky="ew", padx=(8, 0), pady=(0, 6))
    fr.grid_columnconfigure(0, weight=1)
    fr.grid_rowconfigure(0, weight=1)
    t.tag_configure("evenrow", background=theme.EVEN)
    t.tag_configure("oddrow", background=theme.ODD)
    for tag, color in theme.TAG_COLORS.items():
        t.tag_configure(tag, foreground=color)
    return fr, t


def _restripe(tree):
    for i, k in enumerate(tree.get_children("")):
        tags = [x for x in tree.item(k, "tags") if x not in ("evenrow", "oddrow")]
        tags.insert(0, "evenrow" if i % 2 == 0 else "oddrow")
        tree.item(k, tags=tuple(tags))


def _sort(tree, col):
    s = tree._sort
    desc = not s["desc"] if s["col"] == col else False
    rows = [(tree.set(k, col), k) for k in tree.get_children("")]

    def key(item):
        v = item[0]
        return (0, float(v)) if _NUM_RE.match(v.strip()) else (1, v.lower())

    rows.sort(key=key, reverse=desc)
    for i, (_v, k) in enumerate(rows):
        tree.move(k, "", i)
    s["col"], s["desc"] = col, desc
    for c, base in tree._base_head.items():
        arrow = ("  ▾" if desc else "  ▴") if c == col else ""
        tree.heading(c, text=base + arrow)
    _restripe(tree)


def fill_tree(tree, rows):
    """rows: list of dicts {values, tag?, iid?}. Replaces the tree contents, with striping."""
    tree.delete(*tree.get_children())
    for i, r in enumerate(rows):
        tags = ["evenrow" if i % 2 == 0 else "oddrow"]
        if r.get("tag"):
            tags.append(r["tag"])
        tree.insert("", "end", iid=r.get("iid", str(i)), values=r["values"], tags=tuple(tags))
    if getattr(tree, "_sort", None) and tree._sort["col"] in tree["columns"]:
        _resort_current(tree)


def _resort_current(tree):
    col, desc = tree._sort["col"], tree._sort["desc"]
    rows = [(tree.set(k, col), k) for k in tree.get_children("")]

    def key(item):
        v = item[0]
        return (0, float(v)) if _NUM_RE.match(v.strip()) else (1, v.lower())

    rows.sort(key=key, reverse=desc)
    for i, (_v, k) in enumerate(rows):
        tree.move(k, "", i)
    _restripe(tree)


def card(parent, title):
    f = ctk.CTkFrame(parent, fg_color=theme.PANEL, corner_radius=12)
    v = ctk.CTkLabel(f, text="0", font=ctk.CTkFont(size=28, weight="bold"))
    v.pack(anchor="w", padx=18, pady=(14, 0))
    ctk.CTkLabel(f, text=title, text_color=theme.MUTED).pack(anchor="w", padx=18, pady=(0, 14))
    return f, v


def center(window, w, h):
    """Place a toplevel/window centred on the screen."""
    window.update_idletasks()
    sw, sh = window.winfo_screenwidth(), window.winfo_screenheight()
    window.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")


def ask_pw(parent, prompt):
    """Small modal password prompt, centred on screen. Returns the text or None."""
    from .. import config
    d = ctk.CTkToplevel(parent)
    d.title(config.APP)
    d.resizable(False, False)
    center(d, 360, 190)
    d.attributes("-topmost", True)
    res = {"v": None}
    ctk.CTkLabel(d, text=prompt, justify="center").pack(pady=(20, 8))
    e = ctk.CTkEntry(d, show="•", width=270, height=36)
    e.pack()

    def ok():
        res["v"] = e.get()
        d.destroy()

    row = ctk.CTkFrame(d, fg_color="transparent")
    row.pack(pady=16)
    ctk.CTkButton(row, text="OK", width=110, command=ok).pack(side="left", padx=6)
    ctk.CTkButton(row, text="Cancel", width=110, fg_color=theme.BTN2, hover_color=theme.BTN2H,
                  text_color=theme.TEXT, command=d.destroy).pack(side="left", padx=6)
    d.bind("<Return>", lambda _e: ok())
    d.bind("<Escape>", lambda _e: d.destroy())
    d.after(250, e.focus)
    d.wait_visibility()
    d.grab_set()
    parent.wait_window(d)
    return res["v"]
