"""Landing copy honesty, a11y gates, and asset lockstep."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from check_version_surface import (  # noqa: E402
    CSP,
    PRODUCT,
    _csp_from_headers,
    _csp_from_worker,
    collect_fails,
    fap_appids,
    image_size,
)


LANDING = ROOT / "landing"


def test_version_surface_script_is_green():
    assert collect_fails() == []


def test_hits_widget_and_csp_lockstep():
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    headers = (LANDING / "_headers").read_text(encoding="utf-8")
    worker = (LANDING / "worker.js").read_text(encoding="utf-8")
    assert 'src="https://hits.jonbailey.xyz/c.js"' in html
    assert 'data-site="fl1pp3r69"' in html
    assert _csp_from_headers(headers) == CSP
    assert _csp_from_worker(worker) == CSP
    assert "https://hits.jonbailey.xyz" in CSP
    assert "script-src 'self' https://hits.jonbailey.xyz" in CSP
    assert "connect-src 'self' https://hits.jonbailey.xyz" in CSP


def test_share_card_and_hero_dimensions():
    assert image_size(LANDING / "assets" / "share-card.jpg") == (1200, 630)
    assert image_size(LANDING / "assets" / "og.jpg") == (1200, 630)
    assert image_size(LANDING / "assets" / "hero-argus-veil.jpg") == (1600, 900)
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    assert 'width="1600"' in html and 'height="900"' in html
    assert 'og:image:width" content="1200"' in html
    assert 'og:image:height" content="630"' in html


def test_referenced_assets_exist():
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    for src in re.findall(r'(?:src|href)="(/assets/[^"?]+)(?:\?[^"]*)?"', html):
        path = LANDING / src.lstrip("/")
        assert path.is_file(), src


def test_ten_faps_match_application_fam():
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    cards = re.findall(r'<p class="fap-id">([^<]+)</p>', html)
    assert len(cards) == 10
    assert sorted(cards) == sorted(fap_appids())
    assert html.count("10 FAPs") >= 1 or "Ten FAPs" in html or "Exactly 10 FAPs" in html


def test_faq_json_ld_matches_visible_summaries():
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    summaries = re.findall(r"<summary>([^<]+)</summary>", html)
    names: list[str] = []
    for raw in re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        html,
        flags=re.S,
    ):
        data = json.loads(raw)
        if data.get("@type") == "FAQPage":
            names = [item["name"] for item in data["mainEntity"]]
    assert names
    assert summaries == names


def test_a11y_landmarks_and_pipeline_tabs():
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    css = (LANDING / "css" / "site.css").read_text(encoding="utf-8")
    js = (LANDING / "js" / "site.js").read_text(encoding="utf-8")
    assert 'class="skip-link" href="#main"' in html
    assert '<main id="main">' in html
    assert 'lang="en"' in html
    assert 'role="tablist"' in html
    assert 'aria-selected="true"' in html
    assert "prefers-reduced-motion" in css
    assert "prefers-reduced-transparency" in css
    assert "color-scheme: dark" in css
    assert "ArrowRight" in js
    assert "aria-selected" in js
    assert not re.search(r"\.nav\s*\{[^}]*display:\s*none", css)


def test_authorized_rails_not_a_theft_kit():
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    llms = (LANDING / "llms.txt").read_text(encoding="utf-8")
    for text in (html, llms):
        lower = text.lower()
        assert "authorized ops only" in lower or "authorized use" in lower
        assert "exploit poc" in lower
        assert "msfvenom" not in lower
        assert "reverse shell" not in lower
        assert "payload =" not in lower
    assert PRODUCT in html
    assert "safedepositbox.org" not in html.lower()
    assert "safedepositbox.org" not in llms.lower()


def test_demo_op_named_in_quick_start_exists():
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    assert "op-20260711-veil-ledger-demo" in html
    op = ROOT / "examples" / "sd_card" / "flipper69" / "operations" / "op-20260711-veil-ledger-demo"
    assert op.is_dir()
