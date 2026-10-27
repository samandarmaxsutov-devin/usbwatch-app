"""Devices tab: USB storage history + per-device activity."""
from .. import util
from ..core import Command, Observable
from .base import ViewModel

COLUMNS = ("Name", "Serial", "First Connected", "Last Connected", "Last Removed",
           "Capacity", "Free (last seen)", "Connected")
ACTION_COLUMNS = ("Time", "Drive", "Action", "Path", "To / Label", "Size (bytes)")


class DevicesVM(ViewModel):
    def __init__(self, shell):
        super().__init__(shell)
        self.rows = Observable([])            # [{iid, values, tag}]
        self.selected = Observable(None)      # serial (upper) or None
        self.actions = Observable([])         # [(ts,drive,action,path,dest,size)]
        self.title = Observable("Select a device above to see its actions")
        self.refresh = Command(self.shell.load_devices)

    def apply(self, devices):
        cap = self.repo.capacity_map()
        rows = []
        for i, d in enumerate(devices):
            t, f = cap.get(d.serial.upper(), (None, None))
            state = "Connected" if d.connected else ("Disabled" if d.disabled else "")
            rows.append({
                "iid": d.serial.upper() or str(i),
                "device": d,
                "values": (d.name, d.serial, d.first_install, d.last_connect, d.last_disconnect,
                           util.fmt_size(t) if t else "", util.fmt_size(f) if t else "", state),
                "tag": "connected" if d.connected else ("disabled" if d.disabled else ""),
            })
        self.rows.set(rows)
        if self.selected.value and not any(r["iid"] == self.selected.value for r in rows):
            self.selected.value = None
        self.reload_actions()

    def select(self, serial):
        self.selected.value = (serial or "").upper() or None
        self.reload_actions()

    def device_name(self, serial):
        return self.shell.names.get((serial or "").upper(), serial)

    def reload_actions(self):
        sid = self.selected.value
        if not sid:
            self.actions.set([])
            self.title.value = "Select a device above to see its actions"
            return
        rows = self.repo.events_for_serial(sid)
        self.actions.set(rows)
        name = self.device_name(sid)
        self.title.value = (f"Actions on {name}  ·  {len(rows)} event(s)" if rows
                            else f"Actions on {name}  ·  nothing recorded yet")
