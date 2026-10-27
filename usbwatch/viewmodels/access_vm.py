"""Access Control: separate Allowed (whitelist) and Blocked (blacklist) lists, plus a
default action (log-only or block) for devices that are in neither list."""
from .. import util
from ..core import Observable
from ..services import audit_service
from .base import ViewModel

ALL_COLUMNS = ("col.name", "col.serial", "col.last_connected", "col.list", "col.state")
LIST_COLUMNS = ("col.name", "col.serial", "col.last_connected", "col.state")

# default action <-> monitor policy mode
_DEFAULT_TO_MODE = {"off": "off", "log": "blacklist", "block": "whitelist"}
_MODE_TO_DEFAULT = {"off": "off", "blacklist": "log", "whitelist": "block"}


class AccessVM(ViewModel):
    def __init__(self, shell):
        super().__init__(shell)
        self.all_rows = Observable([])
        self.allowed_rows = Observable([])
        self.blocked_rows = Observable([])
        self.default_action = Observable(_MODE_TO_DEFAULT.get(self.cfg.get("policy_mode", "off"), "off"))

    # ---- data ----
    def _state(self, sid, blocked, now):
        if sid in blocked:
            return "blocked"
        if sid in now:
            return "connected"
        return ""

    def reload(self):
        from ..i18n import t
        pol = {s.upper(): (k, n) for s, k, n in self.repo.policy_all()}
        blocked = self.repo.blocked_serials()
        now = {self.mon.serials[d].upper() for d in self.mon.known if self.mon.serials.get(d)}
        info = {d.serial.upper(): (d.name, d.last_connect) for d in self.shell.storage_devices}
        label = {"allow": t("access.tab_allowed"), "block": t("access.tab_blocked")}

        def state_text(sid):
            s = self._state(sid, blocked, now)
            return (t("access.state_blocked") if s == "blocked"
                    else t("access.state_connected") if s == "connected" else "")

        all_rows, allowed, blocked_list = [], [], []
        for d in self.shell.storage_devices:
            sid = d.serial.upper()
            kind = pol.get(sid, ("", ""))[0]
            all_rows.append({"iid": sid, "tag": kind,
                             "values": (d.name, sid, d.last_connect, label.get(kind, "—"), state_text(sid))})
        for sid, (kind, name) in pol.items():
            nm, last = info.get(sid, (name or "(not in history)", ""))
            row = {"iid": sid, "tag": kind, "values": (nm, sid, last, state_text(sid))}
            (allowed if kind == "allow" else blocked_list).append(row)
        self.all_rows.set(all_rows)
        self.allowed_rows.set(allowed)
        self.blocked_rows.set(blocked_list)
        self.default_action.set(_MODE_TO_DEFAULT.get(self.cfg.get("policy_mode", "off"), "off"))

    # ---- commands ----
    def set_kind(self, serials, kind):
        """kind: 'allow' | 'block' | None (remove)."""
        if not serials:
            from ..i18n import t
            return t("access.select_first")
        now = util.now_str()
        names = {r["iid"]: r["values"][0]
                 for src in (self.all_rows, self.allowed_rows, self.blocked_rows)
                 for r in src.value}
        for sid in serials:
            if kind is None:
                self.repo.policy_del(sid)
            else:
                self.repo.policy_set(sid, kind, names.get(sid, ""), now)
            audit_service.log("Policy", {"allow": "Allow", "block": "Block"}.get(kind, "Remove"),
                              names.get(sid, sid), sid)
        self.repo.commit()
        self.shell.policy_changed()
        return None

    def add_manual(self, serial, kind):
        if not serial or not serial.strip():
            return
        self.repo.policy_set(serial.strip(), kind, "(added manually)", util.now_str())
        self.repo.commit()
        audit_service.log("Policy", "Allow" if kind == "allow" else "Block",
                          serial.strip(), "added manually")
        self.shell.policy_changed()

    def set_default(self, action):
        self.shell.set_cfg(policy_mode=_DEFAULT_TO_MODE.get(action, "off"))
        audit_service.log("Policy", "Default action", action)
        self.shell.policy_changed()
        self.default_action.set(action)
