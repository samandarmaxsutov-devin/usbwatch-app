"""Small pure helpers shared across layers."""
import datetime as dt


def now_str():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fmt_size(n):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return ""
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return f"{n:.0f} B" if u == "B" else f"{n:.1f} {u}"
        n /= 1024
