"""A USB device as shown in the Devices / All-USB inventory tables."""
from dataclasses import dataclass


@dataclass
class Device:
    # identity
    name: str = ""              # FriendlyName or best-effort label
    description: str = ""       # DeviceDesc
    serial: str = ""            # instance serial (USBSTOR serial / USB instance id tail)
    instance_id: str = ""       # full PnP instance id (USB\... or USBSTOR\...)
    # classification
    device_type: str = ""       # friendly type ("Mass Storage", "Keyboard", ...)
    usb_class: str = ""         # raw Class string from the registry
    vid: str = ""
    pid: str = ""
    vendor: str = ""            # Ven_ code (USBSTOR) when no VID
    product: str = ""           # Prod_ code (USBSTOR)
    vendor_name: str = ""       # Manufacturer string
    service: str = ""           # driver service name
    # live status
    connected: bool = False     # device is present now
    disabled: bool = False      # device is disabled in Device Manager
    drive: str = ""             # drive letter(s) for storage, e.g. "F:"
    is_storage: bool = False    # True for USBSTOR / disk devices
    # history (from the device Properties timestamps)
    first_install: str = ""
    last_connect: str = ""
    last_disconnect: str = ""

    @property
    def vidpid(self) -> str:
        if self.vid and self.pid:
            return f"{self.vid}:{self.pid}"
        return ""
