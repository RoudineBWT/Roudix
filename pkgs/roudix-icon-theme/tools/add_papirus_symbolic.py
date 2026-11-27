#!/usr/bin/env python3
"""Embarque les icônes *symboliques* de Papirus (16/22/24 px) dans Roudix, recolorées en orange.

Pourquoi : le tray, les menus et les popups Plasma (Notifications, Météo, Disques & périphériques,
Configuration d'affichage, KDE Connect, Gestion d'énergie, presse-papiers, utilisateur, volume,
luminosité...) demandent des noms `*-symbolic`. Roudix ne les fournissant pas, KDE les prenait
chez le thème parent (Papirus) : glyphes crème (couleur du texte du système) ou bleus, pas orange.
Ici on copie Papirus-Dark -> Roudix et Papirus-Light -> Roudix-Light, puis on recolore avec le
primaire Roudix (#FF8C42 sombre, #E0661A clair), comme add_papirus_ui.py.

Dossiers créés : {16x16,22x22,24x24}/symbolic/{actions,apps,categories,devices,emblems,mimetypes,
places,status} (Fixed), déclarés AVANT scalable/* dans index.theme. Idempotent.
À lancer APRÈS add_papirus_ui.py (qui réécrit la ligne Directories et supprimerait ces dossiers).
Usage : add_papirus_symbolic.py <papirus-icon-theme (dépôt)> [<Roudix racine>]
"""
import json, os, re, shutil, sys

PAP = sys.argv[1]
ROOT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SIZES = ("16x16", "22x22", "24x24")
CTXS = {"actions": "Actions", "apps": "Applications", "categories": "Categories", "devices": "Devices",
        "emblems": "Emblems", "mimetypes": "MimeTypes", "places": "Places", "status": "Status"}

PAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "assets", "palette", "Roudix.json")
try: _p = json.load(open(PAL))
except OSError: _p = {"dark": {"mPrimary": "#FF8C42"}, "light": {"mPrimary": "#E0661A"}}
PRIMARY = {"Roudix": _p["dark"]["mPrimary"], "Roudix-Light": _p["light"]["mPrimary"]}
# Papirus-Dark utilise #dfdfdf OU #444444 selon les fichiers pour le texte : on remappe les deux
# (+ le bleu "highlight"). Rouge/vert/orange sémantiques conservés.
TEXT_COLORS = ("#dfdfdf", "#444444")


def copy_dir(src, dst):
    """cp -a du contenu : garde les symlinks relatifs internes, résout les autres."""
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(src):
        s, d = os.path.join(src, f), os.path.join(dst, f)
        if os.path.lexists(d): os.remove(d)
        if os.path.islink(s):
            t = os.readlink(s)
            if "/" not in t and os.path.lexists(os.path.join(src, t)):
                os.symlink(t, d); continue
            s = os.path.realpath(s)
        if os.path.isfile(s): shutil.copyfile(s, d)


def recolor(path, primary):
    n = 0
    for f in os.listdir(path):
        fp = os.path.join(path, f)
        if os.path.islink(fp) or not f.endswith(".svg"): continue
        t = open(fp, encoding="utf-8").read(); o = t
        for c in TEXT_COLORS:
            t = re.sub(re.escape(c), primary, t, flags=re.I)
        t = re.sub(r"#(?:4285f4|3b5df4)\b", primary, t, flags=re.I)
        t = t.replace('id="current-color-scheme"', 'id="roudix-color-scheme"')   # sinon KDE remet la couleur du texte
        if t != o: open(fp, "w", encoding="utf-8").write(t); n += 1
    return n


def main():
    for variant, pap in (("Roudix", "Papirus-Dark"), ("Roudix-Light", "Papirus-Light")):
        theme = os.path.join(ROOT, variant)
        # nettoyage (idempotence)
        for size in SIZES:
            shutil.rmtree(os.path.join(theme, size, "symbolic"), ignore_errors=True)
        dirs, total = [], 0
        for size in SIZES:
            for ctx in CTXS:
                src = os.path.realpath(os.path.join(PAP, pap, size, "symbolic", ctx))
                if not os.path.isdir(src) or not os.listdir(src): continue
                dst = os.path.join(theme, size, "symbolic", ctx)
                copy_dir(src, dst)
                for f in os.listdir(dst):                      # liens pendants -> supprimés
                    fp = os.path.join(dst, f)
                    if os.path.islink(fp) and not os.path.exists(fp): os.remove(fp)
                total += recolor(dst, PRIMARY[variant]); dirs.append(f"{size}/symbolic/{ctx}")
        idx = os.path.join(theme, "index.theme")
        s = open(idx, encoding="utf-8").read()
        s = re.sub(r"\n\[\d+x\d+/symbolic/[a-z]+\]\n(?:[^\[\n].*\n)*", "\n", s)
        m = re.search(r"^Directories=(.*)$", s, re.M)
        old = [x for x in m.group(1).split(",") if "/symbolic/" not in x]
        i = next((k for k, x in enumerate(old) if x.startswith("scalable/")), len(old))
        s = s[:m.start()] + "Directories=" + ",".join(old[:i] + dirs + old[i:]) + s[m.end():]
        s = s.rstrip("\n") + "\n"
        for d in dirs:
            size, _, ctx = d.split("/")
            s += f"\n[{d}]\nContext={CTXS[ctx]}\nSize={size.split('x')[0]}\nType=Fixed\n"
        open(idx, "w", encoding="utf-8").write(s)
        n = sum(len(os.listdir(os.path.join(theme, d))) for d in dirs)
        print(f"{variant} <- {pap} : {len(dirs)} dossiers, {n} entrées, {total} SVG recolorés -> {PRIMARY[variant]}")


main()
