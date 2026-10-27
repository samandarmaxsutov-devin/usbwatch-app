"""File Activity view."""
import customtkinter as ctk

from ..viewmodels import activity_vm
from . import export_util, theme, widgets
from .base_view import BaseView

_COL_KEYS = ("col.time", "col.drive", "col.action", "col.path", "col.to_label", "col.size_bytes")
_COL_WIDTHS = (140, 50, 110, 520, 200, 100)


class ActivityView(BaseView):
    def build(self):
        self.vm = self.shell.activity_vm
        p = self
        p.grid_rowconfigure(1, weight=1)
        self._all = self.t("activity.all")

        tools = widgets.header(p, self.t("nav.activity"))
        ctk.CTkButton(tools, text=self.t("btn.export"), width=110, fg_color=theme.BTN2,
                      hover_color=theme.BTN2H, text_color=theme.TEXT,
                      command=lambda: export_util.export_tree(self, self.tree, "File Activity")
                      ).pack(side="right", padx=4)
        self.filter_var = ctk.StringVar(value=self._all)
        ctk.CTkOptionMenu(tools, values=[self._all] + activity_vm.ACTIONS,
                          variable=self.filter_var, width=160,
                          command=self._on_filter).pack(side="right", padx=4)
        self.search = ctk.CTkEntry(tools, placeholder_text=self.t("activity.search_ph"), width=240)
        self.search.pack(side="right", padx=4)
        self.search.bind("<KeyRelease>", lambda _e: self.vm.set_search(self.search.get()))

        cols = tuple(self.t(k) for k in _COL_KEYS)
        fr, self.tree = widgets.make_tree(p, cols, _COL_WIDTHS, stretch=(cols[3],))
        fr.grid(row=1, column=0, sticky="nsew")
        self.bind_obs(self.vm.rows, lambda rows: widgets.fill_tree(self.tree, rows))

    def _on_filter(self, value):
        self.vm.set_filter(activity_vm.ALL if value == self._all else value)
