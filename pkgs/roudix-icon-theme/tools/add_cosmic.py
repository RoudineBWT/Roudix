#!/usr/bin/env python3
"""Comble les noms d'icônes attendus par COSMIC (cosmic-icons / libcosmic / cosmic-files) dans Roudix.

Le thème couvrait déjà KDE ; COSMIC (basé sur les noms Pop/COSMIC) demande en plus :

  1. des symboliques absentes de Papirus sous ce nom (pencil-symbolic, pin-symbolic, view-fit-symbolic,
     window-new-symbolic, preferences-*-symbolic, network-wireless-secure-signal-*-symbolic...) :
     on prend l'équivalent Papirus *déjà embarqué et recoloré* dans {16,22,24}/symbolic/* et on le copie
     sous le nom COSMIC ;
  2. quelques symboliques qui n'existent pas chez Papirus (grip-lines, insert-arrow, insert-ellipse, ratios,
     stroke-width, window-stack, navbar-open/closed, payment-card) : dessinées ici, même style (16 px,
     remplissage currentColor, classe ColorScheme-Text, couleur primaire Roudix) ;
  3. les emblèmes (emblem-default, -documents, -favorite, -important, -photos, -shared, -synchronizing,
     -system) : copiés de Papirus-Dark / Papirus-Light (16/22/24), recolorés en orange Roudix ;
  4. des alias (liens symboliques relatifs) dans scalable/{mimetypes,apps,devices} pour les noms COSMIC de
     types de fichiers (text-x-json, package-x-deb, text-x-csv...), les pages de réglages (preferences-*)
     et les périphériques audio, qui pointent vers les icônes Roudix existantes ;
  5. devices/payment-card.svg : tuile Roudix + glyphe carte bancaire (construite depuis audio-speakers.svg).

Idempotent. À lancer APRÈS add_papirus_ui.py et add_papirus_symbolic.py (qui réécrivent les dossiers
symbolic/ et la ligne Directories) et après extras*.py.

Usage : add_cosmic.py <papirus-icon-theme (dépôt)> [<Roudix racine>]
"""
import json, os, re, shutil, sys

PAP = sys.argv[1]
ROOT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VARIANTS = (("Roudix", "Papirus-Dark"), ("Roudix-Light", "Papirus-Light"))
SIZES = ("16", "22", "24")
CTXS = {"actions": "Actions", "apps": "Applications", "categories": "Categories", "devices": "Devices",
        "emblems": "Emblems", "mimetypes": "MimeTypes", "places": "Places", "status": "Status"}

PAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "assets", "palette", "Roudix.json")
try: _p = json.load(open(PAL))
except OSError: _p = {"dark": {"mPrimary": "#FF8C42"}, "light": {"mPrimary": "#E0661A"}}
PRIMARY = {"Roudix": _p["dark"]["mPrimary"], "Roudix-Light": _p["light"]["mPrimary"]}

