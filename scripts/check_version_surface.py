#!/usr/bin/env python3
"""Fail if advertised product version or authorized-use copy drifts.

Product version is 4.0.0 ARGUS VEIL. Historical v3 demo ops under examples/
are allowed to keep 3.0.0 stamps. Cache-bust ?v= on CSS/JS must be the
product version or an 8-digit date (YYYYMMDD), not a fake product release.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "4.0.0"
RELEASE = "ARGUS VEIL"

FAILS: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        FAILS.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")


def need(rel: str, needle: str) -> None:
    text = read(rel)
    if text and needle not in text:
        FAILS.append(f"{rel}: missing {needle!r}")


def main() -> int:
    init = read("desktop/flipper69/__init__.py")
    ver = re.search(r'__version__\s*=\s*"([^"]+)"', init)
    rel = re.search(r'__release__\s*=\s*"([^"]+)"', init)
    if not ver or ver.group(1) != PRODUCT:
        FAILS.append(f"desktop __version__ is {ver.group(1) if ver else None}, want {PRODUCT}")
    if not rel or rel.group(1) != RELEASE:
        FAILS.append(f"desktop __release__ is {rel.group(1) if rel else None}, want {RELEASE}")
    if "VEIL LEDGER" in init:
        FAILS.append("desktop/flipper69/__init__.py still says VEIL LEDGER")

    pyproject = read("desktop/pyproject.toml")
    if f'version = "{PRODUCT}"' not in pyproject:
        FAILS.append("desktop/pyproject.toml version mismatch")

    lib = read("fap/libf69/f69_common.h")
    if f'#define F69_LIB_VER      "{PRODUCT}"' not in lib:
        FAILS.append("fap/libf69/f69_common.h F69_LIB_VER mismatch")

    landing = read("landing/index.html")
    need("landing/index.html", f'"softwareVersion": "{PRODUCT}"')
    need("landing/index.html", f'<span class="badge blood">v{PRODUCT}</span>')
    need("landing/index.html", "Authorized ops only")
    need("landing/index.html", "no exploit PoCs")
    need("landing/index.html", "no undocumented attack procedures")
    if "hits.jonbailey.xyz" in landing:
        FAILS.append("landing/index.html still loads third-party hits.jonbailey.xyz (CSP-blocked)")

    for attr in ('href="/css/site.css?v=', 'src="/js/site.js?v='):
        m = re.search(re.escape(attr) + r'([^"]+)"', landing)
        if not m:
            FAILS.append(f"landing/index.html: missing {attr}")
            continue
        token = m.group(1)
        if token != PRODUCT and not re.fullmatch(r"20\d{6}", token):
            FAILS.append(f"cache-bust {attr}{token} is not {PRODUCT} or YYYYMMDD")

    need("landing/llms.txt", f"**Version:** {PRODUCT}")
    need("landing/llms.txt", "Last reviewed: 2026-09-01")
    need("landing/llms.txt", "Authorized use")
    need("landing/llms.txt", "No exploit PoCs")
    need("landing/llms.txt", "No undocumented attack procedures")

    need("SECURITY.md", "4.x (ARGUS VEIL)")
    need("SECURITY.md", "Authorized use")
    need("SECURITY.md", "Exploit proof-of-concepts")
    need("CHANGELOG.md", PRODUCT)
    need("README.md", "Authorized ops only")
    need("landing/sitemap.xml", "<lastmod>2026-09-01</lastmod>")

    headers = read("landing/_headers")
    if "/llms.txt" in headers and "must-revalidate" not in headers.split("/llms.txt", 1)[1].split("\n\n", 1)[0]:
        FAILS.append("landing/_headers: /llms.txt must be must-revalidate so AEO copy does not go sticky")

    sync = read("desktop/flipper69/sync.py")
    if re.search(r'"ver":\s*"3\.0\.0"', sync):
        FAILS.append("desktop/flipper69/sync.py still hardcodes ver 3.0.0")
    if "from flipper69 import __version__" not in sync:
        FAILS.append("desktop/flipper69/sync.py should stamp __version__")

    wrangler = ROOT / ".wrangler" / "cache"
    if wrangler.is_dir() and any(wrangler.iterdir()):
        FAILS.append(".wrangler/cache still has files; keep deploy cache out of git")

    if FAILS:
        print("version surface FAILED:")
        for item in FAILS:
            print(f"  - {item}")
        return 1
    print(f"version surface OK — product {PRODUCT} {RELEASE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
