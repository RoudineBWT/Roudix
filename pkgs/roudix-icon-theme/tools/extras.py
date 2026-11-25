#!/usr/bin/env python3
"""Retouches appliquées par-dessus la sortie de build_roudix.py (à relancer après une régénération).

  * places/user-desktop.svg : dossier Roudix + glyphe écran (au lieu d'une tuile), comme les autres dossiers
  * mimetypes/application-zip.svg : page à fermeture éclair, utilisée pour zip/tar/gz/7z/rar... ;
    package-x-generic (boîte) reste pour deb/rpm/jar/flatpak...
  * mimetypes/text-x-nix.svg : page + flocon NixOS en dégradé Roudix (sinon Papirus affiche son flocon bleu)

Usage : python3 tools/extras.py [<dossier du thème>]   (défaut : le dossier parent de tools/)
"""
import os, re, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VARIANTS = ["Roudix", "Roudix-Light"]

MONITOR = '<rect width="20" height="14" x="2" y="3" rx="2" /> <line x1="8" x2="16" y1="21" y2="21" /> <line x1="12" x2="12" y1="17" y2="21" />'

# fichiers « paquet » qui gardent la boîte (package-x-generic) ; tout le reste des archives passe à la fermeture éclair
KEEP_PACKAGE = re.compile(r"(deb|rpm|jar|java|pak|squashfs|shar|xzpdf|package-x-generic)")

EXTRA_ARCHIVE_NAMES = [
    "application-x-zip-compressed", "application-zstd", "application-x-zstd-compressed-tar", "application-x-zstd",
    "application-x-tgz", "application-x-tbz", "application-x-tbz2", "application-x-txz", "application-x-tzst",
    "application-x-lrzip", "application-x-lrzip-compressed-tar", "application-x-winzip", "application-x-winrar",
    "application-x-7zip-compressed", "application-x-gtar", "application-x-ustar", "application-x-cab",
    "application-x-xar", "application-x-lzh", "application-x-lzh-compressed", "application-x-bzip2",
    "application-x-lz", "application-x-zpaq", "application-x-gz", "application-x-bz2",
]


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def link(dirpath, name, target):
    p = os.path.join(dirpath, name + ".svg")
    if os.path.lexists(p):
        os.remove(p)
    os.symlink(target + ".svg", p)


def desktop_folder(v):
    places = os.path.join(ROOT, v, "scalable", "places")
    s = read(os.path.join(places, "folder-documents.svg"))
    s = re.sub(r"((?:bg|sh|gl|gb|fo|pg))f5\b", r"\1fud", s)           # ids uniques
    s = re.sub(r'(<g transform="translate\(17 21\.5\) scale\(0\.5833\)"[^>]*>).*?(</g>)',
               lambda m: m.group(1) + MONITOR + m.group(2), s, flags=re.S)
    p = os.path.join(places, "user-desktop.svg")
    if os.path.lexists(p):
        os.remove(p)
    write(p, s)


def zip_page(v):
    mime = os.path.join(ROOT, v, "scalable", "mimetypes")
    base = read(os.path.join(mime, "package-x-generic.svg"))
    m = re.search(r'stroke="(#[0-9a-fA-F]+)" opacity="([0-9.]+)"', base)
    sh_col, sh_op = m.group(1), m.group(2)
    head = base[:base.index('  <g transform="translate(16 20)')]       # tuile page sans glyphe
    gid = re.search(r'id="(gl[a-z0-9]+)"', head).group(1)

    teeth = []
    for k in range(6):
        teeth.append(f'<rect x="20.2" y="{7 + k * 4:g}" width="2.9" height="2.2" rx="0.5"/>')
        teeth.append(f'<rect x="23.1" y="{9 + k * 4:g}" width="2.9" height="2.2" rx="0.5"/>')
    pull = '<rect x="20.6" y="32" width="5" height="8" rx="2.2" fill="none" stroke-width="1.6"/><rect x="22.4" y="34.2" width="1.4" height="2.6" rx="0.7"/>'
    grad = (f'  <linearGradient id="zg" x1="0" y1="7" x2="0" y2="40" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="#ffc878"/><stop offset="1" stop-color="#ff8c42"/></linearGradient>\n')
    # couleurs du glyphe de ce variant (dégradé du fichier d'origine)
    stops = re.search(rf'<linearGradient id="{gid}"[^>]*>(.*?)</linearGradient>', head, re.S).group(1)
    grad = (f'  <linearGradient id="zg" x1="0" y1="7" x2="0" y2="40" gradientUnits="userSpaceOnUse">{stops}</linearGradient>\n')
    head = head.replace("</defs>", grad + "  </defs>", 1)

    shape = "".join(teeth)
    body = (f'  <g transform="translate(0 1)" fill="{sh_col}" stroke="{sh_col}" opacity="{sh_op}">{shape}{pull}</g>\n'
            f'  <g fill="url(#zg)" stroke="url(#zg)">{shape}{pull}</g>\n</svg>\n')
    out = os.path.join(mime, "application-zip.svg")
    if os.path.lexists(out):
        os.remove(out)
    write(out, head + body)

    # repointe les alias d'archives
    for f in sorted(os.listdir(mime)):
        p = os.path.join(mime, f)
        if os.path.islink(p) and os.readlink(p) == "package-x-generic.svg" and not KEEP_PACKAGE.search(f):
            os.remove(p)
            os.symlink("application-zip.svg", p)
    for n in EXTRA_ARCHIVE_NAMES:
        if not os.path.lexists(os.path.join(mime, n + ".svg")):
            link(mime, n, "application-zip")


def nix_page(v):
    d = os.path.join(ROOT, v, "scalable")
    page = read(os.path.join(d, "mimetypes", "package-x-generic.svg"))
    head = page[:page.index('  <g transform="translate(16 20)')]
    gb = re.search(r'id="(gb[a-z0-9]+)"', head).group(1)
    nixos = read(os.path.join(d, "apps", "nixos.svg"))
    paths = re.findall(r'^\s*<path transform="[^"]*" d="[^"]*"[^>]*/>\s*$', nixos, re.M)
    assert len(paths) == 2, f"nixos.svg inattendu ({len(paths)} chemins)"
    paths = [re.sub(r"url\(#gb[^)]*\)", f"url(#{gb})", p.strip()) for p in paths]
    # le flocon fait ~26 unités dans la tuile (centré en 24, 23.4) ; sur la page : ~19, centré en (23.5, 29.5)
    k = 19 / 26
    wrap = f'translate(23.5 29.5) scale({k:.4f}) translate(-24 -23.4)'
    body = f'  <g transform="{wrap}">\n    ' + "\n    ".join(paths) + '\n  </g>\n</svg>\n'
    out = os.path.join(d, "mimetypes", "text-x-nix.svg")
    if os.path.lexists(out):
        os.remove(out)
    write(out, head + body)


for v in VARIANTS:
    desktop_folder(v)
    zip_page(v)
    nix_page(v)
print("ok")
