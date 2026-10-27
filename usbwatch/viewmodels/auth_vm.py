"""Login / first-run password setup view-model."""
from .. import i18n
from ..services import settings_service


class AuthVM:
    def __init__(self):
        self.setup = not settings_service.has_password()
        self.tries = 0

    def submit(self, pw, repeat=None):
        """Returns (ok, error_message)."""
        if self.setup:
            if len(pw) < 6:
                return False, i18n.t("auth.min6")
            if pw != repeat:
                return False, i18n.t("auth.mismatch")
            settings_service.set_password(pw)
            return True, ""
        if settings_service.check_password(pw):
            return True, ""
        self.tries += 1
        return False, i18n.t("auth.wrong", self.tries)

    @staticmethod
    def check(pw):
        return settings_service.check_password(pw)
