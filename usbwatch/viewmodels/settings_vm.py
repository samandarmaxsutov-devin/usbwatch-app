"""Settings tab: language, appearance (light/dark), autostart and password."""
from .. import config, i18n
from ..core import Observable
from ..services import audit_service, settings_service
from .base import ViewModel


class SettingsVM(ViewModel):
    def __init__(self, shell):
        super().__init__(shell)
        self.autostart = Observable(settings_service.autostart_enabled())
        self.data_dir = config.DATA
        self.appearance = self.cfg.get("appearance", "dark")

    def set_language(self, code):
        i18n.set_language(code)
        audit_service.log("Settings", "Language", code)

    def set_appearance(self, mode):
        """Persist + audit. The view applies the theme (view-layer concern)."""
        self.shell.set_cfg(appearance=mode)
        self.appearance = mode
        audit_service.log("Settings", "Appearance", mode)

    def toggle_autostart(self, on):
        msg = settings_service.set_autostart(on)
        self.autostart.set(settings_service.autostart_enabled())
        audit_service.log("Settings", "Autostart", "on" if on else "off")
        return msg

    def change_password(self, old, new, repeat):
        if old is None or not settings_service.check_password(old):
            return i18n.t("settings.pw_wrong")
        if not new or len(new) < 6:
            return i18n.t("settings.pw_short")
        if new != repeat:
            return i18n.t("settings.pw_mismatch")
        settings_service.set_password(new)
        audit_service.log("Settings", "Password changed")
        return i18n.t("settings.pw_changed")
