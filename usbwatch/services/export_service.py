"""Export a table (headers + rows) to CSV / HTML / TXT — the USBDeview-style report."""
import csv
import datetime as dt
import html
import io

from .. import config


def _csv(headers, rows):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    w.writerows(rows)
    return buf.getvalue()


def _txt(headers, rows):
    widths = [len(h) for h in headers]
    for r in rows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(str(c)))
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    out = [line, "  ".join("-" * widths[i] for i in range(len(headers)))]
    for r in rows:
        out.append("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)))
    return "\n".join(out) + "\n"


def _html(headers, rows, title):
    esc = html.escape
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "\n".join(
        "<tr>" + "".join(f"<td>{esc(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{esc(title)}</title>
<style>
 body{{font-family:Segoe UI,Arial,sans-serif;background:#16181d;color:#e5e7eb;margin:24px}}
 h1{{font-size:20px}} .meta{{color:#9ca3af;margin-bottom:16px}}
 table{{border-collapse:collapse;width:100%;font-size:13px}}
 th,td{{border:1px solid #2b303b;padding:6px 8px;text-align:left}}
 th{{background:#272b34}} tr:nth-child(even){{background:#1e2128}}
</style></head><body>
<h1>{esc(title)}</h1>
<div class="meta">{esc(config.APP)} report &middot; {len(rows)} device(s) &middot; {dt.datetime.now():%Y-%m-%d %H:%M:%S}</div>
<table><thead><tr>{head}</tr></thead>
<tbody>
{body}
</tbody></table></body></html>"""


def export(headers, rows, fmt, path, title="USB Devices"):
    """fmt in {'csv','html','txt'}. Writes UTF-8 (BOM for csv)."""
    fmt = fmt.lower()
    if fmt == "csv":
        text, enc = _csv(headers, rows), "utf-8-sig"
    elif fmt == "html":
        text, enc = _html(headers, rows, title), "utf-8"
    else:
        text, enc = _txt(headers, rows), "utf-8"
    with open(path, "w", encoding=enc, newline="") as f:
        f.write(text)
    return path
