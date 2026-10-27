"""Plain data models shared across the app (no behaviour, no I/O)."""
from .device import Device
from .activity import ActivityEvent

__all__ = ["Device", "ActivityEvent"]
