"""Devices tab view: storage (flash) history, live drive cards, per-device activity."""
import customtkinter as ctk

from ..util import fmt_size
from . import export_util, theme, widgets
from .base_view import BaseView

_COL_KEYS = ("col.name", "col.serial", "col.first_connected", "col.last_connected",
             "col.last_removed", "col.capacity", "col.free", "col.state")
_COL_WIDTHS = (230, 160, 125, 125, 125, 85, 105, 95)
_ACT_KEYS = ("col.time", "col.drive", "col.action", "col.path", "col.to_label", "col.size_bytes")
_ACT_WIDTHS = (140, 50, 110, 520, 200, 100)


class DevicesView(BaseView):
    def build(self):
        self.vm = self.shell.devices_vm
        p = self
        p.grid_rowconfigure(3, weight=1)
        p.grid_rowconfigure(5, weight=1)

        tools = widgets.header(p, self.t("nav.storage"))
        ctk.CTkButton(tools, text=self.t("btn.refresh"), width=100,
                      command=self.vm.refresh).pack(side="left", padx=4)
        ctk.CTkButton(tools, text=self.t("btn.export"), width=110, fg_color=theme.BTN2,
                      hover_color=theme.BTN2H, text_color=theme.TEXT,
                      command=lambda: export_util.export_tree(self, self.dev_tree, "USB Storage")
                      ).pack(side="left", padx=4)

        cards = ctk.CTkFrame(p, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        self.cards = {}
        for i, (k, key) in enumerate((("known", "card.known"), ("now", "card.now"),
                                      ("events", "card.events"))):
            cards.grid_columnconfigure(i, weight=1, uniform="c")
            f, v = widgets.card(cards, self.t(key))
            f.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))
            self.cards[k] = v

        self.drive_frame = ctk.CTkFrame(p, fg_color="transparent")
        self.drive_frame.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        self.drive_widgets = {}
        self.no_drive_lbl = ctk.CTkLabel(self.drive_frame, text=self.t("storage.no_drive"),
                                         text_color=theme.MUTED)
        self.no_drive_lbl.grid(row=0, column=0, sticky="w")

        cols = tuple(self.t(k) for k in _COL_KEYS)
        fr, self.dev_tree = widgets.make_tree(p, cols, _COL_WIDTHS, stretch=(cols[0],))
        fr.grid(row=3, column=0, sticky="nsew")
        self.dev_tree.bind("<<TreeviewSelect>>", self._on_select)

        self.dev_title = ctk.CTkLabel(p, text="", font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        self.dev_title.grid(row=4, column=0, sticky="w", pady=(14, 6))
        acols = tuple(self.t(k) for k in _ACT_KEYS)
        fr, self.act_tree = widgets.make_tree(p, acols, _ACT_WIDTHS, stretch=(acols[3],))
        fr.grid(row=5, column=0, sticky="nsew")

        self.bind_obs(self.vm.rows, self._render_rows)
        self.bind_obs(self.vm.actions, self._render_actions)
        self.bind_obs(self.vm.title, lambda _t: self.dev_title.configure(text=self._title()))
        self.bind_obs(self.shell.known_count, lambda n: self.cards["known"].configure(text=str(n)))
        self.bind_obs(self.shell.now_count, lambda n: self.cards["now"].configure(text=str(n)))
        self.bind_obs(self.shell.events_count, lambda n: self.cards["events"].configure(text=str(n)))
        self.bind_obs(self.shell.drives, self._render_drives)

    def _title(self):
        sid = self.vm.selected.value
        if not sid:
            return self.t("storage.select_hint")
        name = self.vm.device_name(sid)
        n = len(self.vm.actions.value)
        return self.t("storage.actions_title", name, n) if n else self.t("storage.actions_none", name)

    def _on_select(self, _e=None):
        sel = self.dev_tree.selection()
        self.vm.select(sel[0] if sel else None)

    def _render_rows(self, rows):
        widgets.fill_tree(self.dev_tree, rows)
        if self.vm.selected.value and self.dev_tree.exists(self.vm.selected.value):
            self.dev_tree.selection_set(self.vm.selected.value)

    def _render_actions(self, rows):
        widgets.fill_tree(self.act_tree, [{"values": r, "tag": r[2]} for r in rows])
        self.dev_title.configure(text=self._title())

    def _render_drives(self, drives):
        cur = {d["drive"] for d in drives}
        for key in list(self.drive_widgets):
            if key not in cur:
                self.drive_widgets.pop(key)["frame"].destroy()
        for col, d in enumerate(drives):
            w = self.drive_widgets.get(d["drive"])
            if not w:
                f = ctk.CTkFrame(self.drive_frame, fg_color=theme.PANEL, corner_radius=12)
                title = ctk.CTkLabel(f, text="", font=ctk.CTkFont(size=14, weight="bold"))
                title.pack(anchor="w", padx=14, pady=(10, 2))
                bar = ctk.CTkProgressBar(f, width=280)
                bar.pack(padx=14, pady=4)
                info = ctk.CTkLabel(f, text="", text_color=theme.MUTED, justify="left")
                info.pack(anchor="w", padx=14, pady=(0, 10))
                w = self.drive_widgets[d["drive"]] = {"frame": f, "title": title, "bar": bar, "info": info}
            w["frame"].grid(row=0, column=col, sticky="w", padx=(0, 10))
            w["title"].configure(text=f"{d['drive'][:2]}  {d['label'] or 'USB drive'}  ·  {d['fs']}")
            w["bar"].set(d["ratio"])
            w["bar"].configure(progress_color="#f87171" if d["ratio"] > 0.9 else theme.ACCENT)
            w["info"].configure(text=f"{fmt_size(d['used'])} used  ·  {fmt_size(d['free'])} free  "
                                     f"·  {fmt_size(d['total'])} total")
        if drives:
            self.no_drive_lbl.grid_remove()
        else:
            self.no_drive_lbl.grid()
