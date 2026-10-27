"""Audit log: records user actions and configuration changes to a daily CSV in the logs
folder (audit-YYYY-MM-DD.csv), so they show up in the Logs tab."""
import csv
import datetime as dt
import os

from .. import config

LOGDIR = config.LOGDIR


def log(category, action, target="", details=""):
    try:
        os.makedirs(LOGDIR, exist_ok=True)
        fn = os.path.join(LOGDIR, f"audit-{dt.date.today():%Y-%m-%d}.csv")
        new = not os.path.exists(fn)
        with open(fn, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            if new:
                w.writerow(("Time", "Category", "Action", "Target", "Details"))
            w.writerow((dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        category, action, target, details))
    except OSError:
        pass
