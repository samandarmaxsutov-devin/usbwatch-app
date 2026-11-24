"""Access Control view: an on/off switch and one table of USB storage devices, each either
Allowed or Blocked. While it is on, devices not on the Allowed list are always blocked."""
from tkinter import messagebox

import customtkinter as ctk

from .. import config
from ..services import settings_service
from ..viewmodels import access_vm
from . import theme, widgets
from .base_view import BaseView


class AccessView(BaseView):
    def build(self):
        self.vm = self.shell.access_vm
        p = self
        p.grid_rowconfigure(4, weight=1)

        tools = widgets.header(p, self.t("nav.access"))
        ctk.CTkButton(tools, text=self.t("access.add_manual"), width=190, height=34,
                      fg_color=theme.BTN2, hover_color=theme.BTN2H, text_color=theme.TEXT,
                      command=self._add_manual).pack(side="right")

        self._build_banner(p)
        self._build_stats(p)
        self._build_toolbar(p)

        cols = tuple(self.t(k) for k in access_vm.COLUMNS)
        fr, self.tree = widgets.make_tree(p, cols, (170, 300, 230, 190, 160), stretch=(cols[1],))
        fr.grid(row=4, column=0, sticky="nsew")

        self.bind_obs(self.vm.rows, lambda _r: self._refill())
        self.bind_obs(self.vm.filter, self._show_filter)
        self.bind_obs(self.vm.counts, self._show_counts)
        self.bind_obs(self.vm.is_admin, self._show_admin)
        self.bind_obs(self.vm.enforce_on, self._show_enforce)

    def on_show(self):
        self.vm.reload()

    # ---- layout pieces ----
    def _build_banner(self, p):
        box = ctk.CTkFrame(p, fg_color=theme.PANEL, corner_radius=12)
        box.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        box.grid_columnconfigure(1, weight=1)
        self.strip = ctk.CTkFrame(box, width=5, height=10, fg_color=theme.ACCENT, corner_radius=3)
        self.strip.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(10, 14), pady=12)
        self.rule_title = ctk.CTkLabel(box, font=ctk.CTkFont(size=15, weight="bold"), anchor="w")
        self.rule_title.grid(row=0, column=1, sticky="ew", pady=(12, 0), padx=(0, 16))
        self.rule_text = ctk.CTkLabel(box, text_color=theme.MUTED, anchor="w", justify="left",
                                      wraplength=640)
        self.rule_text.grid(row=1, column=1, sticky="ew", pady=(2, 12), padx=(0, 16))
        # wrap the text to the space actually left of the switch/badge column
        # (ctk multiplies wraplength by the DPI scaling, so divide it back out)
        self.rule_text.bind("<Configure>", lambda e: self.rule_text.configure(
            wraplength=max(300, e.width - 8) / ctk.ScalingTracker.get_widget_scaling(self.rule_text)))
        self.enforce_var = ctk.BooleanVar(value=self.vm.enforce_on.value)
        ctk.CTkSwitch(box, text=self.t("access.enforce"), variable=self.enforce_var,
                      font=ctk.CTkFont(size=13, weight="bold"), progress_color=theme.SUCCESS_BTN,
                      command=self._toggle_enforce).grid(row=0, column=2, sticky="e", padx=(0, 18), pady=(12, 0))
        self.admin_lbl = ctk.CTkLabel(box, text="  " + self.t("access.need_admin") + "  ",
                                      fg_color=theme.DANGER, text_color="white", corner_radius=6,
                                      font=ctk.CTkFont(size=12, weight="bold"))

    def _build_stats(self, p):
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        self.stat = {}
        for i, (key, label, color) in enumerate((
                ("allow", "access.stat_allowed", theme.SUCCESS),
                ("block", "access.stat_blocked", theme.DANGER_TEXT),
                ("connected", "access.stat_connected", theme.ACCENT))):
            row.grid_columnconfigure(i, weight=1, uniform="stat")
            f, v = widgets.card(row, self.t(label))
            v.configure(text_color=color)
            f.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 12, 0))
            self.stat[key] = v
            if key == "block":
                self.block_stat_lbl = f.winfo_children()[1]     # card title label

    def _build_toolbar(self, p):
        bar = ctk.CTkFrame(p, fg_color="transparent")
        bar.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self._filter_label = {"all": self.t("access.filter_all"), "allow": self.t("access.allowed"),
                              "block": self.t("access.blocked")}
        self.filter_btn = ctk.CTkSegmentedButton(
            bar, values=list(self._filter_label.values()), height=34,
            command=lambda v: self.vm.set_filter(
                next(k for k, lbl in self._filter_label.items() if lbl == v)),
            selected_color=theme.ACCENT, selected_hover_color=theme.ACCENT_HOVER,
            unselected_color=theme.BTN2, unselected_hover_color=theme.BTN2H, text_color=theme.TEXT)
        self.filter_btn.pack(side="left")
        ctk.CTkButton(bar, text=self.t("access.do_block"), width=150, height=34,
                      fg_color=theme.DANGER, hover_color=theme.DANGERH,
                      command=lambda: self._set(False)).pack(side="right")
        ctk.CTkButton(bar, text=self.t("access.do_allow"), width=150, height=34,
                      fg_color=theme.SUCCESS_BTN, hover_color=theme.SUCCESS_BTNH,
                      command=lambda: self._set(True)).pack(side="right", padx=(0, 10))

    # ---- observers ----
    def _refill(self):
        widgets.fill_tree(self.tree, self.vm.visible_rows())

    def _show_filter(self, f):
        self.filter_btn.set(self._filter_label.get(f, self._filter_label["all"]))
        self._refill()

    def _show_counts(self, c):
        for k, v in self.stat.items():
            v.configure(text=str(c.get(k, 0)))

    def _show_admin(self, admin):
        if admin:
            self.admin_lbl.grid_forget()
        else:
            self.admin_lbl.grid(row=1, column=2, sticky="e", padx=(0, 16), pady=(4, 12))

    def _show_enforce(self, on):
        self.enforce_var.set(on)
        self.strip.configure(fg_color=theme.ACCENT if on else theme.WARN)
        self.rule_title.configure(text=self.t("access.rule_title" if on else "access.off_title"),
                                  text_color=theme.TEXT if on else theme.WARN)
        self.rule_text.configure(text=self.t("access.rule_text" if on else "access.off_text"))
        self.block_stat_lbl.configure(text=self.t("access.stat_blocked" if on else "access.not_allowed"))
        self.stat["block"].configure(text_color=theme.DANGER_TEXT if on else theme.MUTED)

    # ---- actions ----
    def _toggle_enforce(self):
        on = self.enforce_var.get()
        if not on and not self._confirm_off():
            self.enforce_var.set(True)
            return
        self.vm.set_enforce(on)

    def _confirm_off(self):
        """Turning protection off is sensitive: confirm, and re-check the password if set."""
        if not messagebox.askyesno(config.APP, self.t("access.off_confirm")):
            return False
        if not settings_service.has_password():
            return True
        pw = widgets.ask_pw(self.winfo_toplevel(), self.t("dlg.unlock_prompt"))
        if pw is not None and settings_service.check_password(pw):
            return True
        if pw is not None:
            messagebox.showerror(config.APP, self.t("settings.pw_wrong"))
        return False

    def _set(self, allow):
        msg = self.vm.set_allowed(list(self.tree.selection()), allow)
        if msg:
            messagebox.showinfo(config.APP, msg)

    def _add_manual(self):
        d = ctk.CTkInputDialog(text=self.t("access.add_prompt"), title=config.APP)
        self.vm.add_manual(d.get_input())
