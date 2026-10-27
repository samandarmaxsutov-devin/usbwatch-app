"""Enumerate USB devices from the registry and enrich them with live PnP status.

  list_storage() -> only USBSTOR mass-storage devices (drives the monitor/ACL use).
  list_all()     -> every USB + USBSTOR device, USBDeview-style, for the inventory tab.

Timestamps come from the device "Properties" subkeys (0064/0065/0066/0067); connected /
disabled / friendly names come from one Get-PnpDevice call (see system_service).
"""
import datetime as dt
import re

from .. import config
from ..models import Device
from . import system_service

try:
    import winreg
except ImportError:  # non-Windows import safety
    winreg = None

_FLAGS = (winreg.KEY_READ | winreg.KEY_WOW64_64KEY) if winreg else 0

# Friendly type names by device Class (registry "Class" value / PnP Class).
_TYPE_BY_CLASS = {
    "USBSTOR": "Mass Storage", "DISKDRIVE": "Mass Storage", "VOLUME": "Volume",
    "WPD": "Portable Device", "HIDCLASS": "HID (Input)", "HID": "HID (Input)",
    "KEYBOARD": "Keyboard", "MOUSE": "Mouse", "NET": "Network", "IMAGE": "Camera / Scanner",
    "CAMERA": "Camera", "PRINTER": "Printer", "MEDIA": "Audio / Video", "AUDIOENDPOINT": "Audio",
    "BLUETOOTH": "Bluetooth", "SMARTCARDREADER": "Smart Card", "PORTS": "Serial (COM/LPT)",
    "MONITOR": "Monitor", "MODEM": "Modem", "BIOMETRIC": "Biometric", "USB": "USB Hub / Composite",
    "USBDEVICE": "USB Device", "SCSIADAPTER": "Storage Controller",
}

_VIDPID_RE = re.compile(r"VID_([0-9A-Fa-f]{4}).*?PID_([0-9A-Fa-f]{4})")


def _filetime_to_str(raw):
    try:
        v = int.from_bytes(raw[:8], "little")
        if v == 0:
            return ""
        return dt.datetime.fromtimestamp(v / 1e7 - 11644473600).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def _read_prop_time(inst_key, code):
    try:
        with winreg.OpenKey(inst_key, f"Properties\\{config.PROP}\\{code}") as k:
            i = 0
            while True:
                try:
                    _, val, _ = winreg.EnumValue(k, i)
                except OSError:
                    break
                if isinstance(val, bytes) and len(val) >= 8:
                    return _filetime_to_str(val)
                i += 1
            with winreg.OpenKey(k, "00000000") as k2:   # newer builds nest the value
                i = 0
                while True:
                    _, val, _ = winreg.EnumValue(k2, i)
                    if isinstance(val, bytes) and len(val) >= 8:
                        return _filetime_to_str(val)
                    i += 1
    except OSError:
        pass
    return ""


def _val(key, name):
    try:
        return str(winreg.QueryValueEx(key, name)[0]).split(";")[-1].strip()
    except OSError:
        return ""


def _type_for(cls, desc=""):
    t = _TYPE_BY_CLASS.get((cls or "").upper())
    if t:
        return t
    if "mass storage" in (desc or "").lower():
        return "Mass Storage"
    return cls or "USB Device"


