"""Application coordinator view-model: owns the services, the 1-second tick loop that
drains the monitor queue, and the shared state the page view-models read."""
import queue
import threading

from .. import util
from ..core import Observable
from ..services import audit_service, device_service, logs_service, settings_service
from ..services.database import Repository
from ..services.monitor_service import Monitor
from .access_vm import AccessVM
from .activity_vm import ActivityVM
from .devices_vm import DevicesVM
from .inventory_vm import InventoryVM
from .logs_vm import LogsVM
from .settings_vm import SettingsVM


class ShellViewModel:
    def __init__(self):
        self.repo = Repository()
        self.q = queue.Queue()
        self.mon = Monitor(self.q)
        self.cfg = settings_service.load_cfg()

        self.ui_queue = queue.Queue()   # callables posted from worker threads, run on the UI thread
        self.names = {}                 # serial(upper) -> friendly name
        self.storage_devices = []       # list[Device] shown on the Devices tab
        self._dev_result = None
        self._inv_result = None
        self.tick_n = 0

        # shared observables (sidebar / stats)
        self.known_count = Observable(0)
        self.now_count = Observable(0)
        self.events_count = Observable(0)
        self.drives = Observable([])        # list of dicts for the drive cards
        self.drives_summary = Observable("No USB drives connected")
        self.status_text = Observable("●  Monitoring active")

        # page view-models
        self.devices_vm = DevicesVM(self)
        self.inventory_vm = InventoryVM(self)
        self.activity_vm = ActivityVM(self)
        self.access_vm = AccessVM(self)
        self.logs_vm = LogsVM(self)
        self.settings_vm = SettingsVM(self)

    # ---- lifecycle ----
    def start(self):
        self.sync_policy()
        self.load_devices()
        self.activity_vm.reload()

    def post(self, fn):
        """Schedule a callable to run on the UI thread during the next tick."""
        self.ui_queue.put(fn)

    def set_cfg(self, **kw):
        self.cfg = settings_service.update_cfg(**kw)

    # ---- device history ----
    def load_devices(self):
        def work():
            try:
                self._dev_result = device_service.list_storage()
            except Exception:
                self._dev_result = []
        threading.Thread(target=work, daemon=True).start()

    def load_inventory(self):
        self.inventory_vm.loading.set(True)

        def work():
            try:
                self._inv_result = device_service.list_all()
            except Exception:
                self._inv_result = []
        threading.Thread(target=work, daemon=True).start()

    def _apply_devices(self, devs):
        self.storage_devices = sorted(devs, key=lambda d: d.last_connect or "", reverse=True)
        now = {self.mon.serials[d].upper() for d in self.mon.known if self.mon.serials.get(d)}
        blocked = self.repo.blocked_serials()
        for d in self.storage_devices:        # live status without any PowerShell call
            sid = d.serial.upper()
            d.connected = sid in now
            d.disabled = sid in blocked
        self.names = {d.serial.upper(): d.name for d in self.storage_devices}
        self.devices_vm.apply(self.storage_devices)
        self.known_count.value = len(self.storage_devices)
        self._write_device_csv()
        self.access_vm.reload()

    def _write_device_csv(self):
        cap = self.repo.capacity_map()
        headers = ("Name", "Serial", "First Connected", "Last Connected", "Last Removed",
                   "Capacity", "Free (last seen)")
        rows = []
        for d in self.storage_devices:
            t, f = cap.get(d.serial.upper(), (None, None))
            rows.append((d.name, d.serial, d.first_install, d.last_connect, d.last_disconnect,
                         util.fmt_size(t) if t else "", util.fmt_size(f) if t else ""))
        logs_service.write_device_csv(headers, rows)

    def current_root(self, serial):
        for d, sid in list(self.mon.serials.items()):
            if sid and sid.upper() == (serial or "").upper() and d in self.mon.known:
                return d
        return None

    # ---- policy ----
    def sync_policy(self):
        rows = self.repo.policy_all()
        self.mon.policy = {
            "mode": self.cfg.get("policy_mode", "off"),
            "allow": {s.upper() for s, k, _n in rows if k == "allow"},
            "block": {s.upper() for s, k, _n in rows if k == "block"},
        }

    def policy_changed(self):
        self.sync_policy()
        self.mon.enforce_now()
        for serial, pnp in self.repo.blocked_all():
            if self.mon.allowed(serial):
                threading.Thread(target=self._enable, args=(serial, pnp), daemon=True).start()
        self.access_vm.reload()

    def _enable(self, serial, pnp):
        from ..services import pnp_service
        ok = pnp_service.set_device_enabled(pnp, True)
        self.q.put((util.now_str(), "", "Unblocked" if ok else "Unblock failed", pnp, "", "", serial))

    # ---- capacity ----
    def save_capacity(self):
        import shutil
        from ..services import system_service
        now = util.now_str()
        for d in list(self.mon.known):
            sid = self.mon.serials.get(d)
            if not sid:
                continue
            try:
                total, _used, free = shutil.disk_usage(d)
                label, fs, _ = system_service.volume_info(d)
            except OSError:
                continue
            self.repo.capacity_set(sid, label, fs, total, free, now)
        self.repo.commit()

    def refresh_drives(self):
        import shutil
        from ..services import system_service
        out = []
        for d in sorted(self.mon.known):
            try:
                total, used, free = shutil.disk_usage(d)
                label, fs, _ = system_service.volume_info(d)
            except OSError:
                continue
            out.append({"drive": d, "label": label, "fs": fs, "used": used,
                        "free": free, "total": total, "ratio": used / total if total else 0})
        self.drives.set(out)

    # ---- snapshot bookkeeping ----
    def handle_snapshot(self, d, serial, files):
        prior = self.repo.snapshot(serial)
        now = util.now_str()
        gone = [(now, d, "Deleted (offline)", d + rel, "", str(sz), serial)
                for rel, sz in prior.items() if rel not in files]
        if gone:
            self.repo.insert_events(gone)
        self.repo.replace_snapshot(serial, files)
        logs_service.log_csv(gone)
        return len(gone)

    def track(self, evs):
        """Keep the per-device file index current (used to detect offline deletions)."""
        for ts, drive, action, path, dest, size, serial in evs:
            if not serial or action in ("Mounted", "Unmounted"):
                continue
            rel = path[3:]
            sz = int(size) if str(size).isdigit() else 0
            if action in ("Created", "Modified"):
                self.repo.snapshot_set(serial, rel, sz)
            elif action == "Deleted":
                self.repo.snapshot_del(serial, rel)
            elif action == "Blocked":
                self.repo.blocked_set(serial, dest, ts)
            elif action == "Unblocked":
                self.repo.blocked_del(serial)
            elif action == "Renamed/Moved" and dest:
                self.repo.snapshot_del(serial, rel)
                self.repo.snapshot_set(serial, dest[3:], sz)
        self.repo.commit()

    # ---- the tick ----
    def tick(self):
        self.tick_n += 1
        while True:                      # run anything posted from worker threads
            try:
                self.ui_queue.get_nowait()()
            except queue.Empty:
                break
            except Exception:
                pass
        try:
            self.mon.poll()
        except Exception:
            pass
        if self._dev_result is not None:
            rows, self._dev_result = self._dev_result, None
            self._apply_devices(rows)
        if self._inv_result is not None:
            rows, self._inv_result = self._inv_result, None
            self.inventory_vm.apply(rows)

        new, snaps = [], []
        while True:
            try:
                item = self.q.get_nowait()
            except queue.Empty:
                break
            (snaps if item[0] == "__snapshot__" else new).append(item)

        offline = sum(self.handle_snapshot(d, serial, files) for _t, d, serial, files in snaps)
        if new:
            self.repo.insert_events(new)
            self.track(new)
            logs_service.log_csv(new)
            self.activity_vm.reload()
            self.devices_vm.reload_actions()
            if any(r[2] == "Mounted" for r in new):
                self.save_capacity()
                self.load_devices()
            enforce = [r for r in new if r[2] in ("Blocked", "Unblocked", "Block failed")]
            for r in enforce:
                audit_service.log("Enforcement", r[2], r[6], r[4])   # action, serial, details
            if enforce:
                self.access_vm.reload()
        if offline:
            self.activity_vm.reload()

        if self.tick_n % 3 == 1:
            self.refresh_drives()
        if self.tick_n % 10 == 0:
            self.save_capacity()
        self._update_stats()

    def _update_stats(self):
        from .. import i18n
        self.events_count.value = self.repo.count_events()
        self.now_count.value = len(self.mon.known)
        d = sorted(self.mon.known)
        self.drives_summary.value = (i18n.t("drives.prefix") + ", ".join(d)) if d else i18n.t("drives.none")
