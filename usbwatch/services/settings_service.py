"""Persistent configuration, password protection and Windows autostart."""
import hashlib
import hmac
import json
import os
import secrets
import subprocess

from .. import config
from . import system_service

_NO_WINDOW = 0x08000000


# ---------- config.json ----------
def load_cfg() -> dict:
    try:
        with open(config.CFG) as f:
            return json.load(f)
    except Exception:
        return {}


def save_cfg(c: dict):
    with open(config.CFG, "w") as f:
        json.dump(c, f)


def update_cfg(**kw):
    c = load_cfg()
    c.update(kw)
    save_cfg(c)
    return c


def policy_settings(cfg: dict):
    """(enforcement on, default action 'allow'|'block') for access control.

    Migrates the old single `policy_mode` (off / blacklist / whitelist): its "off" also
    ignored the Blocked list, so it maps to enforcement on with unknown devices allowed."""
    mode = cfg.get("policy_mode", "off")
    on = cfg.get("policy_on", True)
    default = cfg.get("policy_default", "block" if mode == "whitelist" else "allow")
    return bool(on), default


# ---------- password ----------
def _hash_pw(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200_000).hex()


def has_password() -> bool:
    return "hash" in load_cfg()


def set_password(pw):
    salt = secrets.token_bytes(16)
    c = load_cfg()
    c["salt"], c["hash"] = salt.hex(), _hash_pw(pw, salt)
    save_cfg(c)


def check_password(pw) -> bool:
    c = load_cfg()
    if "hash" not in c:
        return False
    return hmac.compare_digest(_hash_pw(pw, bytes.fromhex(c["salt"])), c["hash"])


# ---------- autostart ----------
_TASK_VER = 2   # bump to re-register existing tasks after changing their settings


def _launch_parts():
    """(executable, arguments) used to start the app in the background at logon."""
    import sys
    if getattr(sys, "frozen", False):            # the built .exe
        return os.path.normpath(sys.executable), "--autostart"
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        cand = exe[:-10] + "pythonw.exe"
        if os.path.exists(cand):
            exe = cand
    exe = os.path.normpath(exe)                   # use Windows backslashes
    entry = os.path.normpath(
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "run.py"))
    return exe, f'"{entry}" --autostart'


def _launch_cmd():
    exe, args = _launch_parts()
    return f'"{exe}" {args}'


def _register_task(highest: bool) -> bool:
    """Register the logon task. Unlike plain `schtasks /Create`, this also runs on battery
    power and is never stopped after the default 72-hour execution limit."""
    exe, args = _launch_parts()

    def q(s):
        return "'" + s.replace("'", "''") + "'"
    script = (
        "$u=[Security.Principal.WindowsIdentity]::GetCurrent().Name;"
        f"$a=New-ScheduledTaskAction -Execute {q(exe)} -Argument {q(args)} -WorkingDirectory {q(os.path.dirname(exe))};"
        "$t=New-ScheduledTaskTrigger -AtLogOn -User $u; $t.Delay='PT10S';"
        f"$p=New-ScheduledTaskPrincipal -UserId $u -LogonType Interactive -RunLevel {'Highest' if highest else 'Limited'};"
        "$s=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries "
        "-ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -StartWhenAvailable;"
        f"Register-ScheduledTask -TaskName {q(config.APP)} -Action $a -Trigger $t -Principal $p "
        "-Settings $s -Force -ErrorAction Stop | Out-Null"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                       capture_output=True, text=True, creationflags=_NO_WINDOW, timeout=60)
    return r.returncode == 0


def autostart_enabled() -> bool:
    try:
        import winreg
    except ImportError:
        return False
    r = subprocess.run(["schtasks", "/Query", "/TN", config.APP], capture_output=True)
    if r.returncode == 0:
        return True
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run") as k:
            winreg.QueryValueEx(k, config.APP)
            return True
    except OSError:
        return False


def harden_data_dir():
    """Restrict the data folder (holds the password hash + events DB) to the current user,
    Administrators and SYSTEM, so other standard users on the PC cannot read it. Runs once."""
    cfg = load_cfg()
    if cfg.get("hardened"):
        return
    try:
        import subprocess
        user = os.environ.get("USERNAME")
        grants = ["/grant:r", "*S-1-5-32-544:(OI)(CI)F", "/grant:r", "*S-1-5-18:(OI)(CI)F"]
        if user:
            grants = ["/grant:r", f"{user}:(OI)(CI)F"] + grants
        subprocess.run(["icacls", config.DATA, "/inheritance:r"] + grants,
                       capture_output=True, creationflags=0x08000000, timeout=20)
    except Exception:
        pass
    update_cfg(hardened=True)


def ensure_autostart():
    """Enable autostart on first run so the app starts with Windows, and self-heal if the
    registered task is stale: wrong path after moving/rebuilding, old task settings, or a
    non-elevated task registered before the app ever ran as Administrator.
    The user may still turn it off in Settings; then it stays off."""
    cfg = load_cfg()
    want = _launch_cmd()
    try:
        if cfg.get("autostart_setup") and not autostart_enabled():
            return                              # turned off by the user
        stale = (cfg.get("autostart_cmd") != want or cfg.get("autostart_ver") != _TASK_VER
                 or (system_service.is_admin() and not cfg.get("autostart_admin")))
        if not cfg.get("autostart_setup") or stale:
            set_autostart(True)
            update_cfg(autostart_setup=True, autostart_cmd=want, autostart_ver=_TASK_VER)
    except Exception:
        pass


def set_autostart(on: bool) -> str:
    import winreg
    cmd = _launch_cmd()
    if on:
        # elevated: the task starts the app as Administrator at logon with no UAC prompt
        if system_service.is_admin() and _register_task(highest=True):
            update_cfg(autostart_admin=True)
            _delete_run_key()
            return "Autostart enabled (scheduled task, highest privileges)."
        update_cfg(autostart_admin=False)
        if _register_task(highest=False):        # not elevated: a normal logon task
            _delete_run_key()
            return "Autostart enabled (logon task). Run USBWatch as Administrator once to enable blocking at startup."
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, config.APP, 0, winreg.REG_SZ, cmd)
        return "Autostart enabled (Run key)."
    subprocess.run(["schtasks", "/Delete", "/TN", config.APP, "/F"], capture_output=True)
    _delete_run_key()
    return "Autostart disabled."


def _delete_run_key():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, config.APP)
    except OSError:
        pass
