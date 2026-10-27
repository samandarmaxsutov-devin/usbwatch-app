"""Login / first-run password window."""
import customtkinter as ctk

from .. import config
from ..i18n import t
from ..viewmodels.auth_vm import AuthVM
from . import appicon, theme, widgets


class AuthWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.vm = AuthVM()
        self.ok = False
        setup = self.vm.setup
        self.title(config.APP)
        widgets.center(self, 380, 360 if setup else 300)
        self.resizable(False, False)
        self.configure(fg_color=theme.BG)
        appicon.apply_window_icon(self)

        ctk.CTkLabel(self, text="USBWatch", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(30, 2))
        ctk.CTkLabel(self, text=t("auth.create_sub") if setup else t("auth.signin_sub"),
                     text_color=theme.MUTED).pack()
        self.e1 = ctk.CTkEntry(self, show="•", placeholder_text=t("auth.pw_ph"), width=290, height=40)
        self.e1.pack(pady=(24, 8))
        self.e2 = None
        if setup:
            self.e2 = ctk.CTkEntry(self, show="•", placeholder_text=t("auth.repeat_ph"),
                                   width=290, height=40)
            self.e2.pack(pady=(0, 8))
        self.msg = ctk.CTkLabel(self, text="", text_color="#f87171")
        self.msg.pack()
        ctk.CTkButton(self, text=t("auth.create_btn") if setup else t("auth.unlock_btn"),
                      width=290, height=40, command=self._submit).pack(pady=10)
        self.bind("<Return>", lambda _e: self._submit())
        self.after(300, self.e1.focus)

    def _submit(self):
        ok, err = self.vm.submit(self.e1.get(), self.e2.get() if self.e2 else None)
        if ok:
            self.ok = True
            self.destroy()
            return
        self.e1.delete(0, "end")
        self.msg.configure(text=err)
        if self.vm.tries >= 5:
            self.destroy()
