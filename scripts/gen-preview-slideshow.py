#!/usr/bin/env python3
"""Build the README preview slideshow:

  assets/screenshot/preview-slideshow.webp

A README can't run JS/CSS, so the "slideshow" is an animated WebP (loops
forever, ~4 s per slide) assembled from the desktop screenshots below. Each
slide is letterboxed into the same 16:9 frame (so nothing is cropped) and gets
a footer with the slide's name and progress dots, in the Roudix palette
(assets/palette/Roudix.json).

To add / reorder / replace a slide: edit SLIDES, then run
  python3 scripts/gen-preview-slideshow.py
Requires Pillow (`pip install pillow`, or `nix shell nixpkgs#python3Packages.pillow`).
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "assets/screenshot"
PALETTE = ROOT / "assets/palette/Roudix.json"
OUT = SHOTS / "preview-slideshow.webp"

# (screenshot file in assets/screenshot, label shown in the footer)
SLIDES = [
    ("preview.png", "Umbriel · Noctalia"),
    ("gnome.png", "GNOME"),
    ("kde-plasma.png", "KDE Plasma"),
]

W, H = 1600, 900          # image area (16:9)
FOOTER = 64
SLIDE_MS = 4000
QUALITY = 88

FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf",
    "DejaVuSansMono-Bold.ttf",
]


def font(size):
    for f in FONTS:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def frame(index, shot, label, pal):
    bg, fg = pal["mSurface"], pal["mOnSurface"]
    accent, dim = pal["mPrimary"], pal["mOutline"]

    canvas = Image.new("RGB", (W, H + FOOTER), bg)

    img = Image.open(SHOTS / shot).convert("RGB")
    scale = min(W / img.width, H / img.height)
    size = (round(img.width * scale), round(img.height * scale))
    img = img.resize(size, Image.LANCZOS)
    canvas.paste(img, ((W - size[0]) // 2, (H - size[1]) // 2))

    d = ImageDraw.Draw(canvas)
    d.line([(0, H), (W, H)], fill=dim, width=1)

    f = font(26)
    d.text((32, H + FOOTER / 2), label, font=f, fill=fg, anchor="lm")

    # progress dots, right-aligned
    r, gap = 7, 16
    x = W - 32 - (len(SLIDES) * 2 * r + (len(SLIDES) - 1) * gap)
    for i in range(len(SLIDES)):
        cy = H + FOOTER // 2
        d.ellipse([x, cy - r, x + 2 * r, cy + r], fill=accent if i == index else dim)
        x += 2 * r + gap
    return canvas


def main():
    pal = json.loads(PALETTE.read_text())["dark"]
    frames = [frame(i, s, l, pal) for i, (s, l) in enumerate(SLIDES)]
    frames[0].save(
        OUT, save_all=True, append_images=frames[1:],
        duration=SLIDE_MS, loop=0, quality=QUALITY, method=6,
    )
    print(f"wrote {OUT.relative_to(ROOT)}  "
          f"({len(frames)} slides, {OUT.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