# --------------------------------------------------------------------------------------------------
# 1. symboliques COSMIC -> (contexte COSMIC, [candidats Roudix/Papirus par ordre de préférence])
#    (noms SANS « -symbolic » ; on cherche dans tous les contextes de {size}/symbolic/)
# --------------------------------------------------------------------------------------------------
SYM = {
    # actions
    "close-menu": ("actions", ["window-close"]),
    "date": ("actions", ["x-office-calendar", "office-calendar", "calendar-go-today"]),
    "font": ("actions", ["font-select", "fonts", "font-x-generic"]),
    "image-crop-rotate": ("actions", ["image-crop", "tool-crop"]),
    "insert-drawing": ("actions", ["x-office-drawing", "tool-pencil"]),
    "insert-line": ("actions", ["tool-line"]),
    "insert-polygon": ("actions", ["tool-polygon"]),
    "insert-rectangle": ("actions", ["tool-rectangle"]),
    "insert-star": ("actions", ["starred", "star-large", "star-new"]),
    "markup": ("actions", ["tool-pencil", "document-edit"]),
    "notification-alert": ("actions", ["notification-active", "notification-new", "weather-severe-alert"]),
    "pen": ("actions", ["tool-pencil", "document-edit"]),
    "pencil": ("actions", ["tool-pencil", "document-edit"]),
    "pin": ("actions", ["view-pin"]),
    "printer-queue": ("actions", ["printer-printing", "printer"]),
    "text-highlight": ("actions", ["tool-highlight"]),
    "view-actual-size": ("actions", ["zoom-original"]),
    "view-fit": ("actions", ["zoom-fit-best"]),
    "window-new": ("actions", ["new-window"]),
    "window-swap": ("actions", ["lucide-arrow-right-left", "object-flip-horizontal"]),
    # apps (pages de réglages, utilitaires)
    "accessories-clock": ("apps", ["clock-alt", "feather-clock", "preferences-system-time"]),
    "addressbook": ("apps", ["x-office-address-book", "address-book-new"]),
    "application-font": ("apps", ["font-x-generic", "fonts"]),
    "chat": ("apps", ["chat-message-new", "mail-message-new", "message-indicator"]),
    "disk-usage-analyzer": ("apps", ["drive-harddisk-system", "drive-harddisk"]),
    "disks": ("apps", ["drive-harddisk", "drive-harddisk-system"]),
    "document-viewer": ("apps", ["graphics-viewer-document", "x-office-document"]),
    "firmware-manager": ("apps", ["application-x-firmware"]),
    "preferences-X11-applications": ("apps", ["application-x-executable", "preferences-desktop-apps"]),
    "preferences-appearance": ("apps", ["preferences-desktop-appearance", "appearance", "preferences-desktop-theme"]),
    "preferences-applications": ("apps", ["preferences-desktop-apps", "preferences-desktop-applications", "view-app-grid"]),
    "preferences-default-applications": ("apps", ["preferences-desktop-default-applications", "preferences-desktop-apps"]),
    "preferences-desktop": ("apps", ["user-desktop", "preferences-desktop-wallpaper", "display"]),
    "preferences-dock": ("apps", ["dock-left", "preferences-ubuntu-panel"]),
    "preferences-input-devices": ("apps", ["preferences-desktop-peripherals", "input-keyboard"]),
    "preferences-network-and-wireless": ("apps", ["preferences-system-network", "network-wireless"]),
    "preferences-panel": ("apps", ["preferences-ubuntu-panel", "dock-left"]),
    "preferences-power-and-battery": ("apps", ["preferences-system-power", "org.gnome.Settings-power", "power"]),
    "preferences-region-and-language": ("apps", ["preferences-desktop-locale", "org.gnome.Settings-region"]),
    "preferences-sound": ("apps", ["preferences-desktop-sound", "audio-volume-high"]),
    "preferences-startup-applications": ("apps", ["system-run", "application-x-executable"]),
    "preferences-time-and-language": ("apps", ["preferences-system-time", "preferences-desktop-locale"]),
    "preferences-updates-and-recovery": ("apps", ["software-update-available", "system-software-update"]),
    "preferences-vpn": ("apps", ["network-vpn"]),
    "preferences-window-management": ("apps", ["preferences-system-windows", "focus-windows"]),
    "preferences-wired": ("apps", ["network-wired"]),
    "preferences-wireless": ("apps", ["network-wireless"]),
    "preferences-workspaces": ("apps", ["workspaces"]),
    "weather": ("apps", ["weather-few-clouds", "weather-clear"]),
    # categories
    "applications-accessibility": ("categories", ["preferences-desktop-accessibility"]),
    "applications-video": ("categories", ["video-x-generic", "camera-video"]),
    # devices
    "audio-speaker": ("devices", ["audio-speakers"]),
    "audio-speaker-testing": ("devices", ["audio-speakers"]),
    "audio-subwoofer": ("devices", ["audio-speakers"]),
    "audio-subwoofer-testing": ("devices", ["audio-speakers"]),
    "speaker": ("devices", ["audio-speakers"]),
    # status
    "connection-secure": ("status", ["channel-secure", "network-wired-secure"]),
    "network-wireless-secure-signal-excellent": ("status", ["network-wireless-signal-excellent-secure"]),
    "network-wireless-secure-signal-good": ("status", ["network-wireless-signal-good-secure"]),
    "network-wireless-secure-signal-ok": ("status", ["network-wireless-signal-ok-secure"]),
    "network-wireless-secure-signal-weak": ("status", ["network-wireless-signal-weak-secure"]),
    "network-wireless-secure-signal-none": ("status", ["network-wireless-signal-none", "network-wireless-signal-none-secure"]),
    "plugged-into-power": ("status", ["ac-adapter", "battery-ac-adapter", "battery-full-charging"]),
    # places
    "applications-audio": ("places", ["audio-x-generic", "folder-music"]),
    "folder-recent": ("places", ["document-open-recent", "recent"]),
}

