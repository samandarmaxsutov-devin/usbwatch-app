"""Reading/writing the human-readable CSV logs and parsing Windows' setupapi install log."""
import csv
import datetime as dt
import glob
import os
import re

from .. import config

LOGDIR = config.LOGDIR


def log_csv(rows):
    """Append events to a daily CSV log file."""
    if not rows:
        return
    try:
        os.makedirs(LOGDIR, exist_ok=True)
        fn = os.path.join(LOGDIR, f"events-{dt.date.today():%Y-%m-%d}.csv")
        new = not os.path.exists(fn)
        with open(fn, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            if new:
                w.writerow(("Time", "Drive", "Action", "Path", "To / Label / Device", "Size", "Serial"))
            w.writerows(rows)
    except OSError:
        pass


def write_device_csv(columns, rows):
    """Write the current device table to logs/usb-devices.csv."""
    try:
        os.makedirs(LOGDIR, exist_ok=True)
        with open(os.path.join(LOGDIR, "usb-devices.csv"), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(columns)
            w.writerows(rows)
    except OSError:
        pass


def parse_setupapi(paths=None):
    """USB device install history from Windows' setupapi.dev.log files."""
    if paths is None:
        paths = glob.glob(os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                                       "INF", "setupapi.dev*.log"))
    rx = re.compile(r">>>\s+\[Device Install[^\]]*?-\s+((?:USBSTOR|USB)\\[^\]]+)\]")
    rows = []
    for pth in paths:
        try:
            pending = None
            with open(pth, encoding="utf-8", errors="replace") as f:
                for line in f:
                    m = rx.search(line)
                    if m:
                        pending = m.group(1)
                    elif pending and "Section start" in line:
                        rows.append((line.split("Section start", 1)[1].strip(), pending,
                                     "Storage" if pending.upper().startswith("USBSTOR") else "USB",
                                     os.path.basename(pth)))
                        pending = None
        except OSError:
            continue
    return sorted(rows, reverse=True)


def list_csv_logs():
    return sorted(glob.glob(os.path.join(LOGDIR, "*.csv")), reverse=True)
