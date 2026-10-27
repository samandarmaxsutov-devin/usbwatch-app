"""Logs tab: browse the daily CSV logs and Windows' setupapi install history."""
import csv
import os
import threading

from .. import config
from ..core import Observable
from ..services import logs_service
from .base import ViewModel


class LogsVM(ViewModel):
    def __init__(self, shell):
        super().__init__(shell)
        self.sources = Observable([])     # list of source names for the dropdown
        self.current = Observable("")
        self.columns = Observable(("—",))
        self.rows = Observable([])        # list of tuples
        self.search = Observable("")
        self.info = Observable("")
        self._all_rows = []
        self._custom = {}                 # name -> external file path
        self._paths = {}
        self._result = None               # set by worker, drained via shell.post

    def refresh_sources(self):
        files = logs_service.list_csv_logs()
        self._paths = {os.path.basename(f): f for f in files}
        self._paths.update(self._custom)
        names = list(self._paths) + [config.SETUPAPI]
        self.sources.set(names)
        return names

    def open_external(self, path):
        if not path:
            return
        name = os.path.basename(path)
        self._custom[name] = path
        self.refresh_sources()
        self.load(name)

    def load(self, name):
        self.current.set(name)
        self.info.set("Loading…")
        path = self._paths.get(name)

        def work():
            try:
                if name == config.SETUPAPI:
                    cols = ("Time", "Device ID", "Kind", "Log file")
                    rows = logs_service.parse_setupapi()
                elif path and path.lower().endswith(".log"):
                    cols = ("Time", "Device ID", "Kind", "Log file")
                    rows = logs_service.parse_setupapi([path])
                else:
                    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
                        data = list(csv.reader(f))
                    cols = tuple(data[0]) if data else ("—",)
                    rows = [tuple(r) for r in data[1:]]
                    if cols and cols[0] == "Time":
                        rows.reverse()
                self.shell.post(lambda: self._apply(cols, rows))
            except Exception as e:
                self.shell.post(lambda: self._apply(("Error",), [(str(e),)]))

        threading.Thread(target=work, daemon=True).start()

    def _apply(self, cols, rows):
        self.columns.set(cols)
        self._all_rows = rows
        self._filter()

    def set_search(self, text):
        self.search.set(text or "")
        self._filter()

    def _filter(self):
        flt = self.search.value.lower()
        rows = [r for r in self._all_rows if not flt or flt in " ".join(map(str, r)).lower()]
        shown = rows[:10000]
        self.rows.set(shown)
        extra = " — showing first 10000" if len(rows) > 10000 else ""
        self.info.set(f"{len(rows)} row(s){extra}")
