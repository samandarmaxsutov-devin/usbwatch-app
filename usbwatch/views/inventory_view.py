"""All-USB inventory view (USBDeview-style): rich actions + details popup."""
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from .. import config
from . import export_util, theme, widgets
from .base_view import BaseView

_COL_KEYS = ("col.name", "col.description", "col.type", "col.connected", "col.disabled",
             "col.serial", "col.vid", "col.pid", "col.class", "col.service", "col.vendor",
             "col.first_install", "col.last_connect", "col.last_disconnect", "col.instance_id")
_COL_WIDTHS = (190, 190, 120, 80, 70, 150, 55, 55, 110, 110, 150, 135, 135, 135, 260)


class InventoryView(BaseView):
    def build(self):
        self.vm = self.shell.inventory_vm
        self._loaded = False
        p = self
        p.grid_rowconfigure(2, weight=1)

        tools = widgets.header(p, self.t("nav.all"))
        dark = {"fg_color": theme.BTN2, "hover_color": theme.BTN2H, "text_color": theme.TEXT}
        ctk.CTkButton(tools, text=self.t("btn.refresh"), width=90, command=self.vm.refresh).pack(side="left", padx=3)
        ctk.CTkButton(tools, text=self.t("btn.enable"), width=78,
                      command=lambda: self._set_enabled(True), **dark).pack(side="left", padx=3)
        ctk.CTkButton(tools, text=self.t("btn.disable"), width=85, fg_color=theme.DANGER,
                      hover_color=theme.DANGERH, command=lambda: self._set_enabled(False)).pack(side="left", padx=3)
        ctk.CTkButton(tools, text=self.t("btn.regedit"), width=130,
                      command=self._regedit, **dark).pack(side="left", padx=3)
        ctk.CTkButton(tools, text=self.t("btn.export"), width=90,
                      command=lambda: export_util.export_tree(self, self.tree, "USB Devices"),
                      **dark).pack(side="left", padx=3)

        bar = ctk.CTkFrame(p, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.search = ctk.CTkEntry(bar, placeholder_text=self.t("all.search_ph"), width=340)
        self.search.pack(side="left")
        self.search.bind("<KeyRelease>", lambda _e: self.vm.set_search(self.search.get()))
        self.status = ctk.CTkLabel(bar, text="", text_color=theme.MUTED)
        self.status.pack(side="right")

        cols = tuple(self.t(k) for k in _COL_KEYS)
        fr, self.tree = widgets.make_tree(p, cols, _COL_WIDTHS)
        fr.grid(row=2, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", lambda _e: self._details())
        self.tree.bind("<Button-3>", self._popup)
        self._menu = self._build_menu()

        self.bind_obs(self.vm.rows, lambda rows: widgets.fill_tree(self.tree, rows))
        self.bind_obs(self.vm.status, lambda s: self.status.configure(text=s))
        self.bind_obs(self.vm.loading,
                      lambda b: self.status.configure(text=self.t("common.loading")) if b else None)

    def on_show(self):
        if not self._loaded:
            self._loaded = True
            self.vm.refresh()

    # ---- context menu ----
    def _build_menu(self):
        m = tk.Menu(self, tearoff=0, bg=theme.PANEL, fg=theme.TEXT,
                    activebackground=theme.ACCENT, activeforeground="white", bd=0)
        m.add_command(label=self.t("menu.properties"), command=self._details)
        m.add_command(label=self.t("menu.copy"), command=self._copy)
        m.add_separator()
        m.add_command(label=self.t("btn.regedit"), command=self._regedit)
        m.add_command(label=self.t("btn.enable"), command=lambda: self._set_enabled(True))
        m.add_command(label=self.t("btn.disable"), command=lambda: self._set_enabled(False))
        m.add_separator()
        m.add_command(label=self.t("menu.uninstall"), command=self._uninstall)
        return m

    def _popup(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            try:
                self._menu.tk_popup(event.x_root, event.y_root)
            finally:
                self._menu.grab_release()

    # ---- actions ----
    def _sel(self):
        s = self.tree.selection()
        return s[0] if s else None

    def _set_enabled(self, enable):
        iid = self._sel()
        if not iid:
            return messagebox.showinfo(config.APP, self.t("dlg.select_device"))
        err = self.vm.set_enabled(iid, enable)
        if err:
            messagebox.showwarning(config.APP, err)

    def _regedit(self):
        iid = self._sel()
        if not iid:
            return messagebox.showinfo(config.APP, self.t("dlg.select_device"))
        if not self.vm.open_regedit(iid):
            messagebox.showwarning(config.APP, self.t("dlg.regedit_failed"))

    def _uninstall(self):
        iid = self._sel()
        if not iid:
            return messagebox.showinfo(config.APP, self.t("dlg.select_device"))
        d = self.vm.device_for(iid)
        if not messagebox.askyesno(config.APP, self.t("dlg.uninstall_confirm", d.name if d else "")):
            return
        err = self.vm.uninstall(iid)
        if err:
            messagebox.showwarning(config.APP, err)

    def _copy(self):
        iid = self._sel()
        if not iid:
            return
        values = self.tree.item(iid)["values"]
        self.clipboard_clear()
        self.clipboard_append("\t".join(str(v) for v in values))
        self.status.configure(text=self.t("dlg.copied"))

    def _details(self):
        iid = self._sel()
        if not iid:
            return
        rows = self.vm.detail_rows(iid)
        if not rows:
            return
        DetailsDialog(self, rows)


class DetailsDialog(ctk.CTkToplevel):
    def __init__(self, parent, rows):
        super().__init__(parent)
        from ..i18n import t
        self.title(t("dlg.details_title"))
        self.configure(fg_color=theme.BG)
        widgets.center(self, 560, 520)
        self.attributes("-topmost", True)
        self._text = "\n".join(f"{t(k)}\t{v}" for k, v in rows)

        ctk.CTkLabel(self, text=t("dlg.details_title"), font=ctk.CTkFont(size=18, weight="bold")
                     ).pack(anchor="w", padx=20, pady=(16, 8))
        sf = ctk.CTkScrollableFrame(self, fg_color=theme.PANEL)
        sf.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        sf.grid_columnconfigure(1, weight=1)
        for i, (key, value) in enumerate(rows):
            ctk.CTkLabel(sf, text=t(key), text_color=theme.MUTED, anchor="w", width=160,
                         justify="left").grid(row=i, column=0, sticky="w", padx=(10, 12), pady=3)
            e = ctk.CTkEntry(sf, fg_color=theme.BG, border_width=0)
            e.insert(0, str(value))
            e.configure(state="readonly")
            e.grid(row=i, column=1, sticky="ew", padx=(0, 10), pady=3)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkButton(bar, text=t("menu.copy"), width=130, fg_color=theme.BTN2,
                      hover_color=theme.BTN2H, text_color=theme.TEXT, command=self._copy_all).pack(side="left")
        ctk.CTkButton(bar, text="OK", width=110, command=self.destroy).pack(side="right")
        self.bind("<Escape>", lambda _e: self.destroy())
        self.after(120, self.lift)

    def _copy_all(self):
        self.clipboard_clear()
        self.clipboard_append(self._text)
