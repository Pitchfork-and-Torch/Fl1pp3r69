"""flipper69 CLI — VEIL LEDGER desktop toolkit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from flipper69 import __release__, __version__
from flipper69.audit import audit_op, audit_vault
from flipper69.dashboard import run_dashboard
from flipper69.migrate import migrate_vault
from flipper69.pack import pack_op
from flipper69.report import try_write_pdf, write_report
from flipper69.seal import seal_op
from flipper69.sync import import_sd
from flipper69.templates import apply_template, list_templates
from flipper69.tui import run_tui
from flipper69.vault import default_ops_root, iter_ops, op_path, read_operation, read_timeline


def _banner() -> None:
    print()
    print("  +----------------------------------------------+")
    print(f"  |  FL1PP3R69 DESKTOP  v{__version__:<6}  {__release__:<12} |")
    print("  |  the dolphin grew teeth · ledger never lies  |")
    print("  +----------------------------------------------+")
    print()


def cmd_sync(args: argparse.Namespace) -> int:
    if getattr(args, "serial", None):
        try:
            from flipper69.serial_sync import listen_serial
        except Exception as e:  # pragma: no cover
            print(f"error: {e}", file=sys.stderr)
            return 2
        try:
            result = listen_serial(
                args.serial,
                Path(args.vault) if args.vault else None,
                once=bool(getattr(args, "once", False)),
            )
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2))
        return 0
    if not args.sd:
        print("error: --sd PATH or --serial auto required", file=sys.stderr)
        return 2
    result = import_sd(Path(args.sd), Path(args.vault) if args.vault else None)
    print(f"IMPORT COMPLETE  ops={result['imported']}  hashes_ok={result['hashes_ok']}")
    print(f"vault: {result['vault']}")
    for r in result["results"]:
        flag = "OK" if r["pass"] else "FAIL"
        print(f"  [{flag}] {r['opId']}  match={r['ok']}  miss={len(r['missing'])}  bad={len(r['mismatch'])}")
    return 0 if all(r["pass"] for r in result["results"]) or result["imported"] == 0 else 1


def cmd_seal(args: argparse.Namespace) -> int:
    p = op_path(args.op_id, Path(args.vault) if args.vault else None)
    if not p.is_dir():
        print(f"error: op not found: {args.op_id}", file=sys.stderr)
        return 2
    result = seal_op(p, merkle=not args.no_merkle, chunk_size=args.chunk_size)
    print(json.dumps(result, indent=2))
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    try:
        run_dashboard(
            host=args.bind,
            port=args.port,
            ops_root=Path(args.vault) if args.vault else None,
        )
    except KeyboardInterrupt:
        return 0
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    root = Path(args.vault) if args.vault else None
    if args.op_id:
        p = op_path(args.op_id, root)
        if not p.is_dir():
            print(f"error: op not found: {args.op_id}", file=sys.stderr)
            return 2
        report = audit_op(p)
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "PASS" else 1
    summary = audit_vault(root)
    print(f"AUDIT  ops={summary['ops']}  PASS={summary['passed']}  FAIL={summary['failed']}")
    for r in summary["reports"]:
        print(f"  [{r['status']}] {r['opId']}  issues={len(r['issues'])}  orphans={len(r['orphans'])}")
    return 0 if summary["failed"] == 0 else 1


def cmd_list(args: argparse.Namespace) -> int:
    root = Path(args.vault) if args.vault else None
    for p in iter_ops(root):
        op = read_operation(p) or {}
        if args.type and op.get("opType") != args.type:
            continue
        if args.phase and str(op.get("phase", "")).lower() != args.phase.lower():
            continue
        if args.q:
            blob = json.dumps(op).lower()
            if args.q.lower() not in blob and args.q.lower() not in p.name.lower():
                continue
        print(
            f"{p.name}\ttype={op.get('opType', '?')}\tphase={op.get('phase', '?')}\t"
            f"schema={op.get('schemaVersion', 2)}"
        )
    return 0


def cmd_timeline(args: argparse.Namespace) -> int:
    p = op_path(args.op_id, Path(args.vault) if args.vault else None)
    if not p.is_dir():
        print(f"error: op not found: {args.op_id}", file=sys.stderr)
        return 2
    for ev in read_timeline(p):
        ts = ev.get("ts", "")
        event = ev.get("event", ev.get("phase", "?"))
        detail = ev.get("detail", ev.get("data", ""))
        print(f"{ts}\t{event}\t{detail}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    p = op_path(args.op_id, Path(args.vault) if args.vault else None)
    if not p.is_dir():
        print(f"error: op not found: {args.op_id}", file=sys.stderr)
        return 2
    out = Path(args.output) if args.output else Path(f"{args.op_id}-report.html")
    write_report(p, out)
    print(f"HTML report: {out}")
    if args.pdf:
        pdf_path = Path(args.pdf)
        got = try_write_pdf(p, pdf_path)
        if got:
            print(f"PDF report: {got}")
        else:
            print("PDF skipped (install: pip install reportlab)", file=sys.stderr)
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    root = Path(args.vault) if args.vault else None
    result = migrate_vault(root)
    print(f"MIGRATED ops={result['migrated_ops']}")
    for r in result["results"]:
        flags = [k for k, v in r.items() if k != "opId" and v]
        print(f"  {r['opId']}: {', '.join(flags) or 'already v3'}")
    print(result["note"])
    return 0


def cmd_template(args: argparse.Namespace) -> int:
    extra = Path(args.templates_dir) if args.templates_dir else None
    if args.template_cmd == "list":
        for t in list_templates(extra):
            print(f"{t['templateId']}\t{t.get('opType')}\t{t.get('name')}")
        return 0
    if args.template_cmd == "apply":
        try:
            path = apply_template(
                args.template_id,
                label=args.label,
                ops_root=Path(args.vault) if args.vault else None,
                extra_dir=extra,
                acknowledge_auth=args.acknowledge_auth,
            )
        except (KeyError, PermissionError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"created {path}")
        return 0
    print("usage: template list|apply", file=sys.stderr)
    return 2


def cmd_pack(args: argparse.Namespace) -> int:
    p = op_path(args.op_id, Path(args.vault) if args.vault else None)
    if not p.is_dir():
        print(f"error: op not found: {args.op_id}", file=sys.stderr)
        return 2
    out = Path(args.output) if args.output else Path(f"{args.op_id}{'-redact' if args.redact else ''}.f69pack.zip")
    result = pack_op(p, out, redact=args.redact)
    print(json.dumps(result, indent=2))
    return 0


def _add_vault(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--vault",
        default=None,
        help="Ops root (default: ~/.flipper69/ops or FLIPPER69_OPS_ROOT)",
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="flipper69",
        description="Fl1pp3r69 VEIL LEDGER desktop toolkit — offline CASEFILE vault tools",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__} ({__release__})")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sync", help="Import ops from SD card tree and/or USB serial")
    _add_vault(s)
    s.add_argument("--sd", help="SD root or examples/sd_card path")
    s.add_argument("--serial", help="Serial port or 'auto' (requires pyserial)")
    s.add_argument("--once", action="store_true", help="Serial: exit after one op_close")
    s.set_defaults(func=cmd_sync)

    s = sub.add_parser("seal", help="Desktop re-seal op (merkle + schema v4)")
    _add_vault(s)
    s.add_argument("op_id")
    s.add_argument("--no-merkle", action="store_true")
    s.add_argument("--chunk-size", type=int, default=64)
    s.set_defaults(func=cmd_seal)

    s = sub.add_parser("dashboard", help="Localhost vault browser (127.0.0.1 only)")
    _add_vault(s)
    s.add_argument("--bind", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8769)
    s.set_defaults(func=cmd_dashboard)

    s = sub.add_parser("audit", help="Audit vault or single op")
    _add_vault(s)
    s.add_argument("op_id", nargs="?", help="Optional opId")
    s.set_defaults(func=cmd_audit)

    s = sub.add_parser("list", help="List/filter vault operations")
    _add_vault(s)
    s.add_argument("--type", help="Filter opType")
    s.add_argument("--phase", help="Filter phase")
    s.add_argument("-q", help="Search substring")
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("timeline", help="Print TIMELINE.jsonl")
    _add_vault(s)
    s.add_argument("op_id")
    s.set_defaults(func=cmd_timeline)

    s = sub.add_parser("report", help="Generate HTML CoC report")
    _add_vault(s)
    s.add_argument("op_id")
    s.add_argument("-o", "--output", help="HTML output path")
    s.add_argument("--pdf", help="Optional PDF path (requires reportlab)")
    s.set_defaults(func=cmd_report)

    s = sub.add_parser("migrate", help="Upgrade vault docs to schemaVersion 3")
    _add_vault(s)
    s.set_defaults(func=cmd_migrate)

    s = sub.add_parser("template", help="List or apply operation templates")
    _add_vault(s)
    s.add_argument("template_cmd", choices=["list", "apply"])
    s.add_argument("template_id", nargs="?")
    s.add_argument("--label", default="field")
    s.add_argument("--acknowledge-auth", action="store_true")
    s.add_argument("--templates-dir", help="Extra templates directory")
    s.set_defaults(func=cmd_template)

    s = sub.add_parser("pack", help="Export .f69pack zip (optional --redact)")
    _add_vault(s)
    s.add_argument("op_id")
    s.add_argument("-o", "--output")
    s.add_argument("--redact", action="store_true", help="Share-safe: strip notes/raw captures")
    s.set_defaults(func=cmd_pack)

    s = sub.add_parser("tui", help="Simple vault browser")
    s.set_defaults(func=lambda a: run_tui())

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd != "tui":
        _banner()
    # ensure default vault exists for friendliness
    default_ops_root().mkdir(parents=True, exist_ok=True)
    return int(args.func(args))
