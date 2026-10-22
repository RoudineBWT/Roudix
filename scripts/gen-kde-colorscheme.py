#!/usr/bin/env python3
"""Generate the Plasma colour schemes (RoudixDark.colors / RoudixLight.colors)
from assets/palette/Roudix.json — the single source of truth for Roudix colours.

Usage: python3 scripts/gen-kde-colorscheme.py
Output: assets/kde/color-schemes/Roudix{Dark,Light}.colors
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PALETTE = ROOT / "assets/palette/Roudix.json"
OUT = ROOT / "assets/kde/color-schemes"


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def fmt(c):
    """Accepts '#RRGGBB' or an (r, g, b) tuple."""
    if isinstance(c, str):
        c = rgb(c)
    return "%d,%d,%d" % c


def mix(a, b, t):
    """a * (1 - t) + b * t"""
    return tuple(round(x * (1 - t) + y * t) for x, y in zip(rgb(a), rgb(b)))


def build(name, p, dark):
    t = p["terminal"]
    surf, surf_v = p["mSurface"], p["mSurfaceVariant"]
    on, on_v = p["mOnSurface"], p["mOnSurfaceVariant"]
    prim, on_prim = p["mPrimary"], p["mOnPrimary"]
    hover = p["mHover"]
    err = p["mError"]
    green, blue = t["normal"]["green"], t["normal"]["blue"]
    yellow = t["normal"]["yellow"]

    # Window (content) areas are one step below chrome so cards/inputs read as layers.
    view_bg = mix(surf, "#000000", 0.18) if dark else mix(surf, "#FFFFFF", 0.55)
    view_alt = surf if dark else surf_v
    win_bg = surf
    win_alt = surf_v
    btn_bg = surf_v
    btn_alt = mix(surf_v, on, 0.06)
    tip_bg = surf_v
    # Inactive / disabled foreground, used for the "inactive text" role.
    inactive = on_v
    # Link colours: primary for links, tertiary-ish for visited.
    link = prim if dark else p["mPrimary"]
    visited = p["mTertiary"]
    sel_bg = prim
    sel_fg = on_prim
    sel_alt = mix(prim, surf, 0.12)

    def role(bg, alt, fg, fg_inactive=None, deco_focus=None, deco_hover=None):
        return {
            "BackgroundNormal": fmt(bg),
            "BackgroundAlternate": fmt(alt),
            "ForegroundNormal": fmt(fg),
            "ForegroundInactive": fmt(fg_inactive or inactive),
            "ForegroundActive": fmt(prim),
            "ForegroundLink": fmt(link),
            "ForegroundVisited": fmt(visited),
            "ForegroundNegative": fmt(err),
            "ForegroundNeutral": fmt(yellow),
            "ForegroundPositive": fmt(green),
            "DecorationFocus": fmt(deco_focus or prim),
            "DecorationHover": fmt(deco_hover or hover),
        }

    sections = {}
    sections["Colors:View"] = role(view_bg, view_alt, on)
    sections["Colors:Window"] = role(win_bg, win_alt, on)
    sections["Colors:Button"] = role(btn_bg, btn_alt, on)
    sections["Colors:Tooltip"] = role(tip_bg, surf, on)
    sections["Colors:Complementary"] = role(
        mix(surf, "#000000", 0.25) if dark else mix(surf, "#000000", 0.82),
        surf_v if dark else mix(surf, "#000000", 0.75),
        on if dark else "#EADBCB",
    )
    sections["Colors:Header"] = role(surf_v, surf, on)
    sel = role(sel_bg, sel_alt, sel_fg, fg_inactive=on_prim)
    # Selection: text is always on-primary, accents invert to stay readable on the primary fill.
    sel["ForegroundActive"] = fmt(on_prim)
    sel["ForegroundLink"] = fmt(on_prim)
    sel["ForegroundVisited"] = fmt(on_prim)
    sel["ForegroundNegative"] = fmt(on_prim)
    sel["ForegroundNeutral"] = fmt(on_prim)
    sel["ForegroundPositive"] = fmt(on_prim)
    sel["DecorationFocus"] = fmt(on_prim)
    sections["Colors:Selection"] = sel

    out = ["[ColorEffects:Disabled]",
           "Color=%s" % fmt(mix(surf, on, 0.25)),
           "ColorAmount=0",
           "ColorEffect=0",
           "ContrastAmount=0.65",
           "ContrastEffect=1",
           "IntensityAmount=0.1",
           "IntensityEffect=2",
           "",
           "[ColorEffects:Inactive]",
           "ChangeSelectionColor=true",
           "Color=%s" % fmt(on_v),
           "ColorAmount=0.025",
           "ColorEffect=2",
           "ContrastAmount=0.1",
           "ContrastEffect=2",
           "Enable=false",
           "IntensityAmount=0",
           "IntensityEffect=0",
           ""]
    for sec, kv in sections.items():
        out.append("[%s]" % sec)
        out += ["%s=%s" % (k, v) for k, v in kv.items()]
        out.append("")

    wm_active_bg = mix(surf, "#000000", 0.2) if dark else mix(surf_v, "#000000", 0.04)
    wm_inactive_bg = surf
    out += [
        "[General]",
        "ColorScheme=%s" % name,
        "Name=%s" % ("Roudix Dark" if dark else "Roudix Light"),
        "shadeSortColumn=true",
        "",
        "[KDE]",
        "contrast=4",
        "",
        "[WM]",
        "activeBackground=%s" % fmt(wm_active_bg),
        "activeBlend=%s" % fmt(on),
        "activeForeground=%s" % fmt(on),
        "inactiveBackground=%s" % fmt(wm_inactive_bg),
        "inactiveBlend=%s" % fmt(on_v),
        "inactiveForeground=%s" % fmt(on_v),
        "",
    ]
    return "\n".join(out)


def main():
    raw = json.loads(PALETTE.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for key, name in (("dark", "RoudixDark"), ("light", "RoudixLight")):
        (OUT / f"{name}.colors").write_text(build(name, raw[key], key == "dark"))
        print("wrote", OUT / f"{name}.colors")


if __name__ == "__main__":
    main()