# --------------------------------------------------------------------------------------------------
# 2. symboliques dessinées (n'existent pas chez Papirus) : corps SVG dans un repère 16x16
#    (trait = stroke currentColor, plein = fill currentColor)
# --------------------------------------------------------------------------------------------------
S = 'fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"'
DRAWN = {
    "grip-lines": ("actions",
        '<rect x="2" y="3.25" width="12" height="1.5" rx=".75"/><rect x="2" y="7.25" width="12" height="1.5" rx=".75"/>'
        '<rect x="2" y="11.25" width="12" height="1.5" rx=".75"/>'),
    "insert-arrow": ("actions",
        '<path d="M2.6 12 10.2 4.4H6V2.6h7.4V10h-1.8V5.8L4 13.4z"/>'),
    "insert-ellipse": ("actions", f'<ellipse cx="8" cy="8" rx="6" ry="4.5" {S}/>'),
    "ratios": ("actions",
        f'<rect x="2" y="3.5" width="12" height="9" rx="1.5" {S}/><rect x="8.5" y="7" width="3.5" height="3" rx=".5"/>'),
    "stroke-width": ("actions",
        '<rect x="2" y="2.5" width="12" height="1" rx=".5"/><rect x="2" y="6" width="12" height="2" rx="1"/>'
        '<rect x="2" y="10.25" width="12" height="3.5" rx="1.75"/>'),
    "window-stack": ("actions",
        f'<path d="M5 5V3.3C5 2.6 5.6 2 6.3 2h6.4C13.4 2 14 2.6 14 3.3v5.4c0 .7-.6 1.3-1.3 1.3H11" {S}/>'
        f'<rect x="2" y="5" width="9" height="9" rx="1.3" {S}/>'),
    "navbar-open": ("actions",
        f'<rect x="2" y="2.75" width="12" height="10.5" rx="1.5" {S}/><path d="M3.5 3.5H6v9H3.5z"/>'),
    "navbar-closed": ("actions",
        f'<rect x="2" y="2.75" width="12" height="10.5" rx="1.5" {S}/><path d="M6 3v10" {S}/>'),
    "payment-card": ("devices",
        f'<rect x="1.75" y="3.75" width="12.5" height="8.5" rx="1.5" {S}/><rect x="1.75" y="6" width="12.5" height="1.8"/>'
        '<rect x="3.5" y="9.5" width="3" height="1" rx=".5"/>'),
}

# --------------------------------------------------------------------------------------------------
# 3. emblèmes Papirus
# --------------------------------------------------------------------------------------------------
EMBLEMS = ["emblem-default", "emblem-documents", "emblem-favorite", "emblem-important", "emblem-photos",
           "emblem-shared", "emblem-synchronizing", "emblem-system"]
EMBLEM_RECOLOR = ("#455a64", "#546e7a", "#4285f4", "#3b5df4", "#2196f3", "#1e88e5", "#607d8b")

# --------------------------------------------------------------------------------------------------
# 4. alias scalables (liens symboliques relatifs) : nom COSMIC -> cibles Roudix par ordre de préférence
# --------------------------------------------------------------------------------------------------
ALIASES = {
    "mimetypes": {
        "application-x-ebook": ["application-x-mobipocket-ebook", "application-epub+zip"],
        "application-x-epub": ["application-epub+zip"],
        "package-x-deb": ["application-x-deb", "application-vnd.debian.binary-package"],
        "package-x-rpm": ["application-x-rpm"],
        "text-x-c#": ["text-x-csharp"],
        "text-x-cheader": ["text-x-chdr", "text-x-c++hdr"],
        "text-x-csv": ["text-csv"],
        "text-x-dockerfile": ["text-dockerfile"],
        "text-x-flatpak": ["application-vnd.flatpak"],
        "text-x-generic-template": ["x-office-document-template", "text-x-generic"],
        "text-x-godot": ["application-x-godot-resource", "application-x-godot-scene"],
        "text-x-html": ["text-html"],
        "text-x-json": ["application-json"],
        "text-x-just": ["text-x-makefile", "text-x-script", "text-x-generic"],
        "text-x-ron": ["application-json"],
        "text-x-xml": ["application-xml"],
        "x-office": ["x-office-document"],
        "x-office-database": ["application-vnd.oasis.opendocument.database", "application-database"],
    },
    "apps": {
        "application-default": ["application-default-icon", "application-x-executable"],
        "chat": ["internet-chat", "empathy", "im-message", "telegram", "org.gnome.Polari"],
        "preferences-about": ["roudix-cosmic-settings-about", "preferences-system-details"],
        "preferences-appearance": ["roudix-cosmic-settings-appearance", "preferences-desktop-theme"],
        "preferences-applications": ["roudix-cosmic-settings-apps", "preferences-desktop-apps"],
        "preferences-date-and-time": ["roudix-cosmic-settings-datetime", "preferences-system-time"],
        "preferences-default-applications": ["roudix-cosmic-settings-defaultapps", "preferences-desktop-default-applications"],
        "preferences-displays": ["preferences-desktop-display", "display"],
        "preferences-dock": ["roudix-cosmic-settings-dock", "dock-left"],
        "preferences-input-devices": ["roudix-cosmic-settings-input", "preferences-desktop-peripherals"],
        "preferences-mouse": ["roudix-cosmic-settings-mouse", "preferences-desktop-mouse"],
        "preferences-network-and-wireless": ["roudix-cosmic-settings-network", "preferences-system-network"],
        "preferences-panel": ["preferences-ubuntu-panel", "preferences-desktop"],
        "preferences-power-and-battery": ["preferences-system-power", "preferences-system-power-management"],
        "preferences-region-and-language": ["preferences-desktop-locale"],
        "preferences-startup-applications": ["preferences-system-startup", "preferences-system-session"],
        "preferences-system-and-accounts": ["system-users", "preferences-system-users"],
        "preferences-time-and-language": ["preferences-desktop-locale", "preferences-system-time"],
        "preferences-touchpad": ["preferences-desktop-touchpad", "touchpad"],
        "preferences-updates-and-recovery": ["software-update-available", "system-software-update"],
        "preferences-users": ["system-users", "preferences-system-users"],
        "preferences-vpn": ["preferences-system-network-vpn"],
        "preferences-window-management": ["preferences-system-windows"],
        "preferences-wired": ["network-wired", "preferences-system-network-ethernet"],
        "preferences-wireless": ["preferences-system-network", "network-wireless"],
        "preferences-workspaces": ["preferences-desktop-workspaces", "workspace-switcher"],
        "preferences-x11-applications-compatibility": ["application-x-executable", "preferences-desktop-apps"],
    },
    "devices": {
        "audio-subwoofer": ["audio-speakers"],
        "audio-subwoofer-testing": ["audio-speakers"],
    },
}

