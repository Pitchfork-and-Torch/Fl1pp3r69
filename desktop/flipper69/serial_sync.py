"""USB serial JSON-lines exfil listener (optional pyserial)."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from typing import Any

from flipper69.hashutil import sha256_bytes, sha256_file
from flipper69.sync import append_timeline
from flipper69.vault import ensure_vault, operations_dir


def _try_import_serial():
    try:
        import serial  # type: ignore
        from serial.tools import list_ports  # type: ignore

        return serial, list_ports
    except ImportError:
        return None, None


def find_port(preferred: str | None = None) -> str | None:
    serial, list_ports = _try_import_serial()
    if serial is None:
        return None
    if preferred and preferred not in ("auto", ""):
        return preferred
    for p in list_ports.comports():
        desc = (p.description or "") + (p.manufacturer or "")
        if any(k in desc for k in ("Flipper", "STM32", "USB Serial", "CDC")):
            return p.device
    ports = list(list_ports.comports())
    return ports[0].device if ports else None


def listen_serial(
    port: str | None = "auto",
    ops_root: Path | None = None,
    *,
    once: bool = False,
    baud: int = 115200,
) -> dict[str, Any]:
    serial, _ = _try_import_serial()
    if serial is None:
        raise RuntimeError("pyserial not installed. pip install pyserial")

    ensure_vault(ops_root)
    resolved = find_port(port)
    if not resolved:
        raise RuntimeError("No serial port found")

    dest = operations_dir(ops_root)
    ser = serial.Serial(resolved, baud, timeout=1)
    current: str | None = None
    op_path: Path | None = None
    closed = 0
    print(f"listening {resolved} @ {baud} -> {dest}", file=sys.stderr)

    try:
        while True:
            try:
                raw = ser.readline()
            except Exception:
                continue
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").strip()
            if not line.startswith("{"):
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            mtype = msg.get("type")
            if mtype == "ping":
                ser.write((json.dumps({"type": "pong"}) + "\n").encode("utf-8"))
                continue
            if mtype == "op_header":
                current = msg.get("opId")
                if not current:
                    continue
                op_path = dest / current
                op_path.mkdir(parents=True, exist_ok=True)
                (op_path / "captures").mkdir(exist_ok=True)
                append_timeline(op_path, "serial_op_header", {"opId": current})
                print(f"[>] HEADER {current}")
            elif mtype == "manifest" and op_path:
                (op_path / "CASEFILE-MANIFEST.json").write_text(
                    json.dumps(msg, indent=2) + "\n", encoding="utf-8"
                )
                print("[+] MANIFEST")
            elif mtype == "artifact" and op_path:
                rel = msg.get("path") or "captures/artifact.bin"
                target = op_path / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                b64 = msg.get("b64") or ""
                data = base64.b64decode(b64) if b64 else b""
                target.write_bytes(data)
                expected = (msg.get("sha256") or "").lower()
                if expected and sha256_bytes(data) != expected:
                    append_timeline(op_path, "hash_mismatch", {"path": rel})
                    print(f"[!] HASH MISMATCH {rel}")
                else:
                    print(f"[+] ARTIFACT {rel}")
            elif mtype == "op_close" and op_path:
                append_timeline(op_path, "serial_op_close", {"manifestHash": msg.get("manifestHash")})
                # write receipt without poisoning CASEFILE timeline hash set
                receipt = op_path / "DESKTOP-RECEIPTS.jsonl"
                receipt.write_text(
                    receipt.read_text(encoding="utf-8") if receipt.exists() else ""
                    + json.dumps({"event": "serial_close", "opId": current})
                    + "\n",
                    encoding="utf-8",
                )
                print(f"[+] CLOSE {current} -> {op_path}")
                closed += 1
                if once:
                    break
                current = None
                op_path = None
    finally:
        ser.close()
    return {"closed": closed, "vault": str(dest), "port": resolved}
