#!/usr/bin/env python3
"""Complète le thème : tout nom d'icône que Tela (puis Papirus) dessine et que Roudix ne couvrait pas tombait sur
Papirus-Dark avec ses couleurs d'origine. Ce script comble les trous, dans la palette Roudix :

  * apps       : le SVG Tela (sinon Papirus) est converti par roudixify (rampe brun -> orange -> crème) et inséré dans la
                 tuile Roudix ; chaque fichier source n'est converti qu'une fois, les autres noms sont des liens
  * places     : dossiers / maison / bureau / corbeille / réseau -> icônes Roudix les plus proches (pas de dossiers bleus)
  * mimetypes  : par famille (pdf, tableur, archive, audio...) -> pages Roudix existantes
  * devices    : par famille (optique, disque, clavier...) -> icônes Roudix existantes

Les variantes de couleur de Tela (blue-folder, folder_color_*, default-*...) sont ignorées : le thème n'a qu'une couleur.

Usage : python3 tools/extras_complete.py <Tela-icon-theme> <Papirus/64x64/apps> [<dossier du thème>]
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roudixify

TELA, PAP = sys.argv[1], sys.argv[2]
ROOT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VARIANTS = {"Roudix": "dark", "Roudix-Light": "light"}


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def lexists(p):
    return os.path.lexists(p)


def link(d, name, target):
    p = os.path.join(d, name + ".svg")
    if lexists(p) or name == target:
        return False
    if not lexists(os.path.join(d, target + ".svg")):
        return False
    os.symlink(target + ".svg", p)
    return True


# ------------------------------------------------------------------ sources
def tela_src(name, depth=0):
    """Fichier réel Tela pour un nom d'app (src, ou lien -> src), sinon None."""
    p = f"{TELA}/src/scalable/apps/{name}.svg"
    if os.path.isfile(p):
        return p
    l = f"{TELA}/links/scalable/apps/{name}.svg"
    if os.path.islink(l) and depth < 6:
        return tela_src(os.path.basename(os.readlink(l))[:-4], depth + 1)
    return None


def pap_src(name):
    p = f"{PAP}/{name}.svg"
    if lexists(p):
        r = os.path.realpath(p)
        if os.path.isfile(r):
            return r
    return None


def tela_names(cat):
    names = set()
    for d in (f"{TELA}/src/scalable/{cat}", f"{TELA}/links/scalable/{cat}"):
        if os.path.isdir(d):
            names |= {f[:-4] for f in os.listdir(d) if f.endswith(".svg")}
    return names


# ------------------------------------------------------------------ apps
def do_apps(v, vkey):
    apps = os.path.join(ROOT, v, "scalable", "apps")
    have = {f[:-4] for f in os.listdir(apps)}
    sample = read(os.path.join(apps, "roudix-0ad.svg"))
    head = sample[:sample.index("  <svg x=")]
    pap = {f[:-4] for f in os.listdir(PAP) if f.endswith(".svg")}
    names = sorted((tela_names("apps") | pap) - have)
    canon_of = {}                     # fichier source -> nom canonique (ou None si inconvertible)
    made = linked = skipped = 0
    for n in names:
        src = tela_src(n) or pap_src(n)
        if not src:
            skipped += 1
            continue
        if src not in canon_of:
            canon = "roudix-" + re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(src)[:-4])
            if lexists(os.path.join(apps, canon + ".svg")):
                canon_of[src] = canon                      # déjà converti par build_roudix.py
            else:
                try:
                    res = roudixify.import_inner(src, vkey, len(canon_of))
                except Exception:
                    res = None
                if not res:
                    canon_of[src] = None
                else:
                    (x, y, w, h), inner = res
                    u = f"c{len(canon_of)}"
                    hd = head.replace("t0", u)
                    body = (f'  <svg x="7" y="6.5" width="34" height="34" viewBox="{x:g} {y:g} {w:g} {h:g}">{inner}</svg>\n</svg>\n')
                    with open(os.path.join(apps, canon + ".svg"), "w", encoding="utf-8") as f:
                        f.write(hd + body)
                    canon_of[src] = canon
                    made += 1
        c = canon_of[src]
        if not c:
            skipped += 1
        elif link(apps, n, c):
            linked += 1
    return made, linked, skipped


