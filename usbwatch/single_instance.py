"""Keep one running copy of the app per Windows session.

A second launch (desktop shortcut, the exe run again, the logon task) finds the named
mutex, signals the running copy to show its window, and exits, so two monitors never
log the same events twice. Both objects get a permissive DACL and a low integrity label
so a non-elevated launch can still reach the elevated copy.
"""
import ctypes
import threading
from ctypes import wintypes

from . import config

_MUTEX = f"Local\\{config.APP}.instance"
_EVENT = f"Local\\{config.APP}.show"
# Everyone / SYSTEM / Administrators: full access; low mandatory label, no write-up block.
_SDDL = "D:(A;;GA;;;WD)(A;;GA;;;SY)(A;;GA;;;BA)S:(ML;;NW;;;LW)"
_ERROR_ALREADY_EXISTS = 183
_ERROR_ACCESS_DENIED = 5
_EVENT_MODIFY_STATE = 0x0002

try:
    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _adv = ctypes.WinDLL("advapi32", use_last_error=True)
    _k32.CreateMutexW.restype = wintypes.HANDLE
    _k32.CreateEventW.restype = wintypes.HANDLE
    _k32.OpenEventW.restype = wintypes.HANDLE
except (AttributeError, OSError):  # non-Windows import safety
    _k32 = _adv = None

_mutex = None
_event = None


class _SA(ctypes.Structure):
    _fields_ = [("nLength", wintypes.DWORD), ("lpSecurityDescriptor", ctypes.c_void_p),
                ("bInheritHandle", wintypes.BOOL)]


def _security():
    sd = ctypes.c_void_p()
    if not _adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            _SDDL, 1, ctypes.byref(sd), None):
        return None
    return _SA(ctypes.sizeof(_SA), sd, False)


def acquire() -> bool:
    """True if this is the only running copy (keep running), False if another one exists."""
    global _mutex, _event
    if not _k32:
        return True
    sa = _security()
    sa_ptr = ctypes.byref(sa) if sa else None
    h = _k32.CreateMutexW(sa_ptr, False, _MUTEX)
    err = ctypes.get_last_error()
    if not h:
        return err != _ERROR_ACCESS_DENIED     # exists but owned by an elevated copy
    if err == _ERROR_ALREADY_EXISTS:
        _k32.CloseHandle(h)
        return False
    _mutex = h
    _event = _k32.CreateEventW(sa_ptr, False, False, _EVENT)   # auto-reset "show" signal
    return True


def release():
    """Give the instance slot up (before re-launching elevated)."""
    global _mutex, _event
    for h in (_event, _mutex):
        if h:
            _k32.CloseHandle(h)
    _mutex = _event = None


def signal_existing():
    """Ask the running copy to show its window."""
    if not _k32:
        return
    h = _k32.OpenEventW(_EVENT_MODIFY_STATE, False, _EVENT)
    if h:
        _k32.SetEvent(h)
        _k32.CloseHandle(h)


def listen(callback):
    """Call `callback` (on a worker thread) each time another launch asks us to show."""
    if not _event:
        return
    _k32.ResetEvent(_event)                  # ignore launches made while we were starting

    def loop():
        while _event and _k32.WaitForSingleObject(_event, 0xFFFFFFFF) == 0:
            callback()

    threading.Thread(target=loop, daemon=True).start()