# dans les gabarits de tuile Roudix, les 2 groupes « glyphe » (ombre + dégradé) commencent par translate(11 ..)
CARD_INNER = ('<rect width="20" height="14" x="2" y="5" rx="2" /> <line x1="2" x2="22" y1="10" y2="10" /> '
              '<line x1="6" x2="6.01" y1="15" y2="15" /> <line x1="10" x2="10.01" y1="15" y2="15" />')


def recolor_text(t, primary):
    t = re.sub(r"#(?:dfdfdf|444444)", primary, t, flags=re.I)
    return t.replace('id="current-color-scheme"', 'id="roudix-color-scheme"')


def drawn_svg(body, size, primary):
    off = (size - 16) / 2
    off = int(off) if off == int(off) else off
    g = f'<g transform="matrix(1,0,0,1,{off},{off})">{body}</g>' if off else body
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" version="1.1">\n'
            ' <defs>\n  <style id="roudix-color-scheme" type="text/css">\n'
            f'   .ColorScheme-Text {{ color:{primary}; }}\n  </style>\n </defs>\n'
            f' <g class="ColorScheme-Text" style="fill:currentColor">{g}</g>\n</svg>\n')


def find_symbolic(theme, size, cand):
    for ctx in CTXS:
        p = os.path.join(theme, f"{size}x{size}", "symbolic", ctx, f"{cand}-symbolic.svg")
        if os.path.exists(p):                       # os.path.exists suit les symlinks
            return os.path.realpath(p)
    return None


