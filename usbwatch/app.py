"""Application composition root: appearance, the auth gate, and the main window."""
import sys

import customtkinter as ctk

from . import config, single_instance
from .services import settings_service, system_service
from .views import theme
from .views.auth_view import AuthWindow
from .views.main_window import MainWindow


def run():
    # One copy only: a second launch just brings the running one to the front.
    if not single_instance.acquire():
        single_instance.signal_existing()
        return

    # Blocking/unblocking USB devices needs Administrator: re-launch elevated (UAC prompt).
    # If the prompt is declined, carry on with monitoring only.
    if not system_service.is_admin() and "--elevated" not in sys.argv:
        single_instance.release()            # let the elevated copy take the slot
        if system_service.relaunch_as_admin(sys.argv[1:] + ["--elevated"]):
            return
        if not single_instance.acquire():
            single_instance.signal_existing()
            return

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
