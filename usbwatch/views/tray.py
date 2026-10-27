"""Optional system-tray icon so the app keeps monitoring after the window is closed.

Uses infi.systray (pure-python, Windows-only — no Pillow/compiler needed). Falls back
gracefully (start() returns False) when it is not installed. Menu callbacks run on the
tray's own thread; the main window marshals them back onto the Tk thread with `after`.
"""
from .appicon import ico_path

try:
    from infi.systray import SysTrayIcon
except Exception:  # pragma: no cover - optional dependency
    SysTrayIcon = None


class Tray:
    def __init__(self, on_open, on_exit):
        self.on_open = on_open
        self.on_exit = on_exit
        self.icon = None
        self._quitting = False

    def start(self):
        if SysTrayIcon is None:
            return False
        ico = ico_path()
        if not ico:
            return False
        # infi.systray can only render ASCII reliably and always appends an English "Quit",
        # so keep the tray menu in English (independent of the UI language) and always visible.
        menu = (("Open", None, lambda _s: self.on_open()),)
        self.icon = SysTrayIcon(ico, "USBWatch", menu, on_quit=self._on_quit, default_menu_index=0)
        self.icon.start()
        return True

    def _on_quit(self, _systray):
        # Fired for the tray's built-in Quit item and when we call shutdown(); ignore the latter.
        self.icon = None
        if not self._quitting:
            self.on_exit()

    def stop(self):
        self._quitting = True
        if self.icon:
            try:
                self.icon.shutdown()
            except Exception:
                pass
            self.icon = None
