"""A single file-activity / device event row."""
from dataclasses import dataclass


@dataclass
class ActivityEvent:
    ts: str = ""        # "YYYY-MM-DD HH:MM:SS"
    drive: str = ""     # e.g. "F:\\"
    action: str = ""    # Created / Modified / Deleted / Renamed/Moved / Mounted / Blocked ...
    path: str = ""
    dest: str = ""      # rename destination, label, or device id depending on action
    size: str = ""
    serial: str = ""

    def as_row(self):
        """6-tuple used by the activity tables (no serial column)."""
        return (self.ts, self.drive, self.action, self.path, self.dest, self.size)

    def as_db_row(self):
        return (self.ts, self.drive, self.action, self.path, self.dest, self.size, self.serial)
