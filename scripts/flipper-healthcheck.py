#!/usr/bin/env python3
"""USB health check for Flipper Zero + Fl1pp3r69 v2 install."""
import os
import sys

from pathlib import Path

ufbt_scripts = Path.home() / ".ufbt" / "current" / "scripts"
sys.path.insert(0, str(ufbt_scripts))

from flipper.storage import FlipperStorage
from flipper.utils.cdc import resolve_port

F69_VER = "2.0.0"
PORT = os.environ.get("FLIPPER_PORT", "auto")
FAPS = [
    "/ext/apps/flipper69_casefile_ops.fap",
    "/ext/apps/NFC/flipper69_probe_nfc.fap",
    "/ext/apps/flipper69_probe_subghz.fap",
    "/ext/apps/flipper69_manifest_viewer.fap",
]
OPS_ROOT = "/ext/flipper69"
OPS_INDEX = "/ext/flipper69/index.json"
OPS_DIR = "/ext/flipper69/operations"


def run_cli(storage, cmd):
    storage.send(cmd + "\r")
    out = storage.read.until(storage.CLI_PROMPT).decode("ascii", errors="replace")
    return out.replace("\r", "").strip()


def stat_file(storage, path):
    storage.send_and_wait_eol(f'storage stat "{path}"\r')
    data = storage.read.until(storage.CLI_PROMPT).decode("ascii", errors="replace")
    if "Storage error" in data:
        return None
    for line in data.split("\n"):
        line = line.strip()
        if line.startswith("size:"):
            return line.split(":", 1)[1].strip()
    return "?"


def main():
    port = resolve_port(None, PORT)
    if not port:
        print("USB ERROR: Flipper not found. Set FLIPPER_PORT or plug in device.")
        print("Tips: close qFlipper, press Back to desktop, unplug/replug USB.")
        return 1

    print(f"Connecting to {port}...")
    try:
        storage = FlipperStorage(port)
        storage.start()
    except Exception as e:
        print(f"USB ERROR: {e}")
        print("Tips: close qFlipper, press Back to desktop, unplug/replug USB.")
        return 1

    try:
        print(f"=== FL1PP3R69 HEALTH v{F69_VER} ===")
        print("=== DEVICE INFO ===")
        print(run_cli(storage, "device_info"))

        print("\n=== SD CARD (/ext) ===")
        print(run_cli(storage, "storage info /ext"))

        print("\n=== FL1PP3R69 FAP FILES ===")
        ok = 0
        for path in FAPS:
            size = stat_file(storage, path)
            if size is None:
                print(f"MISSING: {path}")
            else:
                print(f"OK: {path} ({size} bytes)")
                ok += 1
        print(f"FAPs: {ok}/{len(FAPS)}")

        print("\n=== FLIPPER69 OPS LAYOUT ===")
        for path in (OPS_ROOT, OPS_DIR, OPS_INDEX):
            size = stat_file(storage, path)
            label = "OK" if size is not None else "MISSING"
            print(f"{label}: {path}" + (f" ({size})" if size else ""))

        print("\n=== APP LOAD TEST ===")
        run_cli(storage, "loader close")
        storage.send('loader open "/ext/apps/flipper69_casefile_ops.fap"\r')
        resp = storage.read.until(storage.CLI_EOL).decode("ascii", errors="replace").strip()
        print(resp or "(launching...)")
        storage.port.timeout = 2
        try:
            tail = storage.read.until(storage.CLI_PROMPT).decode("ascii", errors="replace").strip()
            if tail and tail != ":":
                print(tail)
        except Exception:
            print("(app running — CLI yielded, expected)")

        low = (resp or "").lower()
        load_ok = "error" not in low and "fail" not in low
        print("LOAD:", "OK" if load_ok else "FAILED")

        print("\n=== POWER ===")
        print(run_cli(storage, "power info"))

        print("\n=== VERDICT ===")
        if ok == len(FAPS) and load_ok:
            print(f"Healthy v{F69_VER}: USB, SD, all 4 apps, CASEFILE Ops loads.")
        elif ok == len(FAPS):
            print("Apps on SD OK; load test inconclusive — open CASEFILE Ops manually.")
        else:
            print("Issue: missing files on SD. Rebuild with scripts/build-fap.ps1 -App all")
        return 0 if ok == len(FAPS) else 2
    finally:
        storage.stop()


if __name__ == "__main__":
    raise SystemExit(main())