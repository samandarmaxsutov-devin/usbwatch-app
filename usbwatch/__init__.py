"""USBWatch — USB device inventory, file-activity audit and access control (Windows).

Layered MVVM:
  models/      plain data (dataclasses)
  services/    system + storage access (registry, PnP, watchdog, sqlite, config)
  viewmodels/  presentation logic + observable state + commands (no Tkinter)
  views/       customtkinter widgets that bind to the view-models
"""
__version__ = "2.0.0"
