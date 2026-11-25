#!/usr/bin/env python3
"""Embarque les icônes d'interface (actions / status / panel) de Papirus dans Roudix.

Pourquoi : sans elles, un nom comme go-previous / edit-find / audio-volume-high n'existe pas
dans Roudix ; si le thème parent ne le fournit pas non plus, KDE/Qt tronque le nom
(go-previous -> go, audio-volume-high -> audio) et tombe sur une *icône d'app* en tuile
(gopher Go, haut-parleur Tela...). Papirus-Dark -> Roudix, Papirus-Light -> Roudix-Light.

Les dossiers sont Fixed 16/22/24 comme dans Papirus, déclarés AVANT scalable/* : aux petites
tailles (barres d'outils, tray, menus) on a l'icône monochrome ; à 32+ px les tuiles Roudix.
Usage : add_papirus_ui.py <papirus-icon-theme (dépôt)> [<Roudix racine>]   (idempotent)
"""
import json, os, re, shutil, sys

PAP = sys.argv[1]
ROOT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..")
SETS = [("16x16", "actions"), ("22x22", "actions"), ("24x24", "actions"),
        ("16x16", "panel"), ("22x22", "panel"), ("24x24", "panel"),
        ("16x16", "status"), ("22x22", "status"), ("24x24", "status")]
# Noms d'icônes d'APP que le tray / les barres d'outils demandent aussi en petit : Roudix y a une
# tuile, on ajoute la version monochrome Papirus pour 16/22/24 px (nom -> (contexte source, fichier)).
SMALL_ALIASES = {"preferences-system": ("actions", "configure"),
                 "video-display": ("panel", "preferences-desktop-display-randr"),
                 "preferences-desktop-display": ("panel", "preferences-desktop-display-randr")}
CONTEXT = {"actions": "Actions", "panel": "Status", "status": "Status"}

# Recoloration : le gris/blanc du texte Papirus (#dfdfdf sombre, #444444 clair) et le bleu "highlight"
# deviennent le primaire Roudix (assets/palette/Roudix.json : #FF8C42 sombre, #E0661A clair).
# Le <style id="current-color-scheme"> est renommé, sinon KDE le remplace par la couleur du texte
# du système et l'orange est perdu. Rouge / vert / orange "sémantiques" (erreur, succès) restent.
PAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "assets", "palette", "Roudix.json")
try: _p = json.load(open(PAL))
except OSError: _p = {"dark": {"mPrimary": "#FF8C42"}, "light": {"mPrimary": "#E0661A"}}
PRIMARY = {"Roudix": _p["dark"]["mPrimary"], "Roudix-Light": _p["light"]["mPrimary"]}
TEXT = {"Roudix": "#dfdfdf", "Roudix-Light": "#444444"}

def recolor(theme_dir, variant, dirs):
    n = 0
    for d in dirs:
        base = os.path.join(theme_dir, d)
        for f in os.listdir(base):
            fp = os.path.join(base, f)
            if os.path.islink(fp) or not f.endswith(".svg"): continue
            t = open(fp, encoding="utf-8").read(); o = t
            t = re.sub(re.escape(TEXT[variant]), PRIMARY[variant], t, flags=re.I)
            t = re.sub(r"#(?:4285f4|3b5df4)\b", PRIMARY[variant], t, flags=re.I)
            t = t.replace('id="current-color-scheme"', 'id="roudix-color-scheme"')
            if t != o: open(fp, "w", encoding="utf-8").write(t); n += 1
    return n

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
            s = os.path.realpath(s)           # lien sortant : on copie la cible
        if os.path.isfile(s): shutil.copyfile(s, d)

def main():
    for variant, pap in (("Roudix", "Papirus-Dark"), ("Roudix-Light", "Papirus-Light")):
        theme = os.path.join(ROOT, variant)
        dirs = []
        for size, ctx in SETS:
            src = os.path.realpath(os.path.join(PAP, pap, size, ctx))
            if not os.path.isdir(src) or not os.listdir(src): continue
            dst = os.path.join(theme, size, ctx)
            if os.path.isdir(dst): shutil.rmtree(dst)
            copy_dir(src, dst); dirs.append(f"{size}/{ctx}")
        for size in ("16x16", "22x22", "24x24"):
            for name, (ctx, src) in SMALL_ALIASES.items():
                sp = os.path.join(theme, size, ctx, src + ".svg")
                dp = os.path.join(theme, size, "panel", name + ".svg")
                if os.path.exists(sp) and f"{size}/panel" in dirs:
                    if os.path.lexists(dp): os.remove(dp)
                    shutil.copyfile(os.path.realpath(sp), dp)
        # chaînes de symlinks internes : on aplatit celles qui pendent
        for d in dirs:
            p = os.path.join(theme, d)
            for f in os.listdir(p):
                fp = os.path.join(p, f)
                if os.path.islink(fp) and not os.path.exists(fp): os.remove(fp)
        print("  recolorés :", recolor(theme, variant, dirs), "SVG ->", PRIMARY[variant])
        idx = os.path.join(theme, "index.theme")
        s = open(idx, encoding="utf-8").read()
        s = re.sub(r"\n\[(?:16x16|22x22|24x24)/[a-z]+\]\n(?:[^\[\n].*\n)*", "\n", s)       # idempotent
        m = re.search(r"^Directories=(.*)$", s, re.M)
        old = [x for x in m.group(1).split(",") if not re.match(r"\d+x\d+/", x)]
        s = s[:m.start()] + "Directories=" + ",".join(dirs + old) + s[m.end():]
        s = s.rstrip("\n") + "\n"
        for d in dirs:
            size, ctx = d.split("/")
            s += f"\n[{d}]\nContext={CONTEXT[ctx]}\nSize={size.split('x')[0]}\nType=Fixed\n"
        open(idx, "w", encoding="utf-8").write(s)
        print(variant, "<-", pap, ":", len(dirs), "dossiers,", sum(len(os.listdir(os.path.join(theme, d))) for d in dirs), "entrées")

main()
