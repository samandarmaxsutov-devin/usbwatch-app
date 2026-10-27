"""The main application window: sidebar navigation, the page views, the tick loop,
language switching (rebuild) and a system-tray icon so monitoring survives window close."""
from tkinter import messagebox

import customtkinter as ctk

from .. import config, i18n
from ..services import settings_service
from ..viewmodels.shell_vm import ShellViewModel
from . import appicon, theme, widgets
from .access_view import AccessView
from .activity_view import ActivityView
from .devices_view import DevicesView
from .inventory_view import InventoryView
from .logs_view import LogsView
from .settings_view import SettingsView
from .tray import Tray

NAV = (
    ("dev", "nav.storage", DevicesView),
    ("all", "nav.all", InventoryView),
    ("act", "nav.activity", ActivityView),
    ("acl", "nav.access", AccessView),
    ("log", "nav.logs", LogsView),
    ("set", "nav.settings", SettingsView),
)


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.shell = ShellViewModel()
        self.current = "dev"
        self._sidebar_subs = []
        self.views = {}

        self.title(config.APP)
        widgets.center(self, 1240, 740)
        self.minsize(1040, 600)
        self.configure(fg_color=theme.BG)
        appicon.apply_window_icon(self)
        theme.style_tree()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()
        self._lang_sub = i18n.lang.subscribe(lambda _l: self.after(0, self._rebuild), immediate=False)
        self._theme_sub = theme.mode.subscribe(lambda _m: self.after(0, self._rebuild), immediate=False)

        self.tray = Tray(on_open=lambda: self.after(0, self._open_from_tray),
                         on_exit=lambda: self.after(0, self._exit_flow))
        self.has_tray = self.tray.start()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---- UI construction ----
    def _build_ui(self):
        self._build_sidebar()
        self.content = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
        self.views = {}
        for key, _label, cls in NAV:
            v = cls(self.content, self.shell)
            v.grid(row=0, column=0, sticky="nsew", padx=24, pady=20)
            v.grid_remove()
            self.views[key] = v
        self.show_page(self.current)

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color=theme.SIDE)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        ctk.CTkLabel(self.sidebar, text="USBWatch", font=ctk.CTkFont(size=22, weight="bold")
                     ).pack(anchor="w", padx=20, pady=(26, 0))
        ctk.CTkLabel(self.sidebar, text=i18n.t("app.subtitle"), text_color=theme.MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", padx=20, pady=(0, 26))
        self.nav = {}
        for key, label, _cls in NAV:
            b = ctk.CTkButton(self.sidebar, text=i18n.t(label), anchor="w", height=42, corner_radius=8,
                              fg_color="transparent", text_color=theme.TEXT, hover_color=theme.SIDE_HOVER,
                              command=lambda k=key: self.show_page(k))
            b.pack(fill="x", padx=12, pady=3)
            self.nav[key] = b
        self.status = ctk.CTkLabel(self.sidebar, text=i18n.t("status.active"), text_color="#34d399")
        self.status.pack(side="bottom", anchor="w", padx=20, pady=(0, 20))
        self.drives_lbl = ctk.CTkLabel(self.sidebar, text=i18n.t("drives.none"), text_color=theme.MUTED,
                                       font=ctk.CTkFont(size=11), justify="left")
        self.drives_lbl.pack(side="bottom", anchor="w", padx=20, pady=(0, 6))
        self._sidebar_subs = [
            self.shell.drives_summary.subscribe(lambda s: self.drives_lbl.configure(text=s)),
        ]

    def _rebuild(self):
        """Rebuild the whole UI after a language change."""
        for off in self._sidebar_subs:
            off()
        self._sidebar_subs = []
        for v in self.views.values():
            v.teardown()
            v.destroy()
        self.content.destroy()
        self.sidebar.destroy()
        self.configure(fg_color=theme.BG)      # follow light/dark change
        self._build_ui()

    def show_page(self, key):
        self.current = key
        for k, v in self.views.items():
            if k == key:
                v.grid()
                v.on_show()
            else:
                v.grid_remove()
        for k, b in self.nav.items():
            b.configure(fg_color=theme.ACCENT if k == key else "transparent")

    # ---- lifecycle ----
    def start(self):
        self.shell.start()
        self.show_page("dev")
        self._tick()
        if config.AUTOSTART:
            self._hide()

    def _tick(self):
        try:
            self.shell.tick()
        except Exception:
            pass
        self.after(1000, self._tick)

    # ---- hide / show / exit ----
    def _hide(self):
        if self.has_tray:
            self.withdraw()
        else:
            self.iconify()

    def on_close(self):
        # Closing the window hides to the tray and keeps monitoring; exit is from the tray menu.
        if self.has_tray:
            self._hide()
        else:
            self._exit_flow()

    def _open_from_tray(self):
        if not settings_service.has_password():
            self.deiconify()
            self.lift()
            self.focus_force()
            return
        # Keep the window invisible (alpha 0) while asking, so no content shows before unlock.
        self.attributes("-alpha", 0.0)
        self.deiconify()
        pw = widgets.ask_pw(self, i18n.t("dlg.unlock_prompt"))
        if pw is not None and settings_service.check_password(pw):
            self.attributes("-alpha", 1.0)
            self.lift()
            self.focus_force()
        else:
            self.withdraw()
            self.attributes("-alpha", 1.0)

    def _exit_flow(self):
        if not settings_service.has_password():
            self.tray.stop()
            self.destroy()
            return
        hidden = self.state() == "withdrawn"
        if hidden:                              # prompt without revealing content
            self.attributes("-alpha", 0.0)
            self.deiconify()
        pw = widgets.ask_pw(self, i18n.t("dlg.exit_prompt"))
        if pw is not None and settings_service.check_password(pw):
            self.tray.stop()
            self.destroy()
            return
        if pw is not None:
            messagebox.showerror(config.APP, i18n.t("settings.pw_wrong"))
        if hidden:
            self.withdraw()
            self.attributes("-alpha", 1.0)
        # make sure the tray icon is back (the menu Quit item removed it)
        if self.has_tray and self.tray.icon is None:
            self.tray.start()
