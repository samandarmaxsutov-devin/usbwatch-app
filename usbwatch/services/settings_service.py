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
def _launch_cmd():
    import sys
    if getattr(sys, "frozen", False):            # the built .exe
        return f'"{os.path.normpath(sys.executable)}" --autostart'
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        cand = exe[:-10] + "pythonw.exe"
        if os.path.exists(cand):
            exe = cand
    exe = os.path.normpath(exe)                   # use Windows backslashes
    entry = os.path.normpath(
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "run.py"))
    return f'"{exe}" "{entry}" --autostart'


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
    """Enable autostart on first run so the app starts with Windows, and self-heal if a
    previously registered command is stale (wrong path/interpreter after moving or rebuild).
    The user may still turn it off in Settings; then it stays off."""
    cfg = load_cfg()
    want = _launch_cmd()
    try:
        if not cfg.get("autostart_setup"):
            if not autostart_enabled():
                set_autostart(True)
            update_cfg(autostart_setup=True, autostart_cmd=want)
        elif cfg.get("autostart_cmd") != want and autostart_enabled():
            set_autostart(True)                 # path changed -> re-register so reboot works
            update_cfg(autostart_cmd=want)
    except Exception:
        pass


def set_autostart(on: bool) -> str:
    import winreg
    cmd = _launch_cmd()
    if on:
        # clear any stale task first, then register fresh
        subprocess.run(["schtasks", "/Delete", "/TN", config.APP, "/F"], capture_output=True)
        r = subprocess.run(["schtasks", "/Create", "/TN", config.APP, "/TR", cmd,
                            "/SC", "ONLOGON", "/RL", "HIGHEST", "/F"], capture_output=True, text=True)
        if r.returncode == 0:
            return "Autostart enabled (scheduled task, highest privileges)."
        # not elevated: a normal logon task still runs at sign-in
        r2 = subprocess.run(["schtasks", "/Create", "/TN", config.APP, "/TR", cmd,
                             "/SC", "ONLOGON", "/F"], capture_output=True, text=True)
        if r2.returncode == 0:
            return "Autostart enabled (logon task)."
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, config.APP, 0, winreg.REG_SZ, cmd)
        return "Autostart enabled (Run key)."
    subprocess.run(["schtasks", "/Delete", "/TN", config.APP, "/F"], capture_output=True)
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, config.APP)
    except OSError:
        pass
    return "Autostart disabled."
