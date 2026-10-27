"""File Activity tab: live log of everything happening on connected USB drives."""
from ..core import Command, Observable
from .base import ViewModel

COLUMNS = ("Time", "Drive", "Action", "Path", "To / Label", "Size (bytes)")
ALL = "All actions"
ACTIONS = ["Created", "Modified", "Deleted", "Renamed/Moved", "Deleted (offline)",
           "Blocked", "Block failed", "Unblocked", "Mounted", "Unmounted"]


class ActivityVM(ViewModel):
    def __init__(self, shell):
        super().__init__(shell)
        self.rows = Observable([])        # [{values, tag}]
        self.search = Observable("")
        self.action_filter = Observable(ALL)
        self.reload_cmd = Command(self.reload)

    def set_search(self, text):
        self.search.set(text or "")
        self.reload()

    def set_filter(self, action):
        self.action_filter.set(action or ALL)
        self.reload()

    def reload(self):
        like = f"%{self.search.value}%"
        act = self.action_filter.value
        rows = self.repo.query_activity(like, None if act == ALL else act)
        self.rows.set([{"values": r, "tag": r[2]} for r in rows])
