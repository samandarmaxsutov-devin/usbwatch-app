"""Application-wide constants and data-folder paths. No UI, no business logic."""
import os
import sys

APP = "USBWatch"
AUTOSTART = "--autostart" in sys.argv

# Device "Properties" GUID that holds install/connect/disconnect timestamps.
PROP = r"{83da6326-97a6-4088-9453-a1923f573b29}"
PROP_CODES = {"install": "0064", "first_install": "0065", "connect": "0066", "disconnect": "0067"}

SETUPAPI = "Windows setupapi.dev.log (USB install history)"
MODES = {"Off": "off", "Blacklist": "blacklist", "Whitelist only": "whitelist"}
SIZE_OPTS = {"25 MB": 25, "100 MB": 100, "500 MB": 500, "2 GB": 2048}
CAP_OPTS = {"2 GB": 2, "5 GB": 5, "20 GB": 20, "50 GB": 50}


def _data_dir():
    for base in (os.environ.get("ProgramData"), os.environ.get("APPDATA")):
        if not base:
            continue
        p = os.path.join(base, APP)
        try:
            os.makedirs(p, exist_ok=True)
            t = os.path.join(p, ".w")
            open(t, "w").close()
            os.remove(t)
            return p
        except OSError:
            continue
    sys.exit("No writable data directory.")


DATA = _data_dir() if os.name == "nt" else os.path.join(os.path.expanduser("~"), ".usbwatch")
CFG = os.path.join(DATA, "config.json")
DB = os.path.join(DATA, "events.db")
LOGDIR = os.path.join(DATA, "logs")
