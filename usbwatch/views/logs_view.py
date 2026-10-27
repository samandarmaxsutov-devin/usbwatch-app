"""Logs view: daily CSV logs + setupapi install history."""
import os
from tkinter import filedialog

import customtkinter as ctk

from .. import config
from ..services import logs_service
from . import theme, widgets
from .base_view import BaseView


class LogsView(BaseView):
    def build(self):
        self.vm = self.shell.logs_vm
        p = self
        p.grid_rowconfigure(3, weight=1)

        tools = widgets.header(p, self.t("nav.logs"))
        ctk.CTkButton(tools, text=self.t("logs.open_folder"), width=120, fg_color=theme.BTN2,
                      hover_color=theme.BTN2H, text_color=theme.TEXT, command=self._open_folder).pack(side="right", padx=4)
        ctk.CTkButton(tools, text=self.t("logs.open_file"), width=120,
                      command=self._open_file).pack(side="right", padx=4)

        bar = ctk.CTkFrame(p, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="w", pady=(0, 6))
        self.src_var = ctk.StringVar(value="")
        self.menu = ctk.CTkOptionMenu(bar, values=[config.SETUPAPI], variable=self.src_var,
                                      width=380, command=self.vm.load)
        self.menu.pack(side="left")
        self.search = ctk.CTkEntry(bar, placeholder_text=self.t("logs.filter"), width=240)
        self.search.pack(side="left", padx=10)
        self.search.bind("<KeyRelease>", lambda _e: self.vm.set_search(self.search.get()))

        self.info = ctk.CTkLabel(p, text=self.t("logs.subtitle"), text_color=theme.MUTED)
        self.info.grid(row=2, column=0, sticky="w", pady=(0, 8))
        fr, self.tree = widgets.make_tree(p, ("—",), (300,))
        fr.grid(row=3, column=0, sticky="nsew")

        self.bind_obs(self.vm.sources, self._set_sources)
        self.bind_obs(self.vm.current, lambda n: self.src_var.set(n) if n else None)
        self.bind_obs(self.vm.columns, self._set_columns)
        self.bind_obs(self.vm.rows, self._set_rows)
        self.bind_obs(self.vm.info, lambda s: self.info.configure(text=s))

    def on_show(self):
        names = self.vm.refresh_sources()
        if not self.vm.current.value:
            self.vm.load(names[0] if names else config.SETUPAPI)

    def _set_sources(self, names):
        self.menu.configure(values=names or [config.SETUPAPI])

    def _set_columns(self, cols):
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c, anchor="w")
            self.tree.column(c, width=max(90, 900 // max(1, len(cols))), anchor="w", stretch=True)

    def _set_rows(self, rows):
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", "end", values=r)

    def _open_folder(self):
        os.makedirs(logs_service.LOGDIR, exist_ok=True)
        os.startfile(logs_service.LOGDIR)

    def _open_file(self):
        f = filedialog.askopenfilename(filetypes=[("Logs", "*.csv *.log"), ("All files", "*.*")])
        if f:
            self.vm.open_external(f)
