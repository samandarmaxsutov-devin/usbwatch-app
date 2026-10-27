"""All-USB inventory tab (USBDeview-style): every USB/USBSTOR device with full columns,
enable/disable, and CSV/HTML/TXT export."""
import threading

from ..core import Command, Observable
from ..i18n import t
from ..services import audit_service, export_service, pnp_service, system_service
from .base import ViewModel

COLUMNS = ("Name", "Description", "Type", "Connected", "Disabled", "Serial", "VID", "PID",
           "Class", "Service", "Vendor", "First Install", "Last Connect", "Last Disconnect",
           "Instance ID")


def _row(d):
    return (d.name, d.description, d.device_type,
            "Yes" if d.connected else "", "Yes" if d.disabled else "",
            d.serial, d.vid, d.pid, d.usb_class, d.service, d.vendor_name,
            d.first_install, d.last_connect, d.last_disconnect, d.instance_id)


class InventoryVM(ViewModel):
    def __init__(self, shell):
        super().__init__(shell)
        self._devs = []
        self.rows = Observable([])            # [{iid, values, tag}]
        self.search = Observable("")
        self.loading = Observable(False)
        self.status = Observable("")
        self.refresh = Command(self.shell.load_inventory)

    def apply(self, devices):
        self._devs = devices
        self.loading.set(False)
        self._rebuild()

    def set_search(self, text):
        self.search.set(text or "")
        self._rebuild()

    def _rebuild(self):
        t = self.search.value.lower().strip()
        rows = []
        for i, d in enumerate(self._devs):
            if t and t not in " ".join(map(str, _row(d))).lower():
                continue
            rows.append({
                "iid": str(i),
                "device": d,
                "values": _row(d),
                "tag": "connected" if d.connected else ("disabled" if d.disabled else ""),
            })
        self.rows.set(rows)
        self.status.set(f"{len(rows)} of {len(self._devs)} device(s)")

    def device_for(self, iid):
        try:
            return self._devs[int(iid)]
        except (ValueError, IndexError):
            return None

    # ---- actions ----
    def set_enabled(self, iid, enable):
        d = self.device_for(iid)
        if not d or not d.instance_id:
            return "No device selected."
        if not system_service.is_admin():
            return t("dlg.need_admin")
        verb = "Enabling" if enable else "Disabling"
        self.status.set(f"{verb} {d.name}…")

        def work():
            ok = pnp_service.set_device_enabled(d.instance_id, enable)
            if ok:
                audit_service.log("Device", "Enable" if enable else "Disable", d.name, d.instance_id)
            msg = (f"{'Enabled' if enable else 'Disabled'} {d.name}." if ok
                   else f"Windows refused to {'enable' if enable else 'disable'} {d.name}.")
            self.shell.post(lambda: (self.status.set(msg), self.shell.load_inventory()))

        threading.Thread(target=work, daemon=True).start()
        return None

    def export(self, fmt, path):
        rows = [r["values"] for r in self.rows.value]
        export_service.export(COLUMNS, rows, fmt, path, title="USB Devices")
        self.status.set(f"Exported {len(rows)} device(s) to {path}")

    def open_regedit(self, iid):
        d = self.device_for(iid)
        if not d or not d.instance_id:
            return False
        return system_service.open_regedit(d.instance_id)

    def uninstall(self, iid):
        d = self.device_for(iid)
        if not d or not d.instance_id:
            return t("dlg.select_device")
        if not system_service.is_admin():
            return t("dlg.need_admin")
        name = d.name
        self.status.set(f"Uninstalling {name}…")

        def work():
            ok = pnp_service.remove_device(d.instance_id)
            if ok:
                audit_service.log("Device", "Uninstall", name, d.instance_id)
            msg = t("dlg.uninstalled", name) if ok else t("dlg.uninstall_failed", name)
            self.shell.post(lambda: (self.status.set(msg), self.shell.load_inventory()))

        threading.Thread(target=work, daemon=True).start()
        return None

    def detail_rows(self, iid):
        """[(i18n_key, value)] for the details dialog, or []."""
        d = self.device_for(iid)
        if not d:
            return []
        return [
            ("col.name", d.name), ("col.description", d.description), ("col.type", d.device_type),
            ("col.connected", "Yes" if d.connected else ""), ("col.disabled", "Yes" if d.disabled else ""),
            ("col.serial", d.serial), ("col.vid", d.vid), ("col.pid", d.pid),
            ("col.class", d.usb_class), ("col.service", d.service), ("col.vendor", d.vendor_name),
            ("col.drive", d.drive), ("col.first_install", d.first_install),
            ("col.last_connect", d.last_connect), ("col.last_disconnect", d.last_disconnect),
            ("col.instance_id", d.instance_id),
        ]
