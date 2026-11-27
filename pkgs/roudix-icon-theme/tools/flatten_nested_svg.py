#!/usr/bin/env python3
"""Remplace le <svg x y width height viewBox> imbriqué dans la tuile par
<g clip-path><g transform> : Qt (Plasma, KDE, QtSvg = SVG Tiny 1.2) ignore les <svg>
imbriqués, ce qui donnait des tuiles vides. Idempotent. Usage : flatten_nested_svg.py [dossier ...]"""
import os, re, sys

NESTED = re.compile(
    r'(?P<ind>[ \t]*)<svg x="(?P<x>[-\d.]+)" y="(?P<y>[-\d.]+)" width="(?P<w>[-\d.]+)" '
    r'height="(?P<h>[-\d.]+)" viewBox="(?P<vb>[^"]+)">(?P<inner>.*)</svg>\s*(?=</svg>\s*$)',
    re.S)

def n(v):
    s = f"{v:.5f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s

def flatten_nested(x, y, w, h, vb, inner, ind="  "):
    vx, vy, vw, vh = (float(t) for t in vb.replace(",", " ").split())
    s = min(w / vw, h / vh)                      # preserveAspectRatio="xMidYMid meet"
    tx = x + (w - vw * s) / 2 - vx * s
    ty = y + (h - vh * s) / 2 - vy * s
    # <clipPath> DOIT être dans <defs> : sinon Qt (SVG Tiny) le dessine comme une forme
    # normale -> gros carré noir derrière le glyphe.
    return (f'{ind}<defs><clipPath id="rvp"><rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}"/></clipPath></defs>\n'
            f'{ind}<g clip-path="url(#rvp)"><g transform="translate({n(tx)} {n(ty)}) scale({n(s)})">{inner}</g></g>\n')

BARE_CLIP = re.compile(r'<clipPath\b.*?</clipPath>', re.S)

def wrap_clippaths(s):
    """Enveloppe dans <defs> tout <clipPath> qui n'y est pas déjà (idempotent)."""
    out, last = [], 0
    for m in BARE_CLIP.finditer(s):
        pre = s[:m.start()]
        if pre.rfind("<defs") > pre.rfind("</defs>"):      # déjà dans un <defs>
            continue
        out.append(s[last:m.start()]); out.append("<defs>" + m.group(0) + "</defs>")
        last = m.end()
    out.append(s[last:])
    return "".join(out)

def fix_text(s):
    s = wrap_clippaths(s)
    m = NESTED.search(s)
    if not m:
        return s
    new = flatten_nested(float(m["x"]), float(m["y"]), float(m["w"]), float(m["h"]),
                         m["vb"], m["inner"], m["ind"])
    return s[:m.start()] + new + s[m.end():]

def main(dirs):
    done = skipped = 0
    for d in dirs:
        for root, _, files in os.walk(d):
            for f in files:
                if not f.endswith(".svg"): continue
                p = os.path.join(root, f)
                if os.path.islink(p): continue
                s = open(p, encoding="utf-8").read()
                t = fix_text(s)
                if t != s:
                    open(p, "w", encoding="utf-8").write(t); done += 1
                else:
                    skipped += 1
    print(f"{done} SVG convertis, {skipped} inchangés")

if __name__ == "__main__":
    main(sys.argv[1:] or ["Roudix", "Roudix-Light"])
