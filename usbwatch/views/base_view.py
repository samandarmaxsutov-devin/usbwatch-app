"""Base class for page views: a transparent frame that binds to observables."""
import customtkinter as ctk

from ..i18n import t


class BaseView(ctk.CTkFrame):
    def __init__(self, parent, shell):
        super().__init__(parent, fg_color="transparent")
        self.shell = shell
        self.t = t
        self._subs = []
        self.grid_columnconfigure(0, weight=1)
        self.build()

    def build(self):
        raise NotImplementedError

    def bind_obs(self, observable, callback):
        """Subscribe callback to an observable for the life of this view."""
        self._subs.append(observable.subscribe(callback))

    def on_show(self):
        """Called when the page becomes visible (override to lazy-load)."""

    def teardown(self):
        """Unsubscribe from observables before this view is destroyed (e.g. on language change)."""
        for off in self._subs:
            off()
        self._subs.clear()
