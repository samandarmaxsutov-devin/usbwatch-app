"""Access Control view: separate Allowed / Blocked lists + default action."""
from tkinter import messagebox

import customtkinter as ctk

from .. import config
from ..viewmodels import access_vm
from . import theme, widgets
from .base_view import BaseView


class AccessView(BaseView):
    def build(self):
        self.vm = self.shell.access_vm
        p = self
        p.grid_rowconfigure(3, weight=1)

        widgets.header(p, self.t("nav.access"))

        # master on/off switch, then the default action for devices in neither list
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.grid(row=2, column=0, sticky="w", pady=(0, 12))
        self.enforce_var = ctk.BooleanVar(value=self.vm.enforce_on.value)
        ctk.CTkSwitch(row, text=self.t("access.enforce"), variable=self.enforce_var,
                      command=self._toggle_enforce).pack(side="left", padx=(0, 28))
        ctk.CTkLabel(row, text=self.t("access.default_label")).pack(side="left", padx=(0, 10))
        self._allow = self.t("access.default_allow")
        self._block = self.t("access.default_block")
        self.default_btn = ctk.CTkSegmentedButton(
            row, values=[self._allow, self._block], command=self._change_default,
            selected_color="#0d9488", selected_hover_color="#0f766e",
            unselected_color=theme.BTN2, unselected_hover_color=theme.BTN2H, text_color=theme.TEXT)
        self.default_btn.pack(side="left")

        tabs = ctk.CTkTabview(
            p, fg_color=theme.PANEL, segmented_button_selected_color=theme.ACCENT,
            segmented_button_selected_hover_color=theme.ACCENT_HOVER,
            segmented_button_unselected_color=theme.BTN2, text_color=theme.TEXT)
        tabs.grid(row=3, column=0, sticky="nsew")
        t_all = tabs.add(self.t("access.tab_all"))
        t_allow = tabs.add(self.t("access.tab_allowed"))
        t_block = tabs.add(self.t("access.tab_blocked"))

        self.all_tree = self._make_all_tab(t_all)
        self.allow_tree = self._make_list_tab(t_allow, "allow")
        self.block_tree = self._make_list_tab(t_block, "block")

        self.bind_obs(self.vm.all_rows, lambda r: widgets.fill_tree(self.all_tree, r))
        self.bind_obs(self.vm.allowed_rows, lambda r: widgets.fill_tree(self.allow_tree, r))
        self.bind_obs(self.vm.blocked_rows, lambda r: widgets.fill_tree(self.block_tree, r))
        self._action_label = {"allow": self._allow, "block": self._block}
        self.bind_obs(self.vm.default_action,
                      lambda a: self.default_btn.set(self._action_label.get(a, self._allow)))
        self.bind_obs(self.vm.enforce_on, self._show_enforce)

    def on_show(self):
        self.vm.reload()

    # ---- tab builders ----
    def _make_all_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="w", pady=(6, 8))
        dark = {"fg_color": theme.BTN2, "hover_color": theme.BTN2H, "text_color": theme.TEXT}
        ctk.CTkButton(bar, text=self.t("access.to_allowed"), width=150,
                      command=lambda: self._set("all", "allow")).pack(side="left", padx=(0, 8))
        ctk.CTkButton(bar, text=self.t("access.to_blocked"), width=150,
                      fg_color=theme.DANGER, hover_color=theme.DANGERH,
                      command=lambda: self._set("all", "block")).pack(side="left", padx=(0, 8))
        ctk.CTkButton(bar, text=self.t("access.remove"), width=160,
                      command=lambda: self._set("all", None), **dark).pack(side="left")
        cols = tuple(self.t(k) for k in access_vm.ALL_COLUMNS)
        fr, tree = widgets.make_tree(parent, cols, (240, 190, 150, 110, 160), stretch=(cols[0],))
        fr.grid(row=1, column=0, sticky="nsew", pady=(0, 6))
        return tree

    def _make_list_tab(self, parent, kind):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="w", pady=(6, 8))
        dark = {"fg_color": theme.BTN2, "hover_color": theme.BTN2H, "text_color": theme.TEXT}
        ctk.CTkButton(bar, text=self.t("access.add_manual"), width=170,
                      command=lambda: self._add_manual(kind)).pack(side="left", padx=(0, 8))
        ctk.CTkButton(bar, text=self.t("access.remove"), width=160,
                      command=lambda: self._set(kind, None), **dark).pack(side="left")
        cols = tuple(self.t(k) for k in access_vm.LIST_COLUMNS)
        fr, tree = widgets.make_tree(parent, cols, (260, 210, 160, 170), stretch=(cols[0],))
        fr.grid(row=1, column=0, sticky="nsew", pady=(0, 6))
        return tree

    # ---- actions ----
    def _tree_for(self, which):
        return {"all": self.all_tree, "allow": self.allow_tree, "block": self.block_tree}[which]

    def _set(self, which, kind):
        serials = list(self._tree_for(which).selection())
        msg = self.vm.set_kind(serials, kind)
        if msg:
            messagebox.showinfo(config.APP, msg)

    def _add_manual(self, kind):
        d = ctk.CTkInputDialog(text=self.t("access.add_prompt"), title=config.APP)
        sid = d.get_input()
        if sid and sid.strip():
            self.vm.add_manual(sid, kind)

    def _show_enforce(self, on):
        self.enforce_var.set(on)
        self.default_btn.configure(state="normal" if on else "disabled")

    def _toggle_enforce(self):
        on = self.enforce_var.get()
        if not on and not messagebox.askyesno(config.APP, self.t("access.enforce_off_warn")):
            self.enforce_var.set(True)
            return
        self.vm.set_enforce(on)

    def _change_default(self, value):
        action = "block" if value == self._block else "allow"
        if action == "block" and not messagebox.askyesno(config.APP, self.t("access.whitelist_warn")):
            self.default_btn.set(self._action_label.get(self.vm.default_action.value, self._allow))
            return
        self.vm.set_default(action)
