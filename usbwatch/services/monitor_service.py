"""Live USB drive monitoring: mount/unmount detection, file-activity events, and
policy enforcement (auto-disable blocked storage devices). Pushes everything onto a
queue the view-model drains on the UI thread."""
import datetime as dt
import os
import threading
import time

from . import pnp_service, system_service

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:  # import safety when watchdog isn't installed yet
    FileSystemEventHandler = object
    Observer = None


def _now():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Handler(FileSystemEventHandler):
    """Translates filesystem events on one drive into activity tuples."""

    def __init__(self, drive, q, serial=""):
        self.drive, self.q, self.serial = drive, q, serial
        self.last, self.sizes = {}, {}

    def _emit(self, action, path, dest=""):
        if "System Volume Information" in path or "$RECYCLE.BIN" in path:
            return
        key = (action, path)
        now = time.time()
        if action == "Modified" and now - self.last.get(key, 0) < 1.0:
            return
        self.last[key] = now
        size = ""
        try:
            size = os.path.getsize(dest or path)
            self.sizes[dest or path] = size
        except OSError:
            size = self.sizes.get(path, "")
        self.q.put((_now(), self.drive, action, path, dest, size, self.serial))

    def on_created(self, e):
        if not e.is_directory:
            self._emit("Created", e.src_path)

    def on_modified(self, e):
        if not e.is_directory:
            self._emit("Modified", e.src_path)

    def on_deleted(self, e):
        if not e.is_directory:
            self._emit("Deleted", e.src_path)

    def on_moved(self, e):
        if not e.is_directory:
            self._emit("Renamed/Moved", e.src_path, e.dest_path)


class Monitor:
    """Polls for drive changes and runs a watchdog observer per connected USB drive."""

    def __init__(self, q):
        self.q = q
        self.obs, self.known, self.serials, self.pnps = {}, set(), {}, {}
        self.policy = {"mode": "off", "allow": set(), "block": set()}
        self.usb_fixed, self._last_fixed, self._refreshing = set(), None, False

    # ---- policy ----
    def allowed(self, serial):
        p, s = self.policy, (serial or "").upper()
        if p["mode"] in ("blacklist", "whitelist") and s in p["block"]:
            return False
        if p["mode"] == "whitelist":
            return s in p["allow"]
        return True

    def _block(self, d, serial, pnp):
        if d[:2].upper() == system_service.system_drive():
            return False                                       # never touch the system drive
        if not pnp.upper().startswith("USBSTOR\\"):
            self.q.put((_now(), d, "Block failed", d, "Cannot identify this device, not blocked", "", serial))
            return False
        if not system_service.is_admin():
            self.q.put((_now(), d, "Block failed", d, "Run USBWatch as Administrator", "", serial))
            return False
        ok = pnp_service.set_device_enabled(pnp, False)
        self.q.put((_now(), d, "Blocked" if ok else "Block failed", d,
                    pnp if ok else "Windows refused to disable the device", "", serial))
        return ok

    def enforce_now(self):
        for d in list(self.known):
            sid = self.serials.get(d)
            if sid and not self.allowed(sid):
                threading.Thread(target=self._enforce, args=(d, sid), daemon=True).start()

    def _enforce(self, d, sid):
        if self._block(d, sid, self.pnps.get(d, "")):
            o = self.obs.pop(d, None)
            if o:
                o.stop()

    # ---- drive lifecycle ----
    def _start(self, d):
        if Observer is None:
            return
        label, fs, vol = system_service.volume_info(d)
        pnp = system_service.drive_pnp_map().get(d[:2].upper(), "")
        serial = pnp.split("\\")[-1].upper() if pnp else f"VOL-{vol:08X}"
        self.serials[d], self.pnps[d] = serial, pnp
        if (not pnp or pnp.upper().startswith("USBSTOR\\")) and not self.allowed(serial):
            if self._block(d, serial, pnp):
                return
        o = Observer()
        o.schedule(Handler(d, self.q, serial), d, recursive=True)
        o.daemon = True
        o.start()
        if d not in self.known:       # removed while we were resolving
            o.stop()
            return
        self.obs[d] = o
        self.q.put((_now(), d, "Mounted", d, label, "", serial))
        files = {}                    # index the drive -> detect offline deletions
        for base, dirs, names in os.walk(d):
            dirs[:] = [x for x in dirs if x not in ("System Volume Information", "$RECYCLE.BIN")]
            for n in names:
                fp = os.path.join(base, n)
                try:
                    files[fp[3:]] = os.path.getsize(fp)
                except OSError:
                    pass
            if d not in self.known:
                return
        self.q.put(("__snapshot__", d, serial, files))

    def _refresh_fixed(self, fixed):
        try:
            sysd = system_service.system_drive()
            self.usb_fixed = {k + "\\" for k, v in system_service.drive_pnp_map().items()
                              if v.upper().startswith("USBSTOR\\") and k != sysd and k + "\\" in fixed}
        finally:
            self._refreshing = False

    def poll(self):
        cur = set(system_service.removable_drives())
        fixed = set(system_service.fixed_drives())
        if fixed != self._last_fixed and not self._refreshing:
            self._last_fixed, self._refreshing = fixed, True
            threading.Thread(target=self._refresh_fixed, args=(fixed,), daemon=True).start()
        cur |= {d for d in fixed if d in self.usb_fixed}
        new, gone = cur - self.known, self.known - cur
        self.known = cur
        for d in new:
            threading.Thread(target=self._start, args=(d,), daemon=True).start()
        for d in gone:
            o = self.obs.pop(d, None)
            if o:
                o.stop()
            self.pnps.pop(d, None)
            self.q.put((_now(), d, "Unmounted", d, "", "", self.serials.pop(d, "")))