def main():
    report = {}
    for variant, pap in VARIANTS:
        theme = os.path.join(ROOT, variant)
        primary = PRIMARY[variant]
        rep = report[variant] = {"sym_copied": 0, "sym_drawn": 0, "sym_unresolved": [],
                                 "emblems": 0, "aliases": 0, "alias_unresolved": [], "dirs": set()}

        # --- 1 + 2 : symboliques --------------------------------------------------------------
        for size in SIZES:
            for name, (ctx, cands) in SYM.items():
                dst_dir = os.path.join(theme, f"{size}x{size}", "symbolic", ctx)
                os.makedirs(dst_dir, exist_ok=True)
                dst = os.path.join(dst_dir, f"{name}-symbolic.svg")
                if os.path.lexists(dst): os.remove(dst)
                src = next((s for s in (find_symbolic(theme, size, c) for c in cands) if s), None)
                if src is None:
                    if size == SIZES[0]: rep["sym_unresolved"].append(name)
                    continue
                shutil.copyfile(src, dst); rep["sym_copied"] += 1; rep["dirs"].add(f"{size}x{size}/symbolic/{ctx}")
            for name, (ctx, body) in DRAWN.items():
                dst_dir = os.path.join(theme, f"{size}x{size}", "symbolic", ctx)
                os.makedirs(dst_dir, exist_ok=True)
                with open(os.path.join(dst_dir, f"{name}-symbolic.svg"), "w", encoding="utf-8") as f:
                    f.write(drawn_svg(body, int(size), primary))
                rep["sym_drawn"] += 1; rep["dirs"].add(f"{size}x{size}/symbolic/{ctx}")

        # --- 3 : emblèmes Papirus --------------------------------------------------------------
        for size in SIZES:
            src_dir = os.path.realpath(os.path.join(PAP, pap, f"{size}x{size}", "emblems"))
            dst_dir = os.path.join(theme, f"{size}x{size}", "emblems")
            shutil.rmtree(dst_dir, ignore_errors=True)
            if not os.path.isdir(src_dir): continue
            os.makedirs(dst_dir)
            for e in EMBLEMS:
                s = os.path.join(src_dir, e + ".svg")
                if not os.path.exists(s): continue
                t = open(os.path.realpath(s), encoding="utf-8").read()
                for c in EMBLEM_RECOLOR: t = re.sub(re.escape(c), primary, t, flags=re.I)
                t = recolor_text(t, primary)
                open(os.path.join(dst_dir, e + ".svg"), "w", encoding="utf-8").write(t)
                rep["emblems"] += 1
            rep["dirs"].add(f"{size}x{size}/emblems")

        # --- 4 : alias scalables ---------------------------------------------------------------
        for ctx, table in ALIASES.items():
            d = os.path.join(theme, "scalable", ctx)
            for name, cands in table.items():
                dst = os.path.join(d, name + ".svg")
                if os.path.lexists(dst) and not os.path.islink(dst):
                    continue                        # vraie icône déjà dessinée : on n'y touche pas
                tgt = next((c for c in cands if c != name and os.path.exists(os.path.join(d, c + ".svg"))), None)
                if tgt is None:
                    rep["alias_unresolved"].append(f"{ctx}/{name}"); continue
                if os.path.lexists(dst): os.remove(dst)
                os.symlink(tgt + ".svg", dst); rep["aliases"] += 1

        # --- 5 : tuile payment-card (depuis audio-speakers) ------------------------------------
        tpl = os.path.join(theme, "scalable", "devices", "audio-speakers.svg")
        if os.path.exists(tpl):
            t = open(os.path.realpath(tpl), encoding="utf-8").read()
            # remplace le contenu des deux <g transform="translate(11 ..) scale(..)"> (ombre + glyphe)
            t = re.sub(r'(<g transform="translate\(11 1[01]\) scale\(1\.0833\)"[^>]*>).*?(</g>)',
                       lambda m: m.group(1) + CARD_INNER + m.group(2), t, flags=re.S)
            dst = os.path.join(theme, "scalable", "devices", "payment-card.svg")
            if os.path.lexists(dst): os.remove(dst)
            open(dst, "w", encoding="utf-8").write(t)

        # --- index.theme : dossiers emblems (16/22/24) -----------------------------------------
        idx = os.path.join(theme, "index.theme")
        s = open(idx, encoding="utf-8").read()
        s = re.sub(r"\n\[\d+x\d+/emblems\]\n(?:[^\[\n].*\n)*", "\n", s)
        m = re.search(r"^Directories=(.*)$", s, re.M)
        old = [x for x in m.group(1).split(",") if not x.endswith("/emblems")]
        new = sorted(d for d in rep["dirs"] if d.endswith("/emblems"))
        known_sym = [d for d in rep["dirs"] if "/symbolic/" in d and d not in old]
        i = next((k for k, x in enumerate(old) if x.startswith("scalable/")), len(old))
        s = s[:m.start()] + "Directories=" + ",".join(old[:i] + known_sym + new + old[i:]) + s[m.end():]
        s = s.rstrip("\n") + "\n"
        for d in known_sym + new:
            ctx = d.split("/")[-1]
            s += f"\n[{d}]\nContext={CTXS[ctx]}\nSize={d.split('x')[0]}\nType=Fixed\n"
        open(idx, "w", encoding="utf-8").write(s)

    for v, r in report.items():
        print(f"{v}: {r['sym_copied']} symboliques copiés (Papirus), {r['sym_drawn']} dessinés, {r['emblems']} emblèmes, "
              f"{r['aliases']} alias scalables")
        if r["sym_unresolved"]: print("  symboliques non résolus :", ", ".join(r["sym_unresolved"]))
        if r["alias_unresolved"]: print("  alias non résolus :", ", ".join(r["alias_unresolved"]))


main()
