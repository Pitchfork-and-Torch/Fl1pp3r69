"""Chain-of-custody HTML (and optional PDF) reports."""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flipper69 import __classification__, __release__, __version__
from flipper69.audit import audit_op
from flipper69.vault import read_manifest, read_operation, read_timeline


def _esc(s: Any) -> str:
    return html.escape("" if s is None else str(s))


def build_report_html(op_dir: Path) -> str:
    op = read_operation(op_dir) or {}
    man = read_manifest(op_dir) or {}
    audit = audit_op(op_dir)
    timeline = read_timeline(op_dir)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    items_rows = []
    for item in man.get("items") or []:
        if not isinstance(item, dict):
            continue
        items_rows.append(
            "<tr>"
            f"<td>{_esc(item.get('type'))}</td>"
            f"<td><code>{_esc(item.get('path'))}</code></td>"
            f"<td><code>{_esc(item.get('hash'))}</code></td>"
            f"<td>{_esc(item.get('sizeBytes', ''))}</td>"
            f"<td>{_esc(item.get('probe', ''))}</td>"
            "</tr>"
        )

    tl_rows = []
    for ev in timeline:
        tl_rows.append(
            "<tr>"
            f"<td>{_esc(ev.get('ts', ''))}</td>"
            f"<td>{_esc(ev.get('event', ev.get('phase', '')))}</td>"
            f"<td><code>{_esc(ev.get('detail', ev.get('data', '')))}</code></td>"
            "</tr>"
        )

    status_color = "#39ff14" if audit["status"] == "PASS" else "#c41e1e"
    issues_html = "".join(f"<li>{_esc(i)}</li>" for i in audit["issues"]) or "<li>None</li>"
    warn_html = "".join(f"<li>{_esc(w)}</li>" for w in audit["warnings"]) or "<li>None</li>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>CASEFILE Report — {_esc(op_dir.name)}</title>
<style>
  body {{ font-family: ui-monospace, Consolas, monospace; background:#0a0a0c; color:#e8e8e8; margin:2rem; }}
  h1,h2 {{ color:#c41e1e; }}
  .badge {{ display:inline-block; padding:0.2rem 0.6rem; border:1px solid {status_color}; color:{status_color}; }}
  table {{ border-collapse:collapse; width:100%; margin:1rem 0; font-size:0.85rem; }}
  th,td {{ border:1px solid #333; padding:0.4rem 0.5rem; text-align:left; vertical-align:top; }}
  th {{ background:#1a1a22; color:#ffb000; }}
  code {{ color:#39ff14; word-break:break-all; }}
  .meta {{ color:#8b8b8b; }}
  footer {{ margin-top:2rem; border-top:1px solid #333; padding-top:1rem; color:#8b8b8b; font-size:0.8rem; }}
  .box {{ background:#1a1a22; padding:1rem; border-left:3px solid #c41e1e; margin:1rem 0; }}
</style>
</head>
<body>
<h1>FL1PP3R69 // CASEFILE REPORT</h1>
<p class="meta">{_esc(__release__)} · toolkit v{_esc(__version__)} · {_esc(__classification__)}</p>
<p><span class="badge">{_esc(audit["status"])}</span> generated { _esc(now) }</p>

<div class="box">
  <strong>Operation</strong><br/>
  opId: <code>{_esc(op.get("opId", op_dir.name))}</code><br/>
  codename: {_esc(op.get("codename", "—"))}<br/>
  type: {_esc(op.get("opType", "—"))} · phase: {_esc(op.get("phase", "—"))}<br/>
  opened: {_esc(op.get("openedAt", "—"))}<br/>
  device: {_esc((op.get("device") or {}).get("firmware", "flipper69"))}
  @ {_esc((op.get("device") or {}).get("version", "—"))}<br/>
  schemaVersion: {_esc(audit.get("schemaVersion"))} · chainPrev: <code>{_esc(man.get("chainPrev"))}</code>
</div>

<h2>1. Scope &amp; authorization</h2>
<p>This report documents a <strong>manifest-driven physical-layer research operation</strong>.
Captures are integrity-hashed (SHA-256). The operator affirms use only on
<strong>owned or explicitly authorized</strong> systems. This software is not legal advice
and contains no exploit, jamming, or region-bypass tooling.</p>
<p>Target authorized flag: <code>{_esc((op.get("target") or {}).get("authorized", op.get("permissions", {}).get("authorized", "unspecified")))}</code></p>

<h2>2. Integrity result</h2>
<ul>
  <li>Hashes verified OK: {_esc(audit["verify"].get("ok", 0))}</li>
  <li>Issues:<ul>{issues_html}</ul></li>
  <li>Warnings:<ul>{warn_html}</ul></li>
</ul>

<h2>3. Artifact inventory</h2>
<table>
  <tr><th>type</th><th>path</th><th>sha256</th><th>bytes</th><th>probe</th></tr>
  {"".join(items_rows) or "<tr><td colspan='5'>No manifest items</td></tr>"}
</table>

<h2>4. Timeline (chain-of-custody events)</h2>
<table>
  <tr><th>ts</th><th>event</th><th>detail</th></tr>
  {"".join(tl_rows) or "<tr><td colspan='3'>No timeline</td></tr>"}
</table>

<h2>5. Chain-of-custody summary</h2>
<ol>
  <li>On-device CAPTURE under staged CASEFILE op.</li>
  <li>VERIFY produced CASEFILE-MANIFEST.json (schemaVersion {_esc(man.get("schemaVersion", 2))}).</li>
  <li>EXFIL deliberate (USB serial or SD import).</li>
  <li>Desktop re-verification: <strong style="color:{status_color}">{_esc(audit["status"])}</strong>.</li>
</ol>

<footer>
  Fl1pp3r69 {_esc(__release__)} · The dolphin grew teeth. The veil hides the op. The ledger never lies.<br/>
  MIT License · Authorized field research only · Do not publish exploit derivatives.
</footer>
</body>
</html>
"""


def write_report(op_dir: Path, out_path: Path) -> Path:
    html_doc = build_report_html(op_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_doc, encoding="utf-8")
    return out_path


def try_write_pdf(op_dir: Path, out_path: Path) -> Path | None:
    """Optional PDF via reportlab if installed."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        return None

    op = read_operation(op_dir) or {}
    audit = audit_op(op_dir)
    c = canvas.Canvas(str(out_path), pagesize=letter)
    width, height = letter
    y = height - 48
    c.setFont("Courier-Bold", 14)
    c.drawString(48, y, "FL1PP3R69 CASEFILE REPORT — VEIL LEDGER")
    y -= 24
    c.setFont("Courier", 10)
    for line in [
        f"opId: {op_dir.name}",
        f"status: {audit['status']}",
        f"type: {op.get('opType')}  phase: {op.get('phase')}",
        f"classification: {__classification__}",
        "",
        "Hashes re-verified on desktop. Authorized research only.",
        "Full inventory: open companion HTML report.",
    ]:
        c.drawString(48, y, line[:90])
        y -= 14
    c.showPage()
    c.save()
    return out_path
