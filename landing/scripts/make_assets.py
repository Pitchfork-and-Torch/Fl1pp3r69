#!/usr/bin/env python3
"""Build production landing assets from Imagine sources (ASCII only)."""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DEST = Path(os.environ["USERPROFILE"]) / "Flipper69" / "landing" / "assets"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\consolab.ttf" if bold else r"C:\Windows\Fonts\consola.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)

    hero = Image.open(DEST / "hero-argus-veil.jpg").convert("RGB")
    emblem = Image.open(DEST / "emblem-dolphin.jpg").convert("RGB")
    share_bg = Image.open(DEST / "share-bg.jpg").convert("RGB")

    hero_w = 1600
    hero_r = hero.resize(
        (hero_w, int(hero.height * hero_w / hero.width)),
        Image.Resampling.LANCZOS,
    )
    hero_r.save(DEST / "hero-argus-veil.jpg", "JPEG", quality=90, optimize=True)
    hero_r.save(DEST / "hero-argus-veil.png", "PNG", optimize=True)

    em = emblem.resize((512, 512), Image.Resampling.LANCZOS)
    em.save(DEST / "emblem-dolphin.png", "PNG", optimize=True)
    em.save(DEST / "emblem-dolphin.jpg", "JPEG", quality=92, optimize=True)
    for size, name in [
        (32, "favicon-32.png"),
        (180, "apple-touch-icon.png"),
        (192, "icon-192.png"),
    ]:
        em.resize((size, size), Image.Resampling.LANCZOS).save(
            DEST / name, "PNG", optimize=True
        )

    W, H = 1200, 630
    bg = share_bg.resize((W, H), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for x in range(W):
        t = max(0.0, 1.0 - (x / (W * 0.72)))
        a = int(185 * t)
        od.line([(x, 0), (x, H)], fill=(10, 10, 12, a))
    od.rectangle([0, H - 8, W, H], fill=(196, 30, 30, 200))
    card = Image.alpha_composite(bg.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(card)

    mono = font(22, bold=True)
    title = font(72, bold=True)
    sub = font(28, False)
    small = font(20, False)

    draw.text((56, 48), "UNCLASSIFIED // FRI", font=mono, fill=(139, 139, 139, 255))
    draw.text((56, 88), "v4.0.0  ·  ARGUS VEIL", font=mono, fill=(255, 176, 0, 255))
    draw.text((56, 200), "FL1PP3R69", font=title, fill=(232, 230, 227, 255))
    draw.text((56, 290), "The dolphin grew teeth.", font=sub, fill=(196, 30, 30, 255))
    draw.text(
        (56, 340),
        "Manifest-driven Flipper Zero field ops.",
        font=sub,
        fill=(200, 200, 200, 255),
    )
    draw.text(
        (56, 400),
        "CASEFILE discipline  ·  10 FAPs  ·  CLAIM harness",
        font=small,
        fill=(57, 255, 20, 230),
    )
    draw.text(
        (56, 540),
        "Pitchfork-and-Torch  ·  owned hardware only",
        font=small,
        fill=(139, 139, 139, 255),
    )

    card_rgb = card.convert("RGB")
    card_rgb.save(DEST / "share-card.jpg", "JPEG", quality=92, optimize=True)
    card_rgb.save(DEST / "og.jpg", "JPEG", quality=92, optimize=True)
    card.save(DEST / "share-card.png", "PNG", optimize=True)
    card.save(DEST / "og.png", "PNG", optimize=True)

    print("hero", (DEST / "hero-argus-veil.jpg").stat().st_size)
    print("share", (DEST / "share-card.jpg").stat().st_size)
    print("emblem", (DEST / "emblem-dolphin.png").stat().st_size)
    print("DONE")


if __name__ == "__main__":
    main()