def _enum_branch(branch):
    """Yield (instance_id, vidpid_or_class_key, serial, friendly, desc, service, cls, mfg,
              first, connect, disconnect) for every device under Enum\\<branch>."""
    if not winreg:
        return
    try:
        root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                              rf"SYSTEM\CurrentControlSet\Enum\{branch}", 0, _FLAGS)
    except OSError:
        return
    with root:
        for i in range(winreg.QueryInfoKey(root)[0]):
            group = winreg.EnumKey(root, i)
            try:
                gk = winreg.OpenKey(root, group, 0, _FLAGS)
            except OSError:
                continue
            with gk:
                for j in range(winreg.QueryInfoKey(gk)[0]):
                    serial = winreg.EnumKey(gk, j)
                    try:
                        ik = winreg.OpenKey(gk, serial, 0, _FLAGS)
                    except OSError:
                        continue
                    with ik:
                        yield (
                            f"{branch}\\{group}\\{serial}", group, serial,
                            _val(ik, "FriendlyName"), _val(ik, "DeviceDesc"),
                            _val(ik, "Service"), _val(ik, "Class"), _val(ik, "Mfg"),
                            _read_prop_time(ik, config.PROP_CODES["first_install"])
                            or _read_prop_time(ik, config.PROP_CODES["install"]),
                            _read_prop_time(ik, config.PROP_CODES["connect"]),
                            _read_prop_time(ik, config.PROP_CODES["disconnect"]),
                        )


def _apply_status(dev: Device, status_map):
    st = status_map.get(dev.instance_id.upper())
    if not st:
        return
    dev.connected = st["present"]
    # Get-PnpDevice reports a disabled / problem device with Status "Error".
    dev.disabled = st["status"].lower() == "error"
    if st["name"] and not dev.name:
        dev.name = st["name"]
    if st["cls"] and not dev.usb_class:
        dev.usb_class = st["cls"]
    if st["svc"] and not dev.service:
        dev.service = st["svc"]
    if st["mfg"] and not dev.vendor_name:
        dev.vendor_name = st["mfg"]


def list_storage():
    """USBSTOR mass-storage devices only (serial-keyed; drives the monitor/ACL).

    Registry-only (no PowerShell) so it is fast; the caller fills connected/disabled
    from the live mounted-drive set and the blocked list.
    """
    out = []
    for iid, group, serial, friendly, desc, service, cls, mfg, first, conn, disc in _enum_branch("USBSTOR"):
        parts = group.split("&")
        vendor = parts[1].replace("Ven_", "") if len(parts) > 1 else ""
        product = parts[2].replace("Prod_", "") if len(parts) > 2 else ""
        out.append(Device(
            name=friendly or f"{vendor} {product}".strip() or desc,
            description=desc, serial=serial, instance_id=iid,
            device_type="Mass Storage", usb_class=cls or "USBSTOR",
            vendor=vendor, product=product, vendor_name=mfg, service=service,
            is_storage=True, first_install=first, last_connect=conn, last_disconnect=disc,
        ))
    return out


def list_all():
    """Every USB + USBSTOR device (USBDeview-style inventory)."""
    status = system_service.pnp_status_map()
    out = []
    for branch in ("USB", "USBSTOR"):
        for iid, group, serial, friendly, desc, service, cls, mfg, first, conn, disc in _enum_branch(branch):
            m = _VIDPID_RE.search(group)
            vid = m.group(1).upper() if m else ""
            pid = m.group(2).upper() if m else ""
            vendor = product = ""
            if branch == "USBSTOR":
                parts = group.split("&")
                vendor = parts[1].replace("Ven_", "") if len(parts) > 1 else ""
                product = parts[2].replace("Prod_", "") if len(parts) > 2 else ""
            d = Device(
                name=friendly or desc or f"{vendor} {product}".strip() or group,
                description=desc, serial=serial, instance_id=iid,
                usb_class=cls, vid=vid, pid=pid, vendor=vendor, product=product,
                vendor_name=mfg, service=service,
                is_storage=(branch == "USBSTOR") or cls.upper() in ("USBSTOR", "DISKDRIVE"),
                first_install=first, last_connect=conn, last_disconnect=disc,
            )
            _apply_status(d, status)
            d.device_type = _type_for(d.usb_class or cls, desc)
            out.append(d)
    # Sort: connected first, then most-recently-connected.
    out.sort(key=lambda x: (x.connected, x.last_connect or x.first_install), reverse=True)
    return out