# ------------------------------------------------------------------ places / devices / mimetypes : par famille
COLOR_VARIANT = re.compile(r"^(blue|brown|custom|default|green|grey|folder_color)[-_]|^folder-(black|blue|brown|cyan|green|grey|magenta|orange|red|violet|yellow)$")

PLACES = [  # (regex, cible) — premier qui correspond ; la cible doit exister dans le thème
    (r"trash.*(full)|full.*trash", "user-trash-full"),
    (r"trash", "user-trash"),
    (r"desktop", "user-desktop"),
    (r"home", "user-home"),
    (r"bookmark", "user-bookmarks"),
    (r"(smb|nfs|ssh|ftp|dav|share-?point|web|network|server|workgroup|dev-network|fs-network|fs-share)", "folder-network"),
    (r"open|visiting|accept", "folder-open"),
    (r"document|doc|txt|text|table|presentation|book", "folder-documents"),
    (r"download", "folder-download"),
    (r"music|sound|podcast|library", "folder-music"),
    (r"pict|image|photo|camera|drawing|paint|design", "folder-pictures"),
    (r"video|movie", "folder-videos"),
    (r"git|build|gradle|unity|godot|html|java|docker|script|root|system|android|flatpak|snap|deb|rpm|tar|extension", "folder-development"),
    (r"games?|steam", "folder-games"),
    (r"lock|private|encrypt|decrypt|sign", "folder-locked"),
    (r"cloud|drive|dropbox|gdrive|onedrive|owncloud", "folder-cloud"),
    (r"mail", "folder-mail"),
    (r"recent|log|crash", "folder-recent"),
    (r"public", "folder-publicshare"),
    (r"^(gnome-fs-|gtk-)?(directory|folder)|^folder|^gnome-folder|^inode", "folder"),
]
DEVICES = [
    (r"floppy", "media-floppy"),
    (r"cd|dvd|disc|optical|blu-?ray", "media-optical"),
    (r"flash|memory|sd|stick|sm$|media-cf|media-ms|media-sm", "media-flash"),
    (r"usb|removable|pendrive", "drive-removable-media-usb"),
    (r"harddisk|drive|blockdev|system", "drive-harddisk"),
    (r"keyboard", "input-keyboard"), (r"mouse|pointing|pointer", "input-mouse"),
    (r"printer", "printer"), (r"scanner", "scanner"), (r"camera", "camera-photo"),
    (r"battery", "battery"), (r"bluetooth|blueman-(?!mouse|keyboard)", "bluetooth"),
    (r"ethernet|wired", "network-wired"), (r"wireless|wavelan|hotspot", "network-wireless"),
    (r"modem|cellular", "network-modem"), (r"server|database", "network-server"),
    (r"laptop", "computer-laptop"), (r"computer|display|desktop", "computer"),
    (r"phone|handheld|pda|ipod", "phone"), (r"headset|headphone", "audio-headphones"),
    (r"loudspeaker|speaker", "audio-speakers"), (r"television|video", "video-display"),
    (r"wii|gaming|joystick", "input-gaming"),
]
MIMES = [
    (r"pdf|postscript|dvi|djvu|xps|chm", "application-pdf"),
    (r"excel|spreadsheet|calc|\.xls|csv|ods|sheet|gnumeric|applix-spreadsheet|siag|insync.*(sheet|table)", "x-office-spreadsheet"),
    (r"powerpoint|presentation|impress|\.ppt|odp|slide|kpresenter|stardivision.*impress", "x-office-presentation"),
    (r"drawing|draw|visio|dia-(diagram|shape)|autocad|dwg|photoshop|gimp|krita|inkscape|svg|scribus|google-apps\.(drawing)", "x-office-drawing"),
    (r"calendar|alarm|todo|journal|akonadi\.(note|calendar)", "x-office-calendar"),
    (r"contact|addressbook|vcard|pkcs|pgp|pem|pkix|keystore|certificate|keepass|kwallet|spkac", "x-office-address-book"),
    (r"rfc822|mail|msoutlook|outlook|eml|mbox", "message-rfc822"),
    (r"epub|ebook|mobi|fb2|oebps|kword|bbeb", "application-epub+zip"),
    (r"font", "font-x-generic"),
    (r"audio|midi|mpegurl|mp3|ogg|flac|wav|sound|cda|rosegarden|jokosher", "audio-x-generic"),
    (r"video|matroska|mplayer|flash|asf|ram$|wmpl|wpl|mpeg", "video-x-generic"),
    (r"image|png|jpe?g|gif|bmp|tiff|icc|iccprofile|fits|raw|kra", "image-x-generic"),
    (r"sqlite|database|\.db|dbf|mdb|rdata|spss|r-project|spss-sav", "application-x-sqlite3"),
    (r"torrent|metalink|dlc|rsdf|ccf", "application-x-bittorrent"),
    (r"iso|disk-image|diskimage|cd-image|vmdk|vdi|qcow|floppy|-rom|snes|gameboy|gamecube|genesis|sega|nintendo", "application-x-cd-image"),
    (r"zip|tar|archive|compress|rar|7z|gz|bz|xz|lz|cab|ace|arj|asar|cpio|stuffit|binhex|macbinary|zoo", "application-zip"),
    (r"flatpak|xdgapp|appimage|apk|android-package|package|install|extension|theme-package|snap", "application-vnd.flatpak"),
    (r"sharedlib|shared-library|\.so|object|core|coredump|dll", "application-x-sharedlib"),
    (r"shellscript|shell|script|executable|bat|msdos|python|perl|ruby|php|gambas|kommander", "application-x-shellscript"),
    (r"source|java|class-file|xml|json|html|css|rdf|owl|gml|gpx|kml|geo|relaxng|mathml|rss|atom|javascript|yaml|sql|qt-|-ui$|-project$|cmake", "text-x-source"),
    (r"^model|stl|3d|blender|collada|sweethome|cad", "model-stl"),
    (r"^(text|application-(text|rtf|x-?(srt|sami|subrip|patch|tex|troff|lyx|gettext|desktop|mswrite))|application-vnd\.(oasis|sun|ms-word|ms-works|wordperfect|stardivision|kde)|application-msword|application-x-(abiword|kword|applix-word))", "text-x-generic"),
    (r"word|document|writer|\.doc|odt|rtf|wps|text", "text-x-generic"),
]


def pick(rules, name):
    for rx, tgt in rules:
        if re.search(rx, name, re.I):
            return tgt
    return None


def do_family(v, cat, rules, names, fallback=None, skip_color=False):
    d = os.path.join(ROOT, v, "scalable", cat)
    have = {f[:-4] for f in os.listdir(d)}
    n = 0
    for name in sorted(names - have):
        if skip_color and COLOR_VARIANT.search(name):
            continue
        tgt = pick(rules, name) or fallback
        if tgt and link(d, name, tgt):
            n += 1
    return n


def main():
    for v, vkey in VARIANTS.items():
        made, linked, skipped = do_apps(v, vkey)
        pl = do_family(v, "places", PLACES, tela_names("places"), skip_color=True)
        dv = do_family(v, "devices", DEVICES, tela_names("devices"))
        mt = do_family(v, "mimetypes", MIMES, tela_names("mimetypes"), fallback="application-octet-stream")
        print(f"{v}: apps +{made} convertis, +{linked} liens ({skipped} sans source) | places +{pl} | devices +{dv} | mimetypes +{mt}")


main()
