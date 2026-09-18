#!/usr/bin/env python3
"""Fail if advertised product version or authorized-use copy drifts.

Product version is 4.0.0 ARGUS VEIL. Historical v3 demo ops under examples/
are allowed to keep 3.0.0 stamps. Cache-bust ?v= on CSS/JS must be the
product version or an 8-digit date (YYYYMMDD), not a fake product release.
"""

from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "4.0.0"
RELEASE = "ARGUS VEIL"
HITS_HOST = "https://hits.jonbailey.xyz"
CSP = (
    "default-src 'self'; script-src 'self' https://hits.jonbailey.xyz; "
    "style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; "
    "connect-src 'self' https://hits.jonbailey.xyz; object-src 'none'; "
    "base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
)
FANCY = re.compile(r"[\u2013\u2014\u2018\u2019\u201c\u201d]")
FAP_APPID_RE = re.compile(r'appid="([^"]+)"')

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


def image_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        width, height = struct.unpack(">II", data[16:24])
        return width, height
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 8:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                height, width = struct.unpack(">HH", data[i + 5 : i + 9])
                return width, height
            if marker == 0xD9:
                break
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            length = struct.unpack(">H", data[i + 2 : i + 4])[0]
            i += 2 + length
        raise ValueError(f"no JPEG SOF in {path}")
    raise ValueError(f"unsupported image {path}")


def fap_appids() -> list[str]:
    ids: list[str] = []
    for fam in sorted((ROOT / "fap").glob("*/application.fam")):
        text = fam.read_text(encoding="utf-8")
        match = FAP_APPID_RE.search(text)
        if match:
            ids.append(match.group(1))
    return ids


def _csp_from_headers(text: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith("Content-Security-Policy:"):
            return line.split(":", 1)[1].strip()
    return ""


def _csp_from_worker(text: str) -> str:
    match = re.search(r'const CSP\s*=\s*\n?\s*"([^"]+)"', text)
    if match:
        return match.group(1)
    match = re.search(r'const CSP\s*=\s*"([^"]+)"', text)
    return match.group(1) if match else ""


def check_landing_honesty() -> None:
    landing = read("landing/index.html")
    need("landing/index.html", f'"softwareVersion": "{PRODUCT}"')
    need("landing/index.html", f'<span class="badge blood">v{PRODUCT}</span>')
    need("landing/index.html", "Authorized ops only")
    need("landing/index.html", "no exploit PoCs")
    need("landing/index.html", "no undocumented attack procedures")
    need("landing/index.html", 'href="#main"')
    need("landing/index.html", 'id="main"')
    need("landing/index.html", 'lang="en"')
    need("landing/index.html", 'role="tablist"')
    need("landing/index.html", 'src="https://hits.jonbailey.xyz/c.js"')
    need("landing/index.html", 'data-site="fl1pp3r69"')

    if "safedepositbox.org" in landing.lower():
        FAILS.append("landing/index.html lists closed SafeDeposit as live")

    for attr in (
        'href="/css/site.css?v=',
        'src="/js/site.js?v=',
        'src="/projects-panel.js?v=',
    ):
        match = re.search(re.escape(attr) + r'([^"]+)"', landing)
        if not match:
            FAILS.append(f"landing/index.html: missing {attr}")
            continue
        token = match.group(1)
        if token != PRODUCT and not re.fullmatch(r"20\d{6}", token):
            FAILS.append(f"cache-bust {attr}{token} is not {PRODUCT} or YYYYMMDD")

    for src in re.findall(r'(?:src|href)="(/assets/[^"?]+)(?:\?[^"]*)?"', landing):
        path = ROOT / "landing" / src.lstrip("/")
        if not path.is_file():
            FAILS.append(f"landing references missing asset {src}")

    cards = re.findall(r'<p class="fap-id">([^<]+)</p>', landing)
    appids = fap_appids()
    if len(appids) != 10:
        FAILS.append(f"fap application.fam count is {len(appids)}, want 10")
    if sorted(cards) != sorted(appids):
        FAILS.append(f"landing FAP ids {sorted(cards)} != fam appids {sorted(appids)}")

    faq_blocks = re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        landing,
        flags=re.S,
    )
    faq_names: list[str] = []
    for raw in faq_blocks:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            FAILS.append("landing/index.html: JSON-LD is not valid JSON")
            continue
        if data.get("@type") == "FAQPage":
            faq_names = [item.get("name", "") for item in data.get("mainEntity", [])]
    summaries = re.findall(r"<summary>([^<]+)</summary>", landing)
    for name in faq_names:
        if name not in summaries:
            FAILS.append(f"FAQ JSON-LD question missing from HTML: {name!r}")

    css = read("landing/css/site.css")
    need("landing/css/site.css", "prefers-reduced-motion")
    need("landing/css/site.css", "prefers-reduced-transparency")
    need("landing/css/site.css", "color-scheme: dark")
    if ".nav" in css and re.search(r"\.nav\s*\{[^}]*display:\s*none", css):
        FAILS.append("landing/css/site.css hides primary nav (keyboard path gone)")

    js = read("landing/js/site.js")
    need("landing/js/site.js", "aria-selected")
    need("landing/js/site.js", "ArrowRight")

    llms = read("landing/llms.txt")
    need("landing/llms.txt", f"**Version:** {PRODUCT}")
    if llms and not re.search(r"Last reviewed: 20\d{2}-\d{2}-\d{2}", llms):
        FAILS.append("landing/llms.txt: missing Last reviewed: YYYY-MM-DD")
    need("landing/llms.txt", "Authorized use")
    need("landing/llms.txt", "No exploit PoCs")
    need("landing/llms.txt", "No undocumented attack procedures")
    need("landing/llms.txt", "hits.jonbailey.xyz")
    if "safedepositbox.org" in llms.lower():
        FAILS.append("landing/llms.txt still lists SafeDeposit as a live related site")

    robots = read("landing/robots.txt")
    if "safedepositbox.org" in robots.lower():
        FAILS.append("landing/robots.txt still lists SafeDeposit as live")

    changelog = read("CHANGELOG.md")
    if re.search(r"hits script removed", changelog, flags=re.I):
        FAILS.append("CHANGELOG still claims the hits widget was removed")

    headers = read("landing/_headers")
    header_csp = _csp_from_headers(headers)
    if header_csp != CSP:
        FAILS.append("landing/_headers CSP is not lockstep with fleet hits allow-list")
    if "/llms.txt" in headers and "must-revalidate" not in headers.split("/llms.txt", 1)[1].split(
        "\n\n", 1
    )[0]:
        FAILS.append("landing/_headers: /llms.txt must be must-revalidate so AEO copy does not go sticky")

    worker = read("landing/worker.js")
    worker_csp = _csp_from_worker(worker)
    if worker_csp != CSP:
        FAILS.append("landing/worker.js CSP is not lockstep with _headers")

    share = ROOT / "landing" / "assets" / "share-card.jpg"
    hero = ROOT / "landing" / "assets" / "hero-argus-veil.jpg"
    og = ROOT / "landing" / "assets" / "og.jpg"
    try:
        if share.is_file() and image_size(share) != (1200, 630):
            FAILS.append(f"share-card.jpg is {image_size(share)}, want 1200x630")
        if hero.is_file() and image_size(hero) != (1600, 900):
            FAILS.append(f"hero-argus-veil.jpg is {image_size(hero)}, want 1600x900")
        if og.is_file() and image_size(og) != (1200, 630):
            FAILS.append(f"og.jpg is {image_size(og)}, want 1200x630")
    except ValueError as exc:
        FAILS.append(str(exc))

    for rel in (
        "landing/index.html",
        "landing/llms.txt",
        "landing/css/site.css",
        "landing/js/site.js",
        "landing/README.md",
    ):
        text = read(rel)
        if text and FANCY.search(text):
            FAILS.append(f"{rel}: fancy dash/quote in landing copy")


