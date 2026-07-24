#!/usr/bin/env python3
"""Portable orchestrator for Fl1pp3r69 v3 builds (desktop checks + optional FAP)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path | None = None) -> int:
    print("+", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(cwd or ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Fl1pp3r69 VEIL LEDGER build orchestrator")
    p.add_argument("--desktop", action="store_true", help="Install + test desktop package")
    p.add_argument("--schemas", action="store_true", help="Parse all JSON schemas")
    p.add_argument("--fap", action="store_true", help="Invoke build-fap.ps1 -App all (Windows/PowerShell)")
    p.add_argument("--all", action="store_true", help="desktop + schemas")
    args = p.parse_args()

    if not any([args.desktop, args.schemas, args.fap, args.all]):
        args.all = True

    if args.all or args.schemas:
        for path in sorted((ROOT / "schemas").glob("*.json")):
            json.loads(path.read_text(encoding="utf-8"))
            print("schema OK", path.name)

    if args.all or args.desktop:
        code = run([sys.executable, "-m", "pip", "install", "-e", str(ROOT / "desktop") + "[dev]"])
        if code != 0:
            return code
        code = run([sys.executable, "-m", "pytest", "-q", str(ROOT / "desktop" / "tests")])
        if code != 0:
            return code

    if args.fap:
        ps1 = ROOT / "scripts" / "build-fap.ps1"
        code = run(["powershell", "-NoProfile", "-File", str(ps1), "-App", "all"])
        if code != 0:
            return code

    print("build_all: done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
