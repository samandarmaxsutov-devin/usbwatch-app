"""Enable / disable PnP devices (needs Administrator). Used for access-control blocking
and for the inventory Enable/Disable actions."""
import re
import subprocess

_NO_WINDOW = 0x08000000

# A permissive but safe instance-id shape; we never pass arbitrary shell text.
_ID_RE = re.compile(r"^(USB|USBSTOR)\\[\w&.\-\\ {}]+$", re.IGNORECASE)


def set_device_enabled(instance_id: str, enable: bool) -> bool:
    """Enable/disable a USB or USBSTOR device by instance id. Returns success."""
    if not instance_id or not _ID_RE.match(instance_id):
        return False
    verb = "Enable" if enable else "Disable"
    safe = instance_id.replace("'", "''")
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             f"{verb}-PnpDevice -InstanceId '{safe}' -Confirm:$false -ErrorAction Stop"],
            capture_output=True, text=True, timeout=45, creationflags=_NO_WINDOW,
        )
        return r.returncode == 0
    except Exception:
        return False


def is_storage_id(instance_id: str) -> bool:
    return (instance_id or "").upper().startswith("USBSTOR\\")


def remove_device(instance_id: str) -> bool:
    """Uninstall (remove) a device node via pnputil. Needs Administrator."""
    if not instance_id or not _ID_RE.match(instance_id):
        return False
    try:
        r = subprocess.run(["pnputil", "/remove-device", instance_id],
                           capture_output=True, text=True, timeout=45, creationflags=_NO_WINDOW)
        return r.returncode == 0
    except Exception:
        return False
