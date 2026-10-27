"""Low-level Windows helpers: drives, volumes, PowerShell, drive<->PnP mapping.

Everything that talks to the OS for drive/volume facts lives here so the rest of the
app stays testable and import-safe on non-Windows machines.
"""
import ctypes
import json
import os
import subprocess

_NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW

try:
    _k32 = ctypes.windll.kernel32
    _shell32 = ctypes.windll.shell32
except AttributeError:  # non-Windows (import safety)
    _k32 = _shell32 = None


def is_admin() -> bool:
    try:
        return bool(_shell32.IsUserAnAdmin())
    except Exception:
        return False


def _drives_of_type(drive_type: int):
    out = []
    if not _k32:
        return out
    mask = _k32.GetLogicalDrives()
    for i in range(26):
        if mask >> i & 1:
            root = f"{chr(65 + i)}:\\"
            if _k32.GetDriveTypeW(root) == drive_type:
                out.append(root)
    return out


def removable_drives():
    """Drive roots reported as removable (DRIVE_REMOVABLE = 2)."""
    return _drives_of_type(2)


def fixed_drives():
    """Drive roots reported as fixed (DRIVE_FIXED = 3) — includes external USB HDDs."""
    return _drives_of_type(3)


def volume_info(root):
    """(label, filesystem, volume-serial-number) for a drive root."""
    if not _k32:
        return "", "", 0
    label = ctypes.create_unicode_buffer(261)
    fs = ctypes.create_unicode_buffer(261)
    ser = ctypes.c_ulong(0)
    _k32.GetVolumeInformationW(root, label, 261, ctypes.byref(ser), None, None, fs, 261)
    return label.value, fs.value, ser.value


def run_ps(script, timeout=30):
    """Run a PowerShell snippet and return stdout ("" on any failure)."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, timeout=timeout, creationflags=_NO_WINDOW,
        )
        return r.stdout
    except Exception:
        return ""


def drive_pnp_map():
    """{'F:': <full PnP device id of the backing disk>} for every logical disk."""
    out = run_ps(
        "Get-CimInstance Win32_DiskDrive | ForEach-Object { $d=$_; "
        "Get-CimAssociatedInstance -InputObject $d -ResultClassName Win32_DiskPartition | ForEach-Object { "
        "Get-CimAssociatedInstance -InputObject $_ -ResultClassName Win32_LogicalDisk | ForEach-Object { "
        "$_.DeviceID + '|' + $d.PNPDeviceID } } }"
    )
    m = {}
    for line in out.splitlines():
        if "|" in line:
            drv, pnp = line.strip().split("|", 1)
            m[drv.upper()] = pnp
    return m


_PNP_STATUS_PS = r"""
Get-PnpDevice | Where-Object { $_.InstanceId -like 'USB\*' -or $_.InstanceId -like 'USBSTOR\*' } |
  ForEach-Object { [pscustomobject]@{
    id=$_.InstanceId; name=$_.FriendlyName; cls=$_.Class; status=$_.Status;
    present=$_.Present; svc=$_.Service; mfg=$_.Manufacturer } } |
  ConvertTo-Json -Compress
"""


_pnp_cache = {"ts": 0.0, "data": {}}


def pnp_status_map(ttl=4.0):
    """{INSTANCEID(upper): dict(present, status, name, cls, svc, mfg)} for USB/USBSTOR devices.

    Result is cached for `ttl` seconds because the underlying Get-PnpDevice call is slow.
    """
    import time
    if ttl and (time.time() - _pnp_cache["ts"]) < ttl and _pnp_cache["data"]:
        return _pnp_cache["data"]
    try:
        data = json.loads(run_ps(_PNP_STATUS_PS, 40) or "null")
    except Exception:
        return {}
    if isinstance(data, dict):
        data = [data]
    out = {}
    for d in data or []:
        iid = (d.get("id") or "").upper()
        if iid:
            out[iid] = {
                "present": bool(d.get("present")),
                "status": (d.get("status") or ""),
                "name": d.get("name") or "",
                "cls": d.get("cls") or "",
                "svc": d.get("svc") or "",
                "mfg": d.get("mfg") or "",
            }
    _pnp_cache["ts"], _pnp_cache["data"] = time.time(), out
    return out


def system_drive():
    return os.environ.get("SystemDrive", "C:").upper()


def open_regedit(instance_id):
    """Open RegEdit navigated to the device's Enum key."""
    try:
        import winreg
    except ImportError:
        return False
    reg_path = ("Computer\\HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Enum\\" + instance_id)
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r"Software\Microsoft\Windows\CurrentVersion\Applets\Regedit") as k:
            winreg.SetValueEx(k, "LastKey", 0, winreg.REG_SZ, reg_path)
        subprocess.Popen(["regedit.exe"])
        return True
    except Exception:
        return False
