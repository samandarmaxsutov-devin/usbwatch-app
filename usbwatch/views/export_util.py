"""Shared 'Export…' helper: asks for a file name and writes CSV / HTML / TXT."""
import os
from tkinter import filedialog, messagebox

from .. import config
from ..i18n import t
from ..services import export_service


def export_tree(parent, tree, title="USB Devices"):
    """Export the current contents of a ttk Treeview, format chosen by extension."""
    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV", "*.csv"), ("HTML report", "*.html"), ("Text", "*.txt")])
    if not path:
        return
    ext = os.path.splitext(path)[1].lower()
    fmt = {".html": "html", ".htm": "html", ".txt": "txt"}.get(ext, "csv")
    headers = list(tree["columns"])
    rows = [tree.item(i)["values"] for i in tree.get_children()]
    try:
        export_service.export(headers, rows, fmt, path, title=title)
        messagebox.showinfo(config.APP, t("dlg.exported", path))
    except OSError as e:
        messagebox.showerror(config.APP, t("dlg.export_failed", e))
