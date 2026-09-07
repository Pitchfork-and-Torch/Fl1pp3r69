"""Minimal localhost-only HTTP dashboard for vault timeline/audit."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from flipper69.audit import audit_vault
from flipper69.vault import default_ops_root, iter_ops, read_operation, read_timeline


def _html_index(ops_root: Path) -> str:
    rows = []
    for op_dir in iter_ops(ops_root):
        op = read_operation(op_dir) or {}
        rows.append(
            f"<tr><td><a href='/op/{op_dir.name}'>{op_dir.name}</a></td>"
            f"<td>{op.get('opType','?')}</td><td>{op.get('phase','?')}</td>"
            f"<td>{op.get('schemaVersion',2)}</td></tr>"
        )
    summary = audit_vault(ops_root)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>Fl1pp3r69 ARGUS VEIL</title>
<style>
body{{font-family:ui-monospace,Consolas,monospace;background:#0a0a0c;color:#e8e8e8;margin:2rem}}
a{{color:#c41e1e}} table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #333;padding:.4rem;text-align:left}} th{{color:#ffb000}}
.badge{{color:#39ff14}}
</style></head><body>
<h1>FL1PP3R69 // ARGUS VEIL</h1>
<p class="badge">localhost only · audit PASS={summary['passed']} FAIL={summary['failed']}</p>
<table><tr><th>opId</th><th>type</th><th>phase</th><th>schema</th></tr>
{''.join(rows) or '<tr><td colspan=4>empty vault</td></tr>'}
</table>
<p><a href="/audit.json">audit.json</a></p>
</body></html>"""


def _html_op(op_dir: Path) -> str:
    op = read_operation(op_dir) or {}
    tl = read_timeline(op_dir)
    events = "".join(
        f"<tr><td>{e.get('ts','')}</td><td>{e.get('event',e.get('phase',''))}</td>"
        f"<td><code>{e.get('detail', e.get('data',''))}</code></td></tr>"
        for e in tl
    )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>{op_dir.name}</title>
<style>
body{{font-family:ui-monospace,Consolas,monospace;background:#0a0a0c;color:#e8e8e8;margin:2rem}}
a{{color:#c41e1e}} code{{color:#39ff14}} table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #333;padding:.35rem;text-align:left;font-size:.85rem}}
</style></head><body>
<p><a href="/">&larr; vault</a></p>
<h1>{op_dir.name}</h1>
<pre>{json.dumps(op, indent=2)}</pre>
<h2>Timeline</h2>
<table><tr><th>ts</th><th>event</th><th>detail</th></tr>{events}</table>
</body></html>"""


def run_dashboard(host: str = "127.0.0.1", port: int = 8769, ops_root: Path | None = None) -> None:
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("dashboard binds localhost only for OPSEC")
    root = ops_root or default_ops_root()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # noqa: N802
            return

        def do_GET(self):  # noqa: N802
            path = urlparse(self.path).path
            if path == "/":
                body = _html_index(root).encode("utf-8")
                ctype = "text/html; charset=utf-8"
            elif path == "/audit.json":
                body = json.dumps(audit_vault(root), indent=2).encode("utf-8")
                ctype = "application/json"
            elif path.startswith("/op/"):
                op_id = path.split("/op/", 1)[1]
                op_dir = root / "operations" / op_id
                if not op_dir.is_dir():
                    self.send_error(404)
                    return
                body = _html_op(op_dir).encode("utf-8")
                ctype = "text/html; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"dashboard http://{host}:{port}/  vault={root}")
    httpd.serve_forever()