def collect_fails() -> list[str]:
    FAILS.clear()

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

    cli = read("desktop/flipper69/cli.py")
    if "schemaVersion 3" in cli:
        FAILS.append("desktop/flipper69/cli.py migrate help still says schemaVersion 3")
    if "already v3" in cli:
        FAILS.append("desktop/flipper69/cli.py migrate status still says already v3")

    check_landing_honesty()

    need("SECURITY.md", "4.x (ARGUS VEIL)")
    need("SECURITY.md", "Authorized use")
    need("SECURITY.md", "Exploit proof-of-concepts")
    need("CHANGELOG.md", PRODUCT)
    need("README.md", "Authorized ops only")
    sitemap = read("landing/sitemap.xml")
    if sitemap and not re.search(r"<lastmod>20\d{2}-\d{2}-\d{2}</lastmod>", sitemap):
        FAILS.append("landing/sitemap.xml: missing lastmod YYYY-MM-DD")

    sync = read("desktop/flipper69/sync.py")
    if re.search(r'"ver":\s*"3\.0\.0"', sync):
        FAILS.append("desktop/flipper69/sync.py still hardcodes ver 3.0.0")
    if "from flipper69 import __version__" not in sync:
        FAILS.append("desktop/flipper69/sync.py should stamp __version__")

    wrangler = ROOT / ".wrangler" / "cache"
    if wrangler.is_dir() and any(wrangler.iterdir()):
        FAILS.append(".wrangler/cache still has files; keep deploy cache out of git")

    return list(FAILS)


def main() -> int:
    fails = collect_fails()
    if fails:
        print("version surface FAILED:")
        for item in fails:
            print(f"  - {item}")
        return 1
    print(f"version surface OK - product {PRODUCT} {RELEASE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
