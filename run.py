"""Entry point: `python run.py` (add --autostart for the logon task)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if os.name != "nt":
    sys.exit("USBWatch runs on Windows only.")

from usbwatch.app import run  # noqa: E402

if __name__ == "__main__":
    run()
