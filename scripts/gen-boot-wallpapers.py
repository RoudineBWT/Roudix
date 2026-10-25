#!/usr/bin/env python3
"""Roudix bootloader wallpapers — "Roux Sunburst", one per screen ratio.

Generates modules/system/boot/bootloader/wallpaper-<format>.png, the files
roudix.boot.wallpaperAspect (modules/system/boot/boot.nix) picks from:

  16x9  2560x1440   16x10  2560x1600   21x9  3440x1440   4x3  2048x1536

  scripts/gen-boot-wallpapers.py                      all 4, into the repo
  scripts/gen-boot-wallpapers.py 2560 1440 out.png    one custom size

Limine stretches the wallpaper to the screen, so each file matches a ratio.
Everything scales with the image height (U = H/1440) and the corner elements
(HUD brackets, logo lockup) stay anchored to the corners.

Needs python3 with Pillow + numpy, and the Poppins Bold + DejaVu Sans Mono
fonts (override with ROUDIX_FONT_BOLD / ROUDIX_FONT_MONO):
  nix shell nixpkgs#python3Packages.pillow nixpkgs#python3Packages.numpy \\
            nixpkgs#poppins nixpkgs#dejavu_fonts -c scripts/gen-boot-wallpapers.py

Palette (assets/logo + the Limine terminal theme):
  ink #150b05  umber #5c2a12  rust #c9622d  orange #ff8c42
  gold #f2b05e amber #ffc878  tan #eab676   cream #f5ebdd
"""
import math
import os
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

INK = (0x15, 0x0B, 0x05)
UMBER = (0x5C, 0x2A, 0x12)
RUST = (0xC9, 0x62, 0x2D)
ORANGE = (0xFF, 0x8C, 0x42)
GOLD = (0xF2, 0xB0, 0x5E)
AMBER = (0xFF, 0xC8, 0x78)
TAN = (0xEA, 0xB6, 0x76)
CREAM = (0xF5, 0xEB, 0xDD)



def _find_font(env, pattern, fallbacks):
    """$env, else fontconfig's best match for `pattern`, else the first existing fallback."""
    if os.environ.get(env):
        return os.environ[env]
    try:
        path = subprocess.check_output(["fc-match", "-f", "%{file}", pattern], text=True).strip()
        if path and Path(path).is_file():
            return path
    except (OSError, subprocess.CalledProcessError):
        pass
    for fb in fallbacks:
        if Path(fb).is_file():
            return fb
    sys.exit(f"font not found for '{pattern}': install it or set {env}=/path/to/font.ttf")


FONT_BOLD = _find_font("ROUDIX_FONT_BOLD", "Poppins:bold",
                       ["/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"])
