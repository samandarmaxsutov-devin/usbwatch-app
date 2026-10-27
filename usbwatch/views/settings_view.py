"""Settings view: language, autostart, password."""
from tkinter import messagebox

import customtkinter as ctk

from .. import config, i18n
from . import theme, widgets
from .base_view import BaseView


class SettingsView(BaseView):
    def build(self):
        self.vm = self.shell.settings_vm
        p = self
        widgets.header(p, self.t("nav.settings"))

        box = ctk.CTkFrame(p, fg_color=theme.PANEL, corner_radius=12)
        box.grid(row=1, column=0, sticky="ew")

        # language
        lang_row = ctk.CTkFrame(box, fg_color="transparent")
        lang_row.pack(anchor="w", padx=20, pady=(20, 6))
        ctk.CTkLabel(lang_row, text=self.t("settings.language") + ":").pack(side="left", padx=(0, 10))
        self._names = {i18n.LANG_NAMES[c]: c for c in i18n.LANGS}
        cur_name = i18n.LANG_NAMES.get(i18n.lang.value, "O'zbekcha")
        ctk.CTkOptionMenu(lang_row, values=list(self._names), width=160,
                          variable=ctk.StringVar(value=cur_name),
                          command=self._set_language).pack(side="left")

        # appearance (light / dark)
        appr_row = ctk.CTkFrame(box, fg_color="transparent")
        appr_row.pack(anchor="w", padx=20, pady=6)
        ctk.CTkLabel(appr_row, text=self.t("settings.appearance") + ":").pack(side="left", padx=(0, 10))
        self._dark, self._light = self.t("settings.dark"), self.t("settings.light")
        seg = ctk.CTkSegmentedButton(appr_row, values=[self._dark, self._light],
                                     command=self._set_appearance)
        seg.set(self._light if self.vm.appearance == "light" else self._dark)
        seg.pack(side="left")

        self.as_var = ctk.BooleanVar(value=self.vm.autostart.value)
        ctk.CTkSwitch(box, text=self.t("settings.autostart"), variable=self.as_var,
                      command=self._toggle_autostart).pack(anchor="w", padx=20, pady=10)
        ctk.CTkButton(box, text=self.t("settings.change_pw"), width=180,
                      command=self._change_pw).pack(anchor="w", padx=20, pady=(0, 20))

        self.bind_obs(self.vm.autostart, lambda v: self.as_var.set(v))

    def _set_language(self, name):
        self.vm.set_language(self._names[name])     # triggers i18n.lang -> main window rebuild

    def _set_appearance(self, label):
        mode = "light" if label == self._light else "dark"
        self.vm.set_appearance(mode)
        theme.set_mode(mode)                        # triggers theme.mode -> main window rebuild

    def _toggle_autostart(self):
        messagebox.showinfo(config.APP, self.vm.toggle_autostart(self.as_var.get()))

    def _change_pw(self):
        old = widgets.ask_pw(self, self.t("settings.pw_current"))
        if old is None:
            return
        new = widgets.ask_pw(self, self.t("settings.pw_new"))
        if new is None:
            return
        repeat = widgets.ask_pw(self, self.t("settings.pw_repeat"))
        msg = self.vm.change_password(old, new, repeat)
        (messagebox.showinfo if msg == self.t("settings.pw_changed")
         else messagebox.showerror)(config.APP, msg)
