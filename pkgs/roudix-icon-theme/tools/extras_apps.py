#!/usr/bin/env python3
"""Icônes d'apps manquantes (apps installées par Roudix dont le nom d'icône n'était pas couvert par le thème,
donc rendues par Papirus/hicolor avec leurs couleurs d'origine). À lancer après build_roudix.py (et extras.py).

Même géométrie que build_roudix.py : tuile Roudix + logo simple-icons recentré (glyph_fill) ou glyphe Lucide.

Usage : python3 tools/extras_apps.py <simple-icons/package> <lucide-static/package> [<dossier du thème>]
        (pip install svgelements)
"""
import os, re, shutil, sys
from svgelements import Path as SvgPath

SI = os.path.join(sys.argv[1], "icons")
LU = os.path.join(sys.argv[2], "icons")
ROOT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REPO = os.path.join(ROOT, "..", "..")
VARIANTS = ["Roudix", "Roudix-Light"]

# fichier canonique -> ("si", slug) | ("lucide", nom) ; puis alias -> canonique
NEW = {
    "cinny":                ("si", "cinny"),
    "chatterino":           ("si", "twitch"),
    "proton-pass":          ("si", "proton"),
    "ytmdesktop":           ("si", "youtubemusic"),
    "songrec":              ("si", "shazam"),
    "fedora":               ("si", "fedora"),
    "bash":                 ("si", "gnubash"),
    "fish":                 ("si", "fishshell"),
    "gnome":                ("si", "gnome"),
    "cinnamon":             ("si", "cinnamon"),
    "hyprland":             ("si", "hyprland"),
    "ollama":               ("si", "ollama"),
    "lact":                 ("lucide", "gauge"),
    "oversteer":            ("lucide", "car"),
    "vm-curator":           ("lucide", "boxes"),
}
ALIASES = {  # alias -> canonique (nouveau ou déjà présent)
    "cinny-desktop": "cinny",
    "chatterino2": "chatterino", "com.chatterino.chatterino": "chatterino",
    "protonpass": "proton-pass", "me.proton.Pass": "proton-pass",
    "youtube-music-desktop-app": "ytmdesktop", "app.ytmdesktop.ytmdesktop": "ytmdesktop",
    "com.github.marinm.songrec": "songrec",
    "io.github.ilya_zlobintsev.LACT": "lact",
    "org.berarma.Oversteer": "oversteer",
    # canoniques déjà dans le thème
    "brave-browser": "brave", "brave-browser-beta": "brave", "brave-browser-nightly": "brave", "brave-browser-dev": "brave",
    "brave-origin": "brave", "brave-origin-beta": "brave", "brave-origin-nightly": "brave", "com.brave.Browser": "brave",
    "ayugram": "telegram", "ayugram-desktop": "telegram", "com.ayugram.desktop": "telegram",
    "zapzap": "whatsapp", "com.rtosta.zapzap": "whatsapp",
    "zed-editor": "zed",
    "davinci-resolve-studio": "davinci-resolve", "DaVinciResolveStudio": "davinci-resolve",
    "zen": "zen-browser", "zen-twilight": "zen-browser", "zen-beta": "zen-browser", "app.zen_browser.zen": "zen-browser",
    "betterbird": "thunderbird", "eu.betterbird.Betterbird": "thunderbird",
    "vencord": "vesktop", "dev.vencord.Vesktop": "vesktop",
    "ptyxis": "org.gnome.Ptyxis",
    "bottles": "com.usebottles.bottles",
    "millennium": "steam",
}
# icônes Roudix déjà dessinées dans le repo : (source, nom dans le thème) ; "{v}" = -light pour la variante claire
ROUDIX_APPS = [
    ("pkgs/roudix-firewall/io.roudix.firewall{v}.svg", "io.roudix.firewall"),
    ("pkgs/roudix-config/io.roudix.config{v}.svg", "io.roudix.config"),
    ("pkgs/roudix-store/io.roudix.store{v}.svg", "io.roudix.store"),
    ("pkgs/roudix-scheduler-switcher/io.roudix.scheduler-{vv}.svg", "io.roudix.scheduler"),
    ("iso/roudix-installer/data/icons/hicolor/scalable/apps/roudix-installer.svg", "roudix-installer"),
]


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def put(path, text):
    if os.path.lexists(path):
        os.remove(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def link(apps, alias, target):
    p = os.path.join(apps, alias + ".svg")
    if os.path.lexists(p):
        return False
    os.symlink(target + ".svg", p)
    return True


def main():
    for v in VARIANTS:
        apps = os.path.join(ROOT, v, "scalable", "apps")
        tpl = read(os.path.join(apps, "nixos.svg"))            # gabarit : defs + tuile + 2 chemins (ombre, logo)
        head = tpl[:tpl.index("  <path transform")]
        sh = re.search(r'fill="(#[0-9a-fA-F]+)" opacity="([0-9.]+)"/>', tpl)
        sh_col, sh_op = sh.group(1), sh.group(2)
        for i, (name, (kind, key)) in enumerate(sorted(NEW.items())):
            u = f"x{i}"
            h = head.replace("b137", u)
            if kind == "si":
                d = re.search(r'\bd="([^"]+)"', read(os.path.join(SI, key + ".svg"))).group(1)
                x0, y0, x1, y1 = SvgPath(d).bbox()
                w, hh = x1 - x0, y1 - y0
                L = 30.0 if w / hh > 1.7 else 26.0
                sc = L / max(w, hh)
                if w / hh > 1.7:
                    sc = min(sc, 14.0 / hh)
                tx, ty = 24 - (x0 + x1) / 2 * sc, 23.4 - (y0 + y1) / 2 * sc
                body = (f'  <path transform="translate({tx:.3f} {ty+1:.3f}) scale({sc:.4f})" d="{d}" fill="{sh_col}" opacity="{sh_op}"/>\n'
                        f'  <path transform="translate({tx:.3f} {ty:.3f}) scale({sc:.4f})" d="{d}" fill="url(#gb{u})"/>\n')
            else:
                inner = re.search(r"<svg[^>]*>(.*)</svg>", read(os.path.join(LU, key + ".svg")), re.S).group(1).strip()
                inner = re.sub(r"\s+", " ", inner)
                attrs = 'fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8"'
                body = (f'  <g transform="translate(11 11) scale(1.0833)" {attrs} stroke="{sh_col}" opacity="{sh_op}">{inner}</g>\n'
                        f'  <g transform="translate(11 10) scale(1.0833)" {attrs} stroke="url(#gl{u})">{inner}</g>\n')
            put(os.path.join(apps, key_name(name) + ".svg"), h + body + "</svg>\n")
        made = 0
        for alias, target in ALIASES.items():
            if os.path.lexists(os.path.join(apps, target + ".svg")) and link(apps, alias, target):
                made += 1
            elif not os.path.lexists(os.path.join(apps, target + ".svg")):
                print(f"  ! {v}: cible absente pour {alias} -> {target}")
        # icônes Roudix (variante claire = fichier -light)
        light = v == "Roudix-Light"
        for src, name in ROUDIX_APPS:
            p = os.path.join(REPO, src.format(v="-light" if light else "", vv="light" if light else "dark"))
            if os.path.exists(p):
                shutil.copyfile(p, os.path.join(apps, name + ".svg"))
            else:
                print(f"  ! {v}: source absente {p}")
        print(v, "ok:", len(NEW), "icônes,", made, "alias")


def key_name(n):
    return n


main()
