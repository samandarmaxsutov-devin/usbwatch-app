"""Access Control: only USB storage devices on the Allowed list may be used; every other
device (blocked or never allowed) is disabled as soon as it is plugged in."""
from .. import util
from ..core import Observable
from ..services import audit_service, system_service
from .base import ViewModel

COLUMNS = ("col.access", "col.name", "col.serial", "col.state", "col.last_connected")
FILTERS = ("all", "allow", "block")


class AccessVM(ViewModel):
    def __init__(self, shell):
        super().__init__(shell)
        self.rows = Observable([])            # every known device, unfiltered
        self.filter = Observable("all")       # one of FILTERS
        self.counts = Observable({"allow": 0, "block": 0, "connected": 0})
        self.is_admin = Observable(system_service.is_admin())
        self.enforce_on = Observable(bool(self.cfg.get("acl_on", True)))

    # ---- data ----
    def reload(self):
        from ..i18n import t
        allowed = {s.upper(): n for s, k, n in self.repo.policy_all() if k == "allow"}
        disabled = self.repo.blocked_serials()
        now = {self.mon.serials[d].upper() for d in self.mon.known if self.mon.serials.get(d)}

        devices = [(d.serial.upper(), d.name, d.last_connect, d.disabled)
                   for d in self.shell.storage_devices]
        seen = {sid for sid, *_ in devices}
        devices += [(sid, name or t("access.manual_name"), "", False)       # allowed by serial,
                    for sid, name in allowed.items() if sid not in seen]  # never plugged in

        on = bool(self.cfg.get("acl_on", True))
        blocked_label = t("access.blocked" if on else "access.not_allowed")
        rows, counts = [], {"allow": 0, "block": 0, "connected": 0}
        for sid, name, last, dev_disabled in devices:
            kind = "allow" if sid in allowed else "block"
            counts[kind] += 1
            if sid in now:
                counts["connected"] += 1
                state = t("access.state_connected")
            elif sid in disabled or dev_disabled:
                state = t("access.state_blocked")
            else:
                state = t("access.state_offline")
            access = "●  " + (t("access.allowed") if kind == "allow" else blocked_label)
            tags = (("acl_block",) if kind == "block" and on else ()) + (("acl_live",) if sid in now else ())
            rows.append({"iid": sid, "kind": kind, "tag": tags,
                         "values": (access, name, sid, state, last)})
        rows.sort(key=lambda r: (r["kind"] != "block", r["values"][2] not in now, r["values"][1].lower()))
        self.rows.set(rows)
        self.counts.set(counts)
        self.is_admin.set(system_service.is_admin())
        self.enforce_on.set(on)

    def visible_rows(self):
        f = self.filter.value
        return [r for r in self.rows.value if f == "all" or r["kind"] == f]

    def set_filter(self, f):
        self.filter.set(f if f in FILTERS else "all")

    # ---- commands ----
    def set_enforce(self, on):
        """Switch access control on/off. Off re-enables every device we blocked."""
        self.shell.set_cfg(acl_on=bool(on))
        audit_service.log("Policy", "Access control", "on" if on else "off")
        self.shell.policy_changed()

    def set_allowed(self, serials, allow):
        """Allow the selected devices, or take their permission away (= blocked)."""
        if not serials:
            from ..i18n import t
            return t("access.select_first")
        now = util.now_str()
        names = {r["iid"]: r["values"][1] for r in self.rows.value}
        for sid in serials:
            if allow:
                self.repo.policy_set(sid, "allow", names.get(sid, ""), now)
            else:
                self.repo.policy_del(sid)
            audit_service.log("Policy", "Allow" if allow else "Block", names.get(sid, sid), sid)
        self.repo.commit()
        self.shell.policy_changed()
        return None

    def add_manual(self, serial):
        serial = (serial or "").strip()
        if not serial:
            return
        self.repo.policy_set(serial, "allow", "", util.now_str())
        self.repo.commit()
        audit_service.log("Policy", "Allow", serial, "added manually")
        self.shell.policy_changed()
