"""Application composition root: appearance, the auth gate, and the main window."""
import customtkinter as ctk

from . import config
from .services import settings_service
from .views import theme
from .views.auth_view import AuthWindow
from .views.main_window import MainWindow


def run():
    ctk.set_default_color_theme("blue")
    theme.apply(settings_service.load_cfg().get("appearance", "dark"))

    if not settings_service.has_password():
        if config.AUTOSTART:
            return                      # not configured yet; launch once manually first
        w = AuthWindow()
        w.mainloop()
        if not w.ok:
            return
    elif not config.AUTOSTART:
        w = AuthWindow()
        w.mainloop()
        if not w.ok:
            return

    settings_service.harden_data_dir()    # protect the password hash + DB from other users
    settings_service.ensure_autostart()   # always run in background from the next boot
    app = MainWindow()
    app.start()                          # start() hides to tray when launched with --autostart
    app.mainloop()