FONT_MONO = _find_font("ROUDIX_FONT_MONO", "DejaVu Sans Mono",
                       ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"])

VARIANTS = {
    "16x9": (2560, 1440),   # 1280x720, 1920x1080, 2560x1440, 3840x2160 ...
    "16x10": (2560, 1600),  # 1920x1200, 2560x1600, 2880x1800 ...
    "21x9": (3440, 1440),   # 2560x1080, 3440x1440 ...
    "4x3": (2048, 1536),    # 1024x768, 1280x1024 (5:4, ~6% stretch), 1600x1200 ...
}


def render(W, H, out_path):
    random.seed(7)
    np.random.seed(7)
    U = H / 1440.0
    CX, CY = W // 2, H // 2
    px = lambda v: max(1, int(round(v * U)))

    def rgba_layer():
        return Image.new("RGBA", (W, H), (0, 0, 0, 0))

    def over(base, layer):
        return Image.alpha_composite(base, layer)

    def glow(layer, radius, strength=1.0):
        g = layer.filter(ImageFilter.GaussianBlur(radius))
        if strength != 1.0:
            g.putalpha(g.getchannel("A").point(lambda v: min(255, int(v * strength))))
        return g

    # ── 1. background gradient ────────────────────────────────────────
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = xx - CX, yy - CY
    dist = np.sqrt(dx * dx + dy * dy)
    rmax = math.hypot(CX, CY)
    t = np.clip(dist / rmax, 0, 1)

    core = np.array([0x3A, 0x1A, 0x0A], np.float32)
    mid = np.array([0x22, 0x10, 0x07], np.float32)
    edge = np.array([0x0B, 0x05, 0x02], np.float32)
    # use height-based radius so the glow keeps the same look on ultrawide
    th_ = np.clip(dist / (math.hypot(1280, 720) * U), 0, 1)
    k1 = np.clip(1 - th_ / 0.45, 0, 1)[..., None] ** 1.6
    k2 = np.clip(1 - th_ / 0.95, 0, 1)[..., None] ** 1.3
    bg = edge + (mid - edge) * k2 + (core - mid) * k1
    img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

    # ── 2. sunburst rays ──────────────────────────────────────────────
    ang = np.arctan2(dy, dx)

    def ray_mask(center_deg, half_width_deg):
        d = np.angle(np.exp(1j * (ang - math.radians(center_deg))))
        return np.exp(-(d / math.radians(half_width_deg)) ** 2)

    arms = sum(ray_mask(-90 + 60 * i, 3.2) for i in range(6))
    chev = sum(ray_mask(-60 + 60 * i, 1.8) for i in range(6))
    fine = sum(ray_mask(-90 + 15 * i + 7.5, 0.55) for i in range(24))

    radial_fade = np.clip(1 - dist / (math.hypot(1280, 720) * U * 0.98), 0, 1) ** 1.7
    radial_hole = np.clip((dist - 150 * U) / (260 * U), 0, 1)
    rays = np.clip((arms * 0.30 + chev * 0.17 + fine * 0.07) * radial_fade * radial_hole, 0, 1)

    ray_rgb = np.zeros((H, W, 3), np.uint8)
    ray_rgb[..., 0], ray_rgb[..., 1], ray_rgb[..., 2] = ORANGE
    img = over(img, Image.fromarray(np.dstack([ray_rgb, (rays * 120).astype(np.uint8)]), "RGBA"))

    # ── 3. rings + tick dial ──────────────────────────────────────────
    S = 2
    ring = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(ring)

    def circle(r, color, a, width=2):
        r *= U
        d.ellipse([(CX - r) * S, (CY - r) * S, (CX + r) * S, (CY + r) * S],
                  outline=color + (a,), width=px(width) * S)

    for r, a in [(300, 40), (420, 30), (560, 24), (730, 18), (940, 12)]:
        circle(r, TAN, a, 2)

    def ticks(r_in, r_out, n, color, a, width=2, every=None, r_out_major=None):
        for i in range(n):
            th = 2 * math.pi * i / n - math.pi / 2
            major = every and i % every == 0
            ro = (r_out_major if (major and r_out_major) else r_out) * U
            ri = r_in * U
            d.line([((CX + ri * math.cos(th)) * S, (CY + ri * math.sin(th)) * S),
                    ((CX + ro * math.cos(th)) * S, (CY + ro * math.sin(th)) * S)],
                   fill=color + ((a + 40) if major else a,),
                   width=px(width + 1 if major else width) * S)

    ticks(486, 500, 180, GOLD, 70, 2, every=6, r_out_major=520)
    ticks(640, 648, 360, TAN, 28, 1)
    circle(486, GOLD, 60, 2)

    for i in range(6):
        th = math.radians(-90 + 60 * i)
        x, y = CX + 730 * U * math.cos(th), CY + 730 * U * math.sin(th)
        s = 9 * U
        d.polygon([(px_ * S, py_ * S) for px_, py_ in
                   [(x, y - s), (x + s * 0.7, y), (x, y + s), (x - s * 0.7, y)]],
                  fill=GOLD + (170,))

    img = over(img, ring.resize((W, H), Image.LANCZOS))

    # ── 4. embers ─────────────────────────────────────────────────────
    ember = rgba_layer()
    ed = ImageDraw.Draw(ember)
    n_embers = int(420 * (W * H) / (2560 * 1440))
    for _ in range(n_embers):
        r = (abs(random.gauss(0, 520)) + 40) * U
        th = random.uniform(0, 2 * math.pi)
        x = CX + r * math.cos(th) * 1.35
        y = CY + r * math.sin(th) * 0.9 - random.uniform(0, 160) * U
        if not (0 <= x < W and 0 <= y < H):
            continue
        size = random.choice([1, 1, 1, 2, 2, 3]) * max(1.0, U)
        col = random.choice([ORANGE, AMBER, GOLD, RUST])
        a = int(random.uniform(60, 220) * max(0.25, 1 - r / (1100 * U)))
        ed.ellipse([x - size, y - size, x + size, y + size], fill=col + (a,))
    img = over(img, glow(ember, 5 * U, 1.4))
    img = over(img, ember)

    # ── 5. central halo ───────────────────────────────────────────────
    halo = rgba_layer()
    hr = 230 * U
    ImageDraw.Draw(halo).ellipse([CX - hr, CY - hr, CX + hr, CY + hr], fill=ORANGE + (95,))
    img = over(img, glow(halo, 110 * U, 1.0))

    # ── 6. logo ───────────────────────────────────────────────────────
    def logo_layer(size, alpha=255, ss=3):
        size = int(size)
        pxs = size * ss
        sc = pxs / 380.0
        c = pxs / 2
        im = Image.new("RGBA", (pxs, pxs), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)

        def tf(pts, rot_deg):
            r = math.radians(rot_deg)
            cs, sn = math.cos(r), math.sin(r)
            return [(c + (x * cs - y * sn) * sc, c + (x * sn + y * cs) * sc) for x, y in pts]

        arm_main = [(0, -179.5), (19, -157), (19, -45), (-19, -45), (-19, -157)]
        arm_l = [(0, -179.5), (-19, -157), (0, -134.5)]
        arm_r = [(0, -179.5), (19, -157), (0, -134.5)]
        chev_main = [(14, -100), (37.6, -140.9), (34.2, -161), (15.1, -153.9), (0, -127.8),
                     (-15.1, -153.9), (-34.2, -161), (-37.6, -140.9), (-14, -100)]
        chev_r = [(34.2, -161), (37.6, -140.9), (18.5, -133.8), (15.1, -153.9)]
        chev_l = [(-34.2, -161), (-37.6, -140.9), (-18.5, -133.8), (-15.1, -153.9)]
        for rot in range(0, 360, 60):
            dr.polygon(tf(arm_main, rot), fill=ORANGE + (alpha,))
            dr.polygon(tf(arm_l, rot), fill=AMBER + (alpha,))
            dr.polygon(tf(arm_r, rot), fill=AMBER + (alpha,))
        for rot in range(30, 360, 60):
            dr.polygon(tf(chev_main, rot), fill=GOLD + (alpha,))
            dr.polygon(tf(chev_r, rot), fill=AMBER + (alpha,))
            dr.polygon(tf(chev_l, rot), fill=AMBER + (alpha,))
        for r, col in [(70, CREAM), (51.5, UMBER), (46, GOLD), (27.5, UMBER), (20.5, ORANGE)]:
            dr.ellipse([c - r * sc, c - r * sc, c + r * sc, c + r * sc], fill=col + (alpha,))
        return im.resize((size, size), Image.LANCZOS)

    # soft watermark behind the boot menu
    BIG = int(1100 * U)
    big = logo_layer(BIG)
    big.putalpha(big.getchannel("A").point(lambda v: int(v * 0.12)))
    img.alpha_composite(big, (CX - BIG // 2, CY - BIG // 2))

    # crisp lockup, bottom-left corner (never hidden by the menu)
    MX = MY = int(150 * U)
    LS = int(150 * U)
    lock_y = H - MY - LS
    lg = logo_layer(LS)
    g = rgba_layer()
    g.alpha_composite(lg, (MX, lock_y))
    img = over(img, glow(g, 22 * U, 0.9))
    img.alpha_composite(lg, (MX, lock_y))

    f_big = ImageFont.truetype(FONT_BOLD, int(66 * U))
    f_small = ImageFont.truetype(FONT_MONO, int(26 * U))

    def spaced_text(draw, xy, text, font, fill, spacing):
        x, y = xy
        for ch in text:
            draw.text((x, y), ch, font=font, fill=fill)
            x += draw.textlength(ch, font=font) + spacing
        return x

    txt = rgba_layer()
    td = ImageDraw.Draw(txt)
    tx = MX + LS + int(36 * U)
    end_x = spaced_text(td, (tx, lock_y + 6 * U), "ROUDIX", f_big, CREAM + (255,), 14 * U)
    td.rectangle([tx, lock_y + 92 * U, end_x - 14 * U, lock_y + 92 * U + px(3)], fill=ORANGE + (255,))
    spaced_text(td, (tx, lock_y + 108 * U), "NIXOS", f_small, TAN + (230,), 5 * U)
    img = over(img, glow(txt, 10 * U, 0.5))
    img = over(img, txt)

    # ── 7. HUD corner brackets ────────────────────────────────────────
    br = rgba_layer()
    bd = ImageDraw.Draw(br)
    L, T, M = int(70 * U), px(5), int(70 * U)
    col = RUST + (200,)
    for (x, y, sx, sy) in [(M, M, 1, 1), (W - M, M, -1, 1), (M, H - M, 1, -1), (W - M, H - M, -1, -1)]:
        bd.rectangle([min(x, x + sx * L), min(y, y + sy * T), max(x, x + sx * L), max(y, y + sy * T)], fill=col)
        bd.rectangle([min(x, x + sx * T), min(y, y + sy * L), max(x, x + sx * T), max(y, y + sy * L)], fill=col)
    img = over(img, br)

    # ── 8. vignette + dither ──────────────────────────────────────────
    vig = np.clip((t - 0.55) / 0.5, 0, 1) ** 1.8
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    arr *= (1 - 0.55 * vig)[..., None]
    arr = np.clip(arr + np.random.normal(0, 1.6, (H, W, 1)).astype(np.float32), 0, 255).astype(np.uint8)

    Image.fromarray(arr, "RGB").save(out_path, optimize=True)
    print("saved", out_path, f"{W}x{H}")


if __name__ == "__main__":
    if len(sys.argv) == 4:
        render(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
    else:
        out = Path(__file__).resolve().parent.parent / "modules/system/boot/bootloader"
        out.mkdir(parents=True, exist_ok=True)
        for name, (w, h) in VARIANTS.items():
            render(w, h, str(out / f"wallpaper-{name}.png"))
