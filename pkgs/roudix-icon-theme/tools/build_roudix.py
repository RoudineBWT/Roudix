#!/usr/bin/env python3
"""Génère le thème d'icônes Roudix (Roudix + Roudix-Light), autonome.

  apps        : logos simple-icons (CC0) dans une tuile Roudix + apps génériques (glyphes Lucide, ISC)
  categories  : applications-*
  places      : dossiers Roudix, maison, bureau, corbeille, logo Roudix (start-here)
  mimetypes   : pages Roudix avec un glyphe par type de fichier
  devices     : disques, clés USB, clavier, souris, imprimante, etc.

Usage : build_roudix.py <Tela-icon-theme> <simple-icons/package> <lucide-static/package> <logo-roudix.svg> <sortie> [Papirus/64x64/apps]
(Tela ne sert qu'à récupérer les bons noms d'icônes d'applications.)
"""
import json, os, re, sys, shutil
from svgelements import Path as SvgPath

TELA, SI, LUC, LOGO, OUT = sys.argv[1:6]
PAPIRUS = sys.argv[6] if len(sys.argv) > 6 else None      # .../Papirus/64x64/apps (optionnel)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roudixify
from flatten_nested_svg import flatten_nested   # Qt ignore les <svg> imbriqués

# ------------------------------------------------------------------ sources
tela = set()
for d in (f"{TELA}/src/scalable/apps", f"{TELA}/links/scalable/apps"):
    for f in os.listdir(d):
        if f.endswith(".svg"):
            tela.add(f[:-4])

si = json.load(open(f"{SI}/data/simple-icons.json"))
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
idx = {}
for e in si:
    for k in {e["slug"], e["title"], *e.get("aliases", {}).get("aka", [])}:
        idx.setdefault(norm(k), e["slug"])

missing = []
def lucide(*cands):
    for c in cands:
        p = f"{LUC}/icons/{c}.svg"
        if os.path.exists(p):
            s = open(p, encoding="utf-8").read()
            s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
            inner = re.search(r"<svg[^>]*>(.*)</svg>", s, flags=re.S).group(1)
            return re.sub(r"\s+", " ", inner).strip()
    missing.append(cands)
    return None

def brand(slug):
    if slug in CUSTOM_FILL: return CUSTOM_FILL[slug]
    s = open(f"{SI}/icons/{slug}.svg", encoding="utf-8").read()
    return " ".join(re.findall(r'<path[^>]*\sd="([^"]+)"', s))

# ------------------------------------------------------------------ styles
STYLES = {
    "Roudix": dict(
        title="Roudix",
        tile=("#2a211b", "#211a15"), sheen=0.10, rim=("#ffffff", 0.06),
        glyph=("#ffc878", "#ff8c42"), shadow=("#000000", 0.30),
        fold=("#ffb468", "#ff8c42"), fback="#cc7034", fglyph="#4a2410", fshadow=0.28,
        page=("#2a211b", "#1c1511"), ear="#ffffff", earop=0.14,
    ),
    "Roudix-Light": dict(
        title="Roudix Light",
        tile=("#fbf5ee", "#f1e6d9"), sheen=0.55, rim=("#3b2f27", 0.10),
        glyph=("#e0661a", "#c98a1e"), shadow=("#3b2f27", 0.20),
        fold=("#f4a95a", "#e0661a"), fback="#b85a1c", fglyph="#fff4e6", fshadow=0.20,
        page=("#fbf5ee", "#f1e6d9"), ear="#3b2f27", earop=0.12,
    ),
}

def defs(st, u):
    return f'''<defs>
    <linearGradient id="bg{u}" x1="6" y1="4" x2="42" y2="44" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{st['tile'][0]}"/><stop offset="1" stop-color="{st['tile'][1]}"/></linearGradient>
    <linearGradient id="sh{u}" x1="24" y1="3" x2="24" y2="20" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#ffffff" stop-opacity="{st['sheen']}"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>
    <linearGradient id="gl{u}" x1="0" y1="0" x2="0" y2="24" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{st['glyph'][0]}"/><stop offset="1" stop-color="{st['glyph'][1]}"/></linearGradient>
    <linearGradient id="gb{u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{st['glyph'][0]}"/><stop offset="1" stop-color="{st['glyph'][1]}"/></linearGradient>
    <linearGradient id="fo{u}" x1="0" y1="17" x2="0" y2="41" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{st['fold'][0]}"/><stop offset="1" stop-color="{st['fold'][1]}"/></linearGradient>
    <linearGradient id="pg{u}" x1="8" y1="5" x2="40" y2="44" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{st['page'][0]}"/><stop offset="1" stop-color="{st['page'][1]}"/></linearGradient>
  </defs>'''

def svg(st, body, u="x"):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">\n  {defs(st,u)}\n{body}</svg>\n'

def tile_base(st, u):
    return f'''  <rect x="3" y="3" width="42" height="42" rx="10" fill="url(#bg{u})"/>
  <rect x="3" y="3" width="42" height="17" rx="10" fill="url(#sh{u})"/>
  <rect x="3.25" y="3.25" width="41.5" height="41.5" rx="9.75" fill="none" stroke="{st['rim'][0]}" stroke-opacity="{st['rim'][1]}" stroke-width="0.5"/>
'''

def glyph_fill(st, d, u):
    """Recentre et redimensionne le logo d'après sa vraie boîte englobante (plus de logos décalés ou trop petits)."""
    x0, y0, x1, y1 = SvgPath(d).bbox()
    w, h = x1 - x0, y1 - y0
    L = 30.0 if w / h > 1.7 else (26.0 if max(w, h) > 0 else 26.0)   # les logos larges ont droit à plus de largeur
    sc = L / max(w, h)
    if w / h > 1.7: sc = min(sc, 14.0 / h)                           # ... sans devenir trop hauts
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    tx, ty = 24 - cx * sc, 23.4 - cy * sc
    return (f'  <path transform="translate({tx:.3f} {ty+1:.3f}) scale({sc:.4f})" d="{d}" fill="{st["shadow"][0]}" opacity="{st["shadow"][1]}"/>\n'
            f'  <path transform="translate({tx:.3f} {ty:.3f}) scale({sc:.4f})" d="{d}" fill="url(#gb{u})"/>\n')

def glyph_stroke(st, inner, u, tx=11, ty=10, sc=1.0833, sw=1.8, stroke=None, shadow=True, extra=""):
    col = stroke or f"url(#gl{u})"
    attrs = f'fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="{sw}"'
    out = ""
    if shadow:
        out += f'  <g transform="translate({tx} {ty+1}) scale({sc})" {attrs} stroke="{st["shadow"][0]}" opacity="{st["shadow"][1]}">{inner}</g>\n'
    out += f'  <g transform="translate({tx} {ty}) scale({sc})" {attrs} stroke="{col}"{extra}>{inner}</g>\n'
    return out

def tile_brand(st, slug, u="x"):
    return svg(st, tile_base(st, u) + glyph_fill(st, brand(slug), u), u)

def tile_lucide(st, inner, u="x"):
    return svg(st, tile_base(st, u) + glyph_stroke(st, inner, u), u)

def tile_import(st, vb, inner, u="x", size=34):
    x, y, w, h = vb
    body = tile_base(st, u) + flatten_nested(24-size/2, 23.5-size/2, size, size, f"{x:g} {y:g} {w:g} {h:g}", inner)
    return svg(st, body, u).replace('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"', '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 48 48"', 1)

def page(st, inner, u="x"):
    body = f'''  <ellipse cx="24" cy="44.6" rx="14" ry="1.4" fill="#000" opacity="{0.22 if st['title']=='Roudix' else 0.12}"/>
  <path d="M11 4.5h17.5L40 16v25.5a3 3 0 0 1-3 3H11a3 3 0 0 1-3-3v-34a3 3 0 0 1 3-3z" fill="url(#pg{u})"/>
  <path d="M11 4.75h17.2l11.55 11.55v25.2a2.75 2.75 0 0 1-2.75 2.75H11a2.75 2.75 0 0 1-2.75-2.75v-34A2.75 2.75 0 0 1 11 4.75z" fill="none" stroke="{st['rim'][0] if st['title']=='Roudix' else st['rim'][0]}" stroke-opacity="{0.10 if st['title']=='Roudix' else 0.16}" stroke-width="0.5"/>
  <path d="M28.5 4.5V13a3 3 0 0 0 3 3H40z" fill="{st['ear']}" opacity="{st['earop']}"/>
'''
    body += glyph_stroke(st, inner, u, tx=16, ty=19, sc=0.6667, sw=2.2)
    return svg(st, body, u)

FOLD_BACK = "M5 11.5A3.5 3.5 0 0 1 8.5 8H19a3 3 0 0 1 2.3 1.1L24 12.5h15.5A3.5 3.5 0 0 1 43 16v21a3.5 3.5 0 0 1-3.5 3.5h-31A3.5 3.5 0 0 1 5 37z"
FOLD_FRONT = "M5 20.5A3.5 3.5 0 0 1 8.5 17h31a3.5 3.5 0 0 1 3.5 3.5v16.5a3.5 3.5 0 0 1-3.5 3.5h-31A3.5 3.5 0 0 1 5 37z"
FOLD_OPEN = "M8.2 19.5A3 3 0 0 1 11 17.5h31.2a2 2 0 0 1 1.95 2.45l-3.2 16.6A3.5 3.5 0 0 1 37.5 39.5H9a3.5 3.5 0 0 1-3.5-3.8z"

def folder(st, inner=None, u="x", opened=False):
    front = FOLD_OPEN if opened else FOLD_FRONT
    body = f'''  <ellipse cx="24" cy="42.2" rx="16" ry="1.6" fill="#000" opacity="{st['fshadow']}"/>
  <path d="{FOLD_BACK}" fill="{st['fback']}"/>
  <path d="{front}" fill="url(#fo{u})"/>
  <path d="M8.5 17.6h31" stroke="#ffffff" stroke-opacity="0.35" stroke-width="0.8" stroke-linecap="round"/>
'''
    if inner:
        body += glyph_stroke(st, inner, u, tx=17, ty=21.5, sc=0.5833, sw=2.4, stroke=st["fglyph"], shadow=False, extra=' stroke-opacity="0.85"')
    return svg(st, body, u)


# ------------------------------------------------------------------ marques redessinées à la main (absentes de simple-icons)
def rrect(x, y, w, h):
    r = min(w, h) / 2
    return (f"M{x+r:g} {y:g}h{w-2*r:g}a{r:g} {r:g} 0 0 1 {r:g} {r:g}v{h-2*r:g}a{r:g} {r:g} 0 0 1 -{r:g} {r:g}"
            f"h-{w-2*r:g}a{r:g} {r:g} 0 0 1 -{r:g} -{r:g}v-{h-2*r:g}a{r:g} {r:g} 0 0 1 {r:g} -{r:g}z")
def dot(cx, cy, r=1.5):
    return f"M{cx-r:g} {cy:g}a{r:g} {r:g} 0 1 1 {2*r:g} 0a{r:g} {r:g} 0 1 1 -{2*r:g} 0z"

CUSTOM_FILL = {
  # VS Code : lame + chevron en creux (sens inverse = trou)
  "custom-vscode": "M17.3 2 22 4.3v15.4L17.3 22 7.2 12.9 3.2 16 1.8 15.2V8.8L3.2 8l4 3.1z M17.3 7.4 11.4 12l5.9 4.6z",
  # Slack : 4 pilules + 4 points en moulinet
  "custom-slack": " ".join([rrect(8.2,1,3.6,10), rrect(13,8.2,10,3.6), rrect(12.2,13,3.6,10), rrect(1,12.2,10,3.6),
                             dot(5.4,3.2,1.8), dot(20.8,5.4,1.8), dot(18.6,20.8,1.8), dot(3.2,18.6,1.8)]),
}
CUSTOM_STROKE = {
  # Edge : anneau ouvert + vague
  "custom-edge": '<path d="M3.2 12h17.6a8.8 8.8 0 1 0-3 6.7"/><path d="M5.2 17.2C6.6 19.6 9 21 12 21"/>',
  # Chromium : anneau + centre + 3 rayons
  "custom-chromium": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.4"/><path d="M12 8.6h8.2M9.05 13.7 4.9 6.5M14.95 13.7 10.8 20.9"/>',
}
CUSTOM_NAMES = {
  "custom-vscode": ["code","visual-studio-code","com.visualstudio.code","com.visualstudio.code-oss","code-oss","code-oss-dev","vscode","com.vscodium.codium","vscodium","codium","visual-studio-code-insiders","code-insiders"],
  "custom-slack": ["slack","com.slack.Slack","slack-desktop","org.slack.Slack"],
  "custom-edge": ["microsoft-edge","com.microsoft.Edge","microsoft-edge-stable","microsoft-edge-beta","microsoft-edge-dev"],
  "custom-chromium": ["chromium","chromium-browser","org.chromium.Chromium","chrome-chromium"],
}

# ---- suite Office, Teams, Skype, Messenger… : formes reprises de Tela/Papirus, redessinées en glyphes Roudix
def _office(letter):
    back = '<path d="M11 6.5V3.5h7.3A1.7 1.7 0 0 1 20 5.2v13.6a1.7 1.7 0 0 1-1.7 1.7H11v-2"/><path d="M16.5 9.5h1.8M16.5 12.5h1.8M16.5 15.5h1.8"/>'
    return ('<g transform="translate(12 12) scale(1.3) translate(-11.5 -12)" stroke-width="1.5">'
            + back + '<rect x="3" y="6.5" width="12" height="12" rx="2.2"/>' + letter + '</g>')
_LETTERS = {
  "w": '<path d="M6 9.5l1.5 6 1.5-4.2 1.5 4.2 1.5-6"/>',
  "x": '<path d="M6.3 9.5l5.4 6M11.7 9.5l-5.4 6"/>',
  "p": '<path d="M7.3 15.5v-6h2.4a1.9 1.9 0 0 1 0 3.8H7.3"/>',
  "o": '<circle cx="9" cy="12.5" r="3"/>',
  "n": '<path d="M7 15.5v-6l4 6v-6"/>',
}
CUSTOM_STROKE.update({
  "custom-msword": _office(_LETTERS["w"]), "custom-msexcel": _office(_LETTERS["x"]),
  "custom-mspowerpoint": _office(_LETTERS["p"]), "custom-msoutlook": _office(_LETTERS["o"]),
  "custom-msonenote": _office(_LETTERS["n"]),
  "custom-teams": '<g transform="translate(12 12) scale(1.12) translate(-12 -12)" stroke-width="1.7"><rect x="2.8" y="6.5" width="12" height="12" rx="2.2"/><path d="M6.2 10.2h5.2M8.8 10.2v5.6"/><circle cx="17.6" cy="5.6" r="2.1"/><path d="M16.4 10h3.3a1.9 1.9 0 0 1 1.9 1.9v3.2a3.4 3.4 0 0 1-3.4 3.4"/></g>',
  "custom-skype": '<circle cx="12" cy="12" r="9"/><path d="M15.7 9.3c-.4-1.4-1.8-2.2-3.7-2.2-2 0-3.3 1-3.3 2.4 0 3.4 6.6 1.6 6.6 5 0 1.5-1.4 2.6-3.5 2.6-1.9 0-3.4-.9-3.9-2.3"/>',
  "custom-messenger": '<path d="M3.5 12a8.5 8.5 0 1 1 3.6 6.9L3.5 20.3l1.1-3.8A8.4 8.4 0 0 1 3.5 12z"/><path d="M7.2 14.3l3.6-3.8 2.4 2.2 3.6-3.7"/>',
  "custom-typora": '<rect x="3" y="3" width="18" height="18" rx="3.5"/><path d="M7.5 8h9M12 8v9"/>',
  "custom-remmina": '<circle cx="12" cy="12" r="9"/><path d="M8.3 8.3 12 12l-3.7 3.7M13.5 8.3l3.7 3.7-3.7 3.7"/>',
})
# Microsoft Office : "porte" pleine, évidée (sens inverse = trou)
CUSTOM_FILL["custom-msoffice"] = "M4.5 7.8 14.2 3l5.3 2v14.2L14.2 21l-9.7-4z M14.2 6.6 8.6 9.1V15l5.6 2.4z"
CUSTOM_NAMES.update({
  "custom-msword": ["ms-word"], "custom-msexcel": ["ms-excel"], "custom-mspowerpoint": ["ms-powerpoint"],
  "custom-msoutlook": ["ms-outlook"], "custom-msonenote": ["ms-onenote"], "custom-msoffice": ["ms-office"],
  "custom-teams": ["teams","microsoft-teams","microsoft-teams-insiders","teams-for-linux","com.microsoft.Teams","com.github.IsmaelMartinez.teams_for_linux"],
  "custom-skype": ["skype","com.skype.Client"],
  "custom-messenger": ["fbmessenger","messenger","facebook-messenger","caprine","com.sindresorhus.Caprine"],
  "custom-typora": ["typora"], "custom-remmina": ["remmina","org.remmina.Remmina"],
})
CUSTOM_NAMES["custom-vscode"] += ["visualstudiocode","visualstudiocode-insiders"]
CUSTOM_NAMES["custom-chromium"] += ["io.github.ungoogled_software.ungoogled_chromium","ungoogled-chromium"]

# Wordmarks trop larges pour une tuile carrée -> glyphe Roudix
SLUG_LUCIDE = {"zoom": ("video",), "vmware": ("box",), "kicad": ("cpu",)}

# ------------------------------------------------------------------ catalogues
# nom d'icône -> glyphes Lucide (le premier qui existe)
def L(*c): return c

GENERIC_APPS = {
 L("terminal-square","terminal"): ["utilities-terminal","terminal","konsole","org.kde.konsole","org.gnome.Ptyxis","xfce4-terminal","tilix","xterm","foot","com.system76.CosmicTerm","cosmic-term","qterminal","lxterminal","terminator","guake","yakuake","org.kde.yakuake","alacritty","kitty","org.gnome.Console","gnome-console","kgx","blackbox","com.raggesilver.BlackBox"],
 L("folder-open"): ["system-file-manager","file-manager","nautilus","org.gnome.Nautilus","nemo","thunar","org.xfce.thunar","org.kde.dolphin","dolphin","pcmanfm","pcmanfm-qt","com.system76.CosmicFiles","cosmic-files","org.gnome.Files","io.elementary.files","caja","krusader","org.kde.krusader","doublecmd","spacefm"],
 L("square-pen","file-pen"): ["accessories-text-editor","text-editor","org.gnome.TextEditor","gnome-text-editor","gedit","org.gnome.gedit","kate","org.kde.kate","kwrite","org.kde.kwrite","mousepad","org.xfce.mousepad","xed","pluma","leafpad","featherpad","com.system76.CosmicEdit","cosmic-edit","org.kde.kwrite"],
 L("calculator"): ["accessories-calculator","calculator","org.gnome.Calculator","gnome-calculator","org.kde.kcalc","kcalc","galculator","mate-calc","qalculate-gtk","io.github.Qalculate"],
 L("settings"): ["preferences-system","preferences-desktop","org.gnome.Settings","gnome-control-center","systemsettings","org.kde.systemsettings","systemsettings5","xfce4-settings-manager","cinnamon-settings","com.system76.CosmicSettings","cosmic-settings","unity-control-center","lxqt-config","mate-control-center","preferences-desktop-settings","org.gnome.tweaks","gnome-tweaks","org.gnome.Tweaks"],
 L("globe"): ["web-browser","internet-web-browser","browser","org.gnome.Epiphany","epiphany","org.kde.falkon","falkon","org.kde.konqueror","konqueror","midori","qutebrowser","org.qutebrowser.qutebrowser","microsoft-edge","com.microsoft.Edge","microsoft-edge-stable","microsoft-edge-beta","org.gnome.Web","luakit","surf","nyxt"],
 L("mail"): ["internet-mail","mail-client","email","org.gnome.Evolution","evolution","org.kde.kmail2","kmail","kmail2","org.gnome.Geary","geary","claws-mail","org.kde.kontact","kontact","sylpheed","mutt","aerc","org.mozilla.Thunderbird.mail"],
 L("calendar"): ["office-calendar","calendar","org.gnome.Calendar","gnome-calendar","org.kde.korganizer","korganizer","org.kde.kalendar","kalendar","org.kde.merkuro.calendar","evolution-calendar","io.elementary.calendar"],
 L("contact","book-user","users"): ["org.gnome.Contacts","gnome-contacts","org.kde.kaddressbook","kaddressbook","address-book","evolution-contacts","org.kde.merkuro.contact"],
 L("image"): ["org.gnome.Loupe","loupe","eog","org.gnome.eog","gwenview","org.kde.gwenview","ristretto","org.xfce.ristretto","shotwell","org.gnome.Shotwell","image-viewer","accessories-image-viewer","org.gnome.gThumb","gthumb","org.kde.digikam","digikam","feh","nomacs","org.nomacs.ImageLounge","viewnior","geeqie","org.gnome.Photos","gnome-photos","rapid-photo-downloader","darktable","org.darktable.Darktable","org.kde.kphotoalbum","rawtherapee","com.rawtherapee.RawTherapee"],
 L("crop","scan"): ["accessories-screenshot","org.gnome.Screenshot","gnome-screenshot","org.kde.spectacle","spectacle","flameshot","org.flameshot.Flameshot","xfce4-screenshooter","org.xfce.screenshooter","ksnip","org.ksnip.ksnip","shutter","org.gnome.Screenshot"],
 L("camera"): ["org.gnome.Cheese","cheese","camera","accessories-camera","org.gnome.Snapshot","snapshot","org.kde.kamoso","kamoso","guvcview"],
 L("circle-play","play"): ["org.gnome.Totem","totem","org.gnome.Showtime","showtime","org.kde.dragonplayer","dragonplayer","celluloid","io.github.celluloid_player.Celluloid","smplayer","info.smplayer.SMPlayer","parole","org.xfce.parole","multimedia-video-player","video-player","mpv","io.mpv.Mpv","haruna","org.kde.haruna","mplayer","gnome-mplayer","kaffeine","org.kde.kaffeine","io.github.iwalton3.jellyfin-media-player","org.jellyfin.JellyfinDesktop","jellyfinmediaplayer"],
 L("music"): ["org.gnome.Rhythmbox3","rhythmbox","org.kde.elisa","elisa","org.gnome.Music","gnome-music","lollypop","org.gnome.Lollypop","audacious","multimedia-audio-player","org.kde.juk","juk","clementine","org.clementine_player.Clementine","strawberry","org.strawberrymusicplayer.strawberry","amberol","io.bassi.Amberol","org.kde.amarok","amarok","quodlibet","io.github.quodlibet.QuodLibet","deadbeef","cantata","org.mpris.MediaPlayer2","sayonara","gnome-podcasts","org.gnome.Podcasts","fragments"],
 L("mic"): ["org.gnome.SoundRecorder","gnome-sound-recorder","org.kde.krecorder","krecorder","audio-input-microphone","gnome-sound-recorder","com.github.wwmm.easyeffects","com.github.wwmm.pulseeffects","easyeffects","pulseeffects"],
 L("volume-2"): ["multimedia-volume-control","pavucontrol","org.pulseaudio.pavucontrol","pavucontrol-qt","org.pipewire.Helvum","org.pipewire.Helvum","helvum","qpwgraph","org.rncbc.qpwgraph","org.kde.plasma.pa","preferences-desktop-sound","org.gnome.Settings-sound-symbolic","pulseaudio","pavucontrol"],
 L("activity"): ["utilities-system-monitor","org.gnome.SystemMonitor","gnome-system-monitor","org.kde.plasma-systemmonitor","plasma-systemmonitor","org.kde.ksysguard","ksysguard","xfce4-taskmanager","org.xfce.taskmanager","resources","net.nokyan.Resources","org.gnome.Usage","mission-center","io.missioncenter.MissionCenter","htop","btop","stacer","org.kde.ksystemlog","ksystemlog","conky","org.gnome.Logs","gnome-logs"],
 L("hard-drive"): ["org.gnome.DiskUtility","gnome-disks","org.gnome.Disks","org.kde.partitionmanager","partitionmanager","gparted","org.gnome.GParted","qdiskinfo","org.kde.kdiskfree","kdf","gsmartcontrol","io.github.gsmartcontrol","partition-manager","ventoy","org.kde.isoimagewriter","isoimagewriter","org.gnome.Disks","balena-etcher","balenaetcher","io.balena.Etcher","org.fedoraproject.MediaWriter","mediawriter","gnome-multi-writer","org.gnome.MultiWriter","usb-creator","usb-creator-gtk","usbimager","rufus"],
 L("chart-pie"): ["org.gnome.baobab","baobab","filelight","org.kde.filelight","qdirstat","k4dirstat","org.kde.kdirstat","ncdu","dust","gdmap"],
 L("shopping-bag"): ["org.gnome.Software","gnome-software","org.kde.discover","plasmadiscover","plasma-discover","system-software-install","softwarecenter","software-center","pamac","pamac-manager","io.elementary.appcenter","org.flathub.Flathub","org.kde.discover.flatpak","bauh","org.gnome.Software.Plugin","gnome-software-local-file","flathub","appimagelauncher","gearlever","it.mijorus.gearlever","io.github.flattool.Warehouse","com.github.tchx84.Flatseal","flatseal","org.kde.discover.notifier","system-software-update","software-update-available","org.gnome.PackageUpdater","pamac-tray"],
 L("archive"): ["org.gnome.FileRoller","file-roller","org.kde.ark","ark","engrampa","xarchiver","peazip","io.github.peazip.PeaZip","org.gnome.Archive","gnome-archive","ark.desktop","fr.romainvigier.Archive","com.github.ahrm.ark"],
 L("book-open"): ["org.gnome.Evince","evince","org.gnome.Papers","papers","org.kde.okular","okular","atril","zathura","org.pwmt.zathura","document-viewer","accessories-document-viewer","org.gnome.Document-Viewer","mupdf","xreader","org.x.Reader","foliate","com.github.johnfactotum.Foliate","calibre","com.calibre_ebook.calibre","org.kde.calibre","koreader","org.kde.kbook","org.kde.arianna","arianna","lyx","org.lyx.LyX","org.kde.kile"],
 L("notebook-pen","notebook","sticky-note"): ["org.gnome.gnote","gnote","org.kde.knotes","knotes","org.gnome.Notes","joplin","net.cozic.joplin_desktop","org.gnome.Notes","xpad","org.xfce.Xfce4-notes","xfce4-notes","com.github.flxzt.rnote","rnote","io.github.mezoahmedii.Picker","org.kde.kjots","org.kde.kjots","simplenote","standardnotes","org.standardnotes.standardnotes","com.logseq.Logseq","logseq"],
 L("clock"): ["org.gnome.clocks","gnome-clocks","org.kde.kclock","kclock","org.gnome.Clocks","xfce4-clock","org.kde.plasma.digitalclock","clock","org.kde.kalarm","kalarm","alarm-clock-applet","alarm-clock"],
 L("cloud-sun"): ["org.gnome.Weather","gnome-weather","org.kde.kweather","kweather","weather-app","weather","org.gnome.Weather.Application","io.github.amit9838.weather","com.github.amit9838.mousam"],
 L("map"): ["org.gnome.Maps","gnome-maps","org.kde.marble","marble","org.openstreetmap.josm","josm","qgis","org.qgis.qgis","org.kde.itinerary","itinerary","com.github.vikdevelop.googlemaps"],
 L("type"): ["org.gnome.font-viewer","gnome-font-viewer","org.kde.fontviewer","kfontview","org.kde.kfontinst","fontforge","org.fontforge.FontForge","font-manager","com.github.FontManager.FontManager","org.gnome.Fonts","fonts","fontmatrix","io.github.nokse22.Exhibit"],
 L("smile","languages","at-sign"): ["org.gnome.Characters","gnome-characters","accessories-character-map","gucharmap","org.gnome.Gucharmap","org.kde.kcharselect","kcharselect","io.github.nokse22.Exhibit","emote","com.tomjwatson.Emote","org.gnome.Fractal.Devel"],
 L("keyboard"): ["preferences-desktop-keyboard","input-keyboard","gnome-keyboard","org.kde.keyboard","fcitx","fcitx5","org.fcitx.Fcitx5","fcitx5-configtool","ibus","ibus-setup","org.freedesktop.IBus.Panel","onboard","florence","org.gnome.Settings-keyboard-symbolic","kbd","xkb-switch"],
 L("network","cable"): ["preferences-system-network","nm-connection-editor","network-manager","network-manager-applet","nm-applet","org.kde.plasma.networkmanagement","kde-nm-connection-editor","connman-gtk","cmst","wicd-gtk","network-config","system-config-network","org.gnome.Settings-network-symbolic","networkmanager","kcm_networkmanagement","org.kde.kcm_networkmanagement","io.github.NetworkManager"],
 L("bluetooth"): ["blueman","blueman-manager","blueberry","preferences-bluetooth","bluetooth","org.kde.bluedevil","bluedevil","bluetooth-settings","gnome-bluetooth-panel","bluedevil-wizard","org.kde.bluedevil-wizard","bluez","bluetooth-manager"],
 L("printer"): ["printer","system-config-printer","org.kde.print-manager","print-manager","preferences-devices-printer","hplip","hp-toolbox","org.gnome.Settings-printers-symbolic","cups","org.cups.cupsd","cups-config","kcm_printer_manager","gnome-printers-panel","xsane","org.xsane.XSane","simple-scan","org.gnome.SimpleScan"],
 L("monitor"): ["preferences-desktop-display","org.kde.kscreen","kscreen","display-settings","arandr","org.gnome.Settings-display-symbolic","lxrandr","xfce4-display-settings","org.xfce.display","nvidia-settings","org.freedesktop.nvidia-settings","gnome-display-panel","krandrtray","wdisplays","nwg-displays"],
 L("battery-charging"): ["preferences-system-power","org.kde.powerdevil","powerdevil","gnome-power-statistics","org.gnome.PowerStats","xfce4-power-manager","xfce4-power-manager-settings","power","power-profiles-daemon","tlp","tlpui","org.kde.plasma.battery","battery","cpupower-gui","gnome-power-panel","laptop-mode-tools","org.gnome.Settings-power-symbolic"],
 L("users","user-round"): ["system-users","user-info","org.gnome.Settings-users-symbolic","preferences-desktop-user","user-manager","org.kde.kuser","kuser","users-admin","accountsservice","cinnamon-settings-users","gnome-users-panel","org.gnome.Settings.users","org.freedesktop.accounts","userinfo","system-users-panel","kcm_users","mate-user-admin"],
 L("key-round","lock-keyhole"): ["preferences-system-privacy","preferences-desktop-security","org.gnome.seahorse.Application","seahorse","gnome-keyring","org.kde.kwalletmanager5","kwalletmanager","kwalletmanager5","org.kde.kwalletmanager","passwords","org.gnome.World.Secrets","secrets","org.kde.kgpg","kgpg","gpa","gnome-keyring-manager","kleopatra","org.kde.kleopatra","pass","org.gnome.Settings-privacy-symbolic","pinentry","keepass","gnome-privacy-panel","preferences-security","security-high","org.freedesktop.secrets","lastpass","1password-x"],
 L("shield"): ["gufw","firewall-config","org.fedoraproject.FirewallConfig","firewall","org.kde.kcm_firewall","ufw","opensnitch-ui","opensnitch","clamtk","com.github.davidcrabb.clamtk","bleachbit","org.bleachbit.BleachBit","bleachbit","timeshift-gtk","security-medium","org.kde.plasma.vault","org.kde.vault","vaults","io.github.nicotine_plus.Nicotine","glasswire","lynis","gnome-firewall","cryptomator","org.cryptomator.Cryptomator","veracrypt","org.veracrypt.VeraCrypt"],
 L("history","archive-restore"): ["org.gnome.DejaDup","deja-dup","timeshift","org.kde.kup","kup","backintime","backintime-qt","backintime-gnome","org.gnome.World.PikaBackup","pika-backup","borg","vorta","com.borgbase.Vorta","restic","luckybackup","grsync","org.gnome.Backups","backup","simple-backup","sbackup","bacula","systemback","clonezilla","rescuezilla","cronopete","duplicati","deja-dup-preferences"],
 L("circle-help","circle-question-mark"): ["help-browser","help","org.gnome.Yelp","yelp","help-about","khelpcenter","org.kde.khelpcenter","org.kde.help","gnome-help","support","org.gnome.Tour","gnome-tour","org.gnome.Help","documentation","ubuntu-help","info","org.kde.kinfocenter","kinfocenter","org.kde.kinfocenter","about","about-me","org.freedesktop.Platform","hardinfo","org.hardinfo.hardinfo","org.hardinfo2.hardinfo2","hardinfo2","cpu-x","io.github.thetumultuousunicornofdarkness.cpu-x","lshw-gtk","gnome-about","org.gnome.Settings-about-symbolic"],
 L("box","server"): ["org.gnome.Boxes","gnome-boxes","virt-manager","org.virt_manager.virt-manager","virtualbox","org.virtualbox.VirtualBox","vboxmanage","qemu","org.qemu.qemu","qemu-system","org.qemu.Qemu","cockpit","org.cockpit_project.cockpit","podman-desktop","io.podman_desktop.PodmanDesktop","distrobox","com.ranfdev.DistroShelf","org.gnome.Boxes.Extension","incus","lxd","lxc","vagrant","gnome-boxes-symbolic","virtualbox-ose","vmware-workstation","vmware-player","vmware-view","vmplayer","vmware-netcfg","org.kde.kvm","kvm","bochs","utm","com.github.marhkb.Pods","pods","distroshelf","containers"],
 L("code-xml","code"): ["code","visual-studio-code","com.visualstudio.code","com.visualstudio.code-oss","code-oss","code-oss-dev","vscode","com.vscodium.codium","vscodium","codium","org.gnome.Builder","gnome-builder","org.kde.kdevelop","kdevelop","geany","org.geany.Geany","org.gnome.gitg","gitg","org.kde.kate.dev","lite-xl","org.lite_xl.lite_xl","helix","emacs","org.gnu.emacs","gvim","vim","neovim","nvim","nano","sublime_text","sublime-text","com.sublimetext.three","sublime-merge","com.sublimemerge.App","org.eclipse.Java","eclipse","org.eclipse.Eclipse","netbeans","apache-netbeans","org.apache.netbeans","atom","io.atom.Atom","brackets","io.brackets.Brackets","bluefish","org.bluefish.Bluefish","com.github.marketplace.cursor","cursor","windsurf","kiro","trae","positron","com.positron.Positron","org.positron.Positron"],
 L("slack","hash"): ["slack","com.slack.Slack","slack-desktop","org.slack.Slack"],
 L("message-square","message-circle"): ["org.gnome.Fractal","fractal","org.gnome.Polari","polari","pidgin","org.kde.kopete","kopete","empathy","org.gnome.Empathy","hexchat","io.github.Hexchat","org.hexchat.HexChat","quassel","org.quassel_irc.QuasselClient","irssi","weechat","org.kde.neochat","neochat","element-desktop","im.riot.Riot","io.element.Element","nheko","io.github.NhekoReborn.Nheko","org.mozilla.Thunderbird.chat","gajim","org.gajim.Gajim","dino","im.dino.Dino","skype","com.skype.Client","microsoft-teams","com.microsoft.Teams","teams","teams-for-linux","com.github.IsmaelMartinez.teams_for_linux","microsoft-teams-insiders","org.kde.ruqola","ruqola","rocketchat","chat.rocket.RocketChat","mattermost","com.mattermost.Desktop","zulip","org.zulip.Zulip","jami","net.jami.Jami","revolt","chat.revolt.RevoltDesktop","session-desktop","network.loki.Session","threema","ch.threema.Threema","wire","com.wire.WireDesktop","keybase","io.keybase.Keybase","franz","com.meetfranz.Franz","ferdium","org.ferdium.Ferdium","rambox","com.rambox.Rambox","caprine","com.sindresorhus.Caprine","messenger","facebook-messenger","gitter","im.gitter.Gitter","hangouts","google-hangouts","org.gnome.Chat"],
 L("video"): ["org.kde.kdenlive.dev","shotcut","org.shotcut.Shotcut","openshot","org.openshot.OpenShot","org.openshot.OpenShot","pitivi","org.pitivi.Pitivi","olive","org.olivevideoeditor.Olive","flowblade","io.github.jliljebl.Flowblade","blender-video","davinci-resolve","resolve","DaVinciResolve","com.blackmagicdesign.resolve","handbrake","fr.handbrake.ghb","org.handbrake.ghb","fr.handbrake.HandBrake","org.handbrake.HandBrake","mkvtoolnix-gui","org.bunkus.mkvtoolnix-gui","avidemux","org.avidemux.Avidemux","losslesscut","no.mifi.losslesscut","kooha","io.github.seadve.Kooha","simplescreenrecorder","org.simplescreenrecorder.SimpleScreenRecorder","vokoscreen","vokoscreenNG","com.github.vkohaupt.vokoscreenNG","peek","com.uploadedlobster.peek","byzanz","green-recorder","com.github.rafostar.Clapper","clapper","org.kde.kmediaplayer"],
 L("gamepad-2"): ["applications-games","org.gnome.Chess","gnome-chess","org.gnome.Mines","gnome-mines","org.gnome.Sudoku","gnome-sudoku","org.gnome.Mahjongg","gnome-mahjongg","org.gnome.Aisleriot","aisleriot","org.gnome.Quadrapassel","quadrapassel","org.gnome.Tetravex","gnome-tetravex","org.gnome.Hitori","gnome-klotski","org.gnome.Klotski","org.gnome.Reversi","iagno","org.gnome.Lightsoff","lightsoff","org.gnome.Nibbles","gnome-nibbles","org.gnome.Robots","gnome-robots","org.gnome.Swell-foop","swell-foop","org.gnome.Five-or-More","five-or-more","org.gnome.Tali","tali","org.gnome.Taquin","gnome-taquin","org.kde.kmahjongg","kmahjongg","org.kde.kpat","kpat","org.kde.ksudoku","ksudoku","org.kde.kmines","kmines","org.kde.kolf","kolf","org.kde.kblocks","kblocks","org.kde.katomic","katomic","org.kde.kbounce","kbounce","org.kde.kbreakout","kbreakout","org.kde.kgoldrunner","kgoldrunner","org.kde.klines","klines","org.kde.kshisen","kshisen","org.kde.knavalbattle","knavalbattle","org.kde.kspaceduel","kspaceduel","org.kde.ksnakeduel","ksnakeduel","org.kde.ktuberling","ktuberling","org.kde.kubrick","kubrick","org.kde.kfourinline","kfourinline","gamemode","heroic","com.heroicgameslauncher.hgl","heroic-games-launcher","org.prismlauncher.PrismLauncher","prismlauncher","com.usebottles.bottles","bottles","com.github.Matoking.protontricks","protontricks","net.davidotek.pupgui2","protonup-qt","protonup","protonplus","com.vysp3r.ProtonPlus","org.openttd.OpenTTD","openttd","org.supertuxproject.SuperTux","supertux","org.supertuxkart.SuperTuxKart","supertuxkart","org.openarena.OpenArena","openarena","org.xonotic.Xonotic","xonotic","org.0ad.0AD","0ad","net.minetest.Minetest","minetest","org.luanti.luanti","luanti","org.srb2.SRB2","srb2","org.wesnoth.Wesnoth","wesnoth","com.mojang.Minecraft","minecraft","minecraft-launcher","org.kde.kigo","kigo","org.kde.kreversi","kreversi","org.kde.bomber","bomber","org.kde.granatier","granatier","org.kde.klickety","klickety","org.kde.kiriki","kiriki","org.kde.kjumpingcube","kjumpingcube","org.kde.killbots","killbots","org.kde.knights","knights","org.kde.kollision","kollision","org.kde.konquest","konquest","org.kde.kpatience","kpatience","org.kde.ksquares","ksquares","org.kde.ktron","ktron","org.kde.palapeli","palapeli","org.kde.picmi","picmi","org.kde.skladnik","skladnik","org.kde.kapman","kapman","org.kde.kdiamond","kdiamond","org.kde.kgoldrunner","org.kde.kcheckers","kcheckers","org.kde.kbattleship","kbattleship","org.kde.blinken","blinken","org.kde.kanagram","kanagram","org.kde.khangman","khangman","org.kde.kwordquiz","kwordquiz"],
 L("graduation-cap"): ["applications-education","org.kde.kalgebra","kalgebra","org.kde.kgeography","kgeography","org.kde.kturtle","kturtle","org.kde.kalzium","kalzium","org.kde.kstars","kstars","org.kde.step","step","org.kde.kbruch","kbruch","org.kde.kig","kig","org.kde.kmplot","kmplot","org.kde.cantor","cantor","org.kde.rocs","rocs","org.kde.parley","parley","org.kde.artikulate","artikulate","org.kde.kanagram","org.kde.minuet","minuet","org.kde.kteatime","kteatime","org.kde.ktouch","ktouch","org.kde.klettres","klettres","org.kde.kiten","kiten","org.kde.klatin","klatin","org.kde.kmouth","kmouth","org.kde.kolourpaint","kolourpaint-edu","anki","net.ankiweb.Anki","org.ankiweb.Anki","org.kde.kanki","tuxtype","tuxpaint","org.tuxpaint.Tuxpaint","tuxmath","scratch","edu.mit.Scratch","org.scratch.Scratch","stellarium","org.stellarium.Stellarium","celestia","space.celestia.Celestia","geogebra","org.geogebra.GeoGebra","octave","org.octave.Octave","maxima","wxmaxima","org.wxmaxima.wxMaxima","sagemath","org.sagemath.SageMath","jupyter","jupyterlab","org.jupyter.JupyterLab","rstudio","org.rstudio.RStudio","spyder","org.spyder_ide.spyder","orange","scilab","org.scilab.Scilab","freecad","org.freecad.FreeCAD","gnuplot","org.gnuplot.gnuplot","gcompris","org.kde.gcompris","gcompris-qt","org.kde.GCompris","avogadro","org.avogadro.Avogadro","gperiodic","xmind","org.xmind.XMind","freeplane","org.freeplane.App","vym","org.insilmaps.vym","mindmaster","com.edrawsoft.mindmaster"],
 L("palette"): ["applications-graphics","org.kde.kolourpaint","kolourpaint","org.kde.krita.dev","drawing","com.github.maoschanz.drawing","org.gnome.Drawing","pinta","com.github.PintaProject.Pinta","mypaint","org.mypaint.MyPaint","gpick","org.gpick.Gpick","org.gnome.Colorpicker","colorpicker","color-picker","com.github.finefindus.eyedropper","eyedropper","org.kde.kcolorchooser","kcolorchooser","com.github.tenderowl.frog","frog","org.gnome.design.Palette","palette","paletter","io.github.zefr0x.hashes","org.gnome.design.IconLibrary","icon-library","org.gnome.design.Contrast","contrast","org.gnome.design.Emblem","emblem","org.gnome.design.AppIconPreview","app-icon-preview","org.gnome.design.SymbolicPreview","symbolic-preview","org.gnome.design.Lorem","lorem","com.github.huluti.Curtail","curtail","io.gitlab.adhami3310.Impression","impression","io.gitlab.adhami3310.Converter","switcheroo","com.github.huluti.ColorPicker","com.rafaelmardojai.Blanket","blanket","org.kde.kruler","kruler","org.kde.kcolorchooser"],
 L("flask-conical"): ["applications-science","org.kde.labplot2","labplot2","labplot","org.kde.kstars.science","scidavis","org.scidavis.SciDAVis","gnuradio","org.gnuradio.GNURadio","gqrx","dev.gqrx.gqrx","org.gqrx.gqrx","cutecom","org.kde.cutecom","gtkwave","org.gtkwave.GTKWave","logisim","kicad-science","fritzing","org.fritzing.Fritzing","arduino","cc.arduino.IDE2","cc.arduino.arduinoide","org.arduino.IDE","platformio","org.platformio.PlatformIO","processing","org.processing.Processing","openscad","org.openscad.OpenSCAD","qelectrotech","org.qelectrotech.QElectroTech","lazarus","org.lazarus.Lazarus","pymol","org.pymol.PyMOL","jmol","org.jmol.Jmol","ugene","org.ugene.UGENE","bioconda","octave-gui","org.gnu.octave","scilab-science","speedcrunch","org.speedcrunch.SpeedCrunch","qalculate-science","org.kde.kalk","kalk"],
 L("briefcase"): ["applications-office","org.libreoffice.LibreOffice.office","onlyoffice","org.onlyoffice.desktopeditors","onlyoffice-desktopeditors","wps-office","com.wps.Office","wps-office-wps","wps-office-et","wps-office-wpp","wps-office-pdf","softmaker","freeoffice","com.softmaker.FreeOffice","calligra","org.kde.calligra","org.kde.calligrawords","org.kde.calligrasheets","org.kde.calligrastage","org.kde.calligraplan","calligraplan","gnumeric","org.gnumeric.Gnumeric","abiword","com.abisource.AbiWord","org.abiword.AbiWord","planner","org.gnome.Planner","gnucash","org.gnucash.GnuCash","homebank","fr.free.Homebank","kmymoney","org.kde.kmymoney","skrooge","org.kde.skrooge","money-manager-ex","org.moneymanagerex.MMEX","org.kde.kontact.office","scribus","net.scribus.Scribus","org.scribus.Scribus","pdfarranger","com.github.jeromerobert.pdfarranger","xournalpp","com.github.xournalpp.xournalpp","org.xournalpp.Xournalpp","okular-office","masterpdfeditor","masterpdfeditor5","com.code_industry.MasterPDFEditor","pdfsam","org.pdfsam.PdfSam","pdfmod","pdfshuffler","pdf-shuffler","ocrmypdf","paperwork","work.openpaper.Paperwork","simple-scan-office","tesseract","gscan2pdf","net.sourceforge.gscan2pdf","io.github.mawerickLP.MyApps"],
 L("app-window"): ["application-default-icon","application-x-executable","application-x-desktop","applications-other","applications-all","org.gnome.Application","kde","xdg-desktop-portal","application","app","unknown","exec","binary","executable","gnome-run","system-run","xorg","wayland-logo","xwayland","org.freedesktop.Xwayland","org.kde.plasma.systemtray","kdeconnect-indicator","kdeconnect","org.kde.kdeconnect","org.kde.kdeconnect.app","org.kde.kdeconnect.sms","org.kde.kdeconnect.handler","org.kde.kdeconnect.nonplasma","org.gnome.Shell.Extensions","gnome-shell-extension-prefs","org.gnome.Extensions","extensions","org.gnome.Shell.Extensions.GSConnect","org.gnome.Settings.Default","org.gnome.Settings.Application","org.gnome.Software.Application","com.github.tkashkin.gamehub","gamehub","com.github.donadigo.eddy","eddy","org.kde.kde-gtk-config"],
}

# Catégories (scalable/categories)
CATEGORIES = {
 "applications-accessories": ("wrench",), "applications-utilities": ("wrench",),
 "applications-development": ("code-xml","code"), "applications-education": ("graduation-cap",),
 "applications-games": ("gamepad-2",), "applications-graphics": ("palette",),
 "applications-internet": ("globe",), "applications-multimedia": ("clapperboard",),
 "applications-office": ("briefcase",), "applications-science": ("flask-conical",),
 "applications-system": ("settings-2","settings"), "applications-other": ("layout-grid","grid-2x2"),
 "applications-all": ("layout-grid","grid-2x2"), "preferences-other": ("sliders-horizontal",),
 "applications-engineering": ("ruler","drafting-compass"), "applications-electronics": ("cpu",),
 "applications-mathematics": ("sigma","calculator"), "applications-network": ("network",),
 "applications-audio": ("music",), "applications-video": ("video",), "applications-sound": ("music",),
 "applications-accessibility": ("accessibility","person-standing"), "preferences-desktop": ("settings",),
 "preferences-system": ("settings",), "preferences-desktop-theme": ("palette",),
 "preferences-desktop-wallpaper": ("image",), "preferences-desktop-font": ("type",),
 "preferences-desktop-locale": ("languages","globe"), "preferences-desktop-accessibility": ("accessibility","person-standing"),
 "preferences-desktop-default-applications": ("app-window",), "preferences-desktop-notification": ("bell",),
 "preferences-desktop-screensaver": ("monitor-pause","monitor"), "preferences-desktop-peripherals": ("mouse",),
 "preferences-system-time": ("clock",), "preferences-system-session": ("log-in",),
 "preferences-system-sharing": ("share-2",), "preferences-system-search": ("search",),
 "preferences-system-notifications": ("bell",), "preferences-system-windows": ("app-window",),
 "preferences-desktop-online-accounts": ("cloud","user-round"), "preferences-system-details": ("info",),
}

# Dossiers (scalable/places) : nom -> glyphe (None = dossier nu)
FOLDERS = {
 "folder": (None, False), "folder-open": (None, True),
 "folder-documents": (("file-text",), False), "folder-download": (("download",), False),
 "folder-music": (("music",), False), "folder-pictures": (("image",), False),
 "folder-videos": (("clapperboard","video"), False), "folder-publicshare": (("share-2",), False),
 "folder-templates": (("layout-template","layout-panel-top"), False),
 "folder-remote": (("globe",), False), "folder-network": (("network",), False),
 "folder-favorites": (("star",), False), "folder-bookmark": (("bookmark",), False),
 "folder-recent": (("history",), False), "folder-temp": (("clock",), False),
 "folder-cloud": (("cloud",), False), "folder-development": (("code-xml","code"), False),
 "folder-games": (("gamepad-2",), False), "folder-projects": (("kanban","layers"), False),
 "folder-saved-search": (("search",), False), "folder-locked": (("lock",), False),
 "folder-activities": (("layers",), False), "folder-script": (("terminal",), False),
 "folder-git": (("git-branch",), False), "folder-github": (("github","git-branch"), False),
 "folder-code": (("code-xml","code"), False), "folder-text": (("file-text",), False),
 "folder-notes": (("notebook",), False), "folder-books": (("book-open",), False),
 "folder-backup": (("archive",), False), "folder-wine": (("wine",), False),
 "folder-steam": (("gamepad-2",), False), "folder-trash": (("trash-2",), False),
 "folder-important": (("flag",), False), "folder-mail": (("mail",), False),
 "folder-photo": (("camera",), False), "folder-image": (("image",), False),
 "folder-video": (("clapperboard","video"), False), "folder-music-symbolic": None,
 "folder-drag-accept": (("plus",), True), "folder-visiting": (("eye",), True),
 "folder-new": (("plus",), False),
 "inode-directory": (None, False),
}
FOLDERS = {k: v for k, v in FOLDERS.items() if v is not None}

# Places "tuile" : nom -> glyphe
PLACE_TILES = {
 "user-home": ("house",), "user-desktop": ("monitor",), "user-trash": ("trash-2",),
 "user-bookmarks": ("bookmark",), "user-available": ("circle-check",), "user-away": ("clock",),
 "user-busy": ("circle-minus","ban"), "user-offline": ("circle-off","circle"),
 "network-server": ("server",), "network-workgroup": ("network",), "network-wired": ("cable","ethernet-port"),
 "network-wireless": ("wifi",), "network-vpn": ("shield",), "network-transmit-receive": ("arrow-up-down",),
 "network-offline": ("wifi-off",), "network-error": ("wifi-off",), "network-idle": ("wifi",),
 "folder-remote-ftp": ("server",), "folder-remote-ssh": ("terminal",), "folder-remote-smb": ("network",),
 "folder-remote-nfs": ("network",), "folder-remote-sftp": ("server",), "folder-remote-davs": ("cloud",),
 "network-connect": ("plug",), "network-disconnect": ("unplug",), "gtk-network": ("network",),
 "network-server-symbolic-dummy": None,
 "computer": ("monitor",), "user-identity": ("user-round",), "avatar-default": ("user-round",),
 "user-info": ("user-round",), "stock_person": ("user-round",), "preferences-desktop-user": ("user-round",),
 "mail-unread": ("mail",), "mail-read": ("mail-open",), "mail-replied": ("reply",),
 "mail-forward": ("forward",), "mail-send": ("send",), "mail-attachment": ("paperclip",),
 "mail-mark-important": ("flag",), "mail-mark-junk": ("shield-alert",), "mail-message-new": ("mail-plus",),
 "dialog-information": ("info",), "dialog-warning": ("triangle-alert",), "dialog-error": ("circle-x",),
 "dialog-question": ("circle-help","circle-question-mark"), "dialog-password": ("lock-keyhole","lock"),
 "emblem-important": ("flag",), "emblem-favorite": ("star",), "emblem-default": ("circle-check",),
 "emblem-ok": ("circle-check",), "emblem-system": ("settings",), "emblem-shared": ("share-2",),
 "emblem-synchronizing": ("refresh-cw",), "emblem-readonly": ("lock",), "emblem-unreadable": ("eye-off",),
 "emblem-symbolic-link": ("link",), "emblem-documents": ("file-text",), "emblem-downloads": ("download",),
 "emblem-photos": ("image",), "emblem-music": ("music",), "emblem-videos": ("clapperboard","video"),
 "emblem-web": ("globe",), "emblem-urgent": ("circle-alert","badge-alert"), "emblem-mail": ("mail",),
 "emblem-new": ("sparkles",), "emblem-art": ("palette",), "emblem-money": ("wallet",),
 "emblem-generic": ("tag",), "emblem-desktop": ("monitor",), "emblem-development": ("code-xml","code"),
 "emblem-cloud": ("cloud",), "emblem-package": ("package",), "emblem-notes": ("notebook",),
 "emblem-locked": ("lock",), "emblem-unlocked": ("lock-open",), "emblem-default-symbolic-dummy": None,
 "weather-clear": ("sun",), "weather-clear-night": ("moon",), "weather-few-clouds": ("cloud-sun",),
 "weather-few-clouds-night": ("cloud-moon",), "weather-overcast": ("cloud",), "weather-showers": ("cloud-drizzle",),
 "weather-showers-scattered": ("cloud-drizzle",), "weather-snow": ("snowflake",), "weather-storm": ("cloud-lightning",),
 "weather-fog": ("cloud-fog",), "weather-severe-alert": ("triangle-alert",),
 "audio-volume-high": ("volume-2",), "audio-volume-medium": ("volume-1",), "audio-volume-low": ("volume",),
 "audio-volume-muted": ("volume-x",), "microphone-sensitivity-high": ("mic",), "microphone-sensitivity-muted": ("mic-off",),
 "battery-full": ("battery-full",), "battery-good": ("battery-medium",), "battery-low": ("battery-low",),
 "battery-caution": ("battery-warning",), "battery-empty": ("battery",), "battery-full-charging": ("battery-charging",),
 "battery-missing": ("battery",), "ac-adapter": ("plug-zap","plug"),
 "system-shutdown": ("power",), "system-reboot": ("rotate-cw",), "system-suspend": ("moon",),
 "system-hibernate": ("moon-star","moon"), "system-lock-screen": ("lock",), "system-log-out": ("log-out",),
 "system-switch-user": ("users",), "system-search": ("search",), "system-run": ("play",),
 "system-help": ("circle-help","circle-question-mark"), "system-users-dummy": None,
 "system-software-update": ("refresh-cw","arrow-up-circle"), "system-software-installer": ("package-plus","package"),
 "software-update-available": ("circle-arrow-up","arrow-up-circle"), "software-update-urgent": ("triangle-alert",),
 "update-high": ("circle-arrow-up",), "update-low": ("circle-arrow-up",), "update-medium": ("circle-arrow-up",),
 "view-refresh": ("refresh-cw",), "view-fullscreen": ("maximize",), "view-restore": ("minimize",),
 "view-list": ("list",), "view-grid": ("layout-grid",), "view-sort-ascending": ("arrow-up-narrow-wide",),
 "edit-find": ("search",), "edit-copy": ("copy",), "edit-cut": ("scissors",), "edit-paste": ("clipboard",),
 "edit-delete": ("trash-2",), "edit-undo": ("undo-2",), "edit-redo": ("redo-2",), "edit-clear": ("eraser",),
 "edit-select-all": ("square-dashed-mouse-pointer","box-select"), "list-add": ("plus",), "list-remove": ("minus",),
 "go-home": ("house",), "go-up": ("arrow-up",), "go-down": ("arrow-down",), "go-next": ("arrow-right",),
 "go-previous": ("arrow-left",), "go-jump": ("corner-down-right",), "go-top": ("chevrons-up",),
 "go-bottom": ("chevrons-down",), "go-first": ("chevrons-left",), "go-last": ("chevrons-right",),
 "document-new": ("file-plus",), "document-open": ("folder-open",), "document-save": ("save",),
 "document-save-as": ("save",), "document-print": ("printer",), "document-print-preview": ("scan-eye","eye"),
 "document-properties": ("file-cog","info"), "document-export": ("file-output","upload"),
 "document-import": ("file-input","download"), "document-send": ("send",), "document-revert": ("rotate-ccw",),
 "document-open-recent": ("history",), "window-close": ("x",), "window-new": ("app-window",),
 "window-maximize": ("maximize",), "window-minimize": ("minus",), "window-restore": ("minimize",),
 "media-playback-start": ("play",), "media-playback-pause": ("pause",), "media-playback-stop": ("square",),
 "media-skip-forward": ("skip-forward",), "media-skip-backward": ("skip-back",), "media-seek-forward": ("fast-forward",),
 "media-seek-backward": ("rewind",), "media-record": ("circle-dot","circle"), "media-eject": ("eject",),
 "media-playlist-repeat": ("repeat",), "media-playlist-shuffle": ("shuffle",), "media-mount": ("hard-drive-download","hard-drive"),
 "process-stop": ("octagon-x","x"), "process-working": ("loader",), "appointment-new": ("calendar-plus",),
 "appointment-soon": ("calendar-clock",), "contact-new": ("user-plus",), "bookmark-new": ("bookmark-plus",),
 "tab-new": ("plus",), "zoom-in": ("zoom-in",), "zoom-out": ("zoom-out",), "zoom-fit-best": ("scan",),
 "zoom-original": ("scan-search","search"), "format-text-bold": ("bold",), "format-text-italic": ("italic",),
 "format-text-underline": ("underline",), "format-text-strikethrough": ("strikethrough",),
 "format-justify-left": ("align-left",), "format-justify-center": ("align-center",), "format-justify-right": ("align-right",),
 "format-justify-fill": ("align-justify",), "format-indent-more": ("indent-increase",), "format-indent-less": ("indent-decrease",),
 "insert-image": ("image-plus","image"), "insert-link": ("link",), "insert-text": ("type",), "insert-object": ("shapes","box"),
 "object-rotate-left": ("rotate-ccw",), "object-rotate-right": ("rotate-cw",), "object-flip-horizontal": ("flip-horizontal",),
 "object-flip-vertical": ("flip-vertical",), "image-missing": ("image-off",), "image-loading": ("loader",),
 "camera-photo-dummy": None, "call-start": ("phone",), "call-stop": ("phone-off",), "call-missed": ("phone-missed",),
 "call-incoming": ("phone-incoming",), "call-outgoing": ("phone-outgoing",), "notification": ("bell",),
 "notification-new": ("bell-ring",), "notification-disabled": ("bell-off",), "preferences-desktop-notification-bell": ("bell",),
 "starred": ("star",), "non-starred": ("star-off","star"), "semi-starred": ("star-half",),
 "security-high": ("shield-check",), "security-medium": ("shield",), "security-low": ("shield-alert",),
 "channel-secure": ("lock",), "channel-insecure": ("lock-open",), "tag": ("tag",), "gtk-ok": ("check",),
 "gtk-cancel": ("x",), "gtk-yes": ("check",), "gtk-no": ("x",), "gtk-apply": ("check",),
 "gtk-add": ("plus",), "gtk-remove": ("minus",), "gtk-about": ("info",), "gtk-help": ("circle-help","circle-question-mark"),
 "gtk-preferences": ("settings",), "gtk-properties": ("settings-2","settings"), "gtk-refresh": ("refresh-cw",),
 "gtk-find": ("search",), "gtk-home": ("house",), "gtk-open": ("folder-open",), "gtk-save": ("save",),
 "gtk-delete": ("trash-2",), "gtk-copy": ("copy",), "gtk-paste": ("clipboard",), "gtk-cut": ("scissors",),
 "gtk-print": ("printer",), "gtk-quit": ("log-out",), "gtk-close": ("x",), "gtk-edit": ("pencil",),
 "gtk-info": ("info",), "gtk-select-all": ("box-select",), "gtk-new": ("file-plus",), "gtk-file": ("file",),
 "gtk-directory": ("folder",), "gtk-harddisk": ("hard-drive",), "gtk-cdrom": ("disc",), "gtk-execute": ("play",),
}
PLACE_TILES = {k: v for k, v in PLACE_TILES.items() if v is not None}

# Types de fichiers (scalable/mimetypes) : glyphe -> noms
MIMES = {
 L("align-left"): ["text-x-generic","text-plain","text-x-preview","text-x-readme","text-x-log","text-x-copying","text-x-authors","text-x-changelog","text-x-install","text-x-generic-template","text-x-patch","text-x-diff","text-rtf","application-rtf","text-x-tex","text-x-bibtex","text-x-lyx","text-vnd.abc","text-x-subrip","text-vtt","text-x-ssa","text-x-uri","text-uri-list","text-x-vcard","text-x-ldif","text-x-opml","application-x-subrip","text-richtext","text-enriched","application-x-trash","text-x-troff-man","text-x-gettext-translation","text-x-gettext-translation-template","text-x-po","text-x-pot","text-x-mo","text-x-qml","text-x-systemd-unit","text-x-ini","text-x-properties","text-x-conf","text-x-config","text-x-cfg","text-x-yaml","application-x-yaml","text-x-toml","text-x-nix","text-x-dockerfile","text-x-cmake","text-x-meson"],
 L("file-text"): ["application-pdf","application-x-pdf","application-postscript","application-x-postscript","application-x-dvi","image-vnd.djvu","application-x-gzpostscript","application-vnd.oasis.opendocument.text","application-vnd.oasis.opendocument.text-template","application-msword","application-vnd.ms-word","application-vnd.openxmlformats-officedocument.wordprocessingml.document","application-vnd.openxmlformats-officedocument.wordprocessingml.template","application-x-abiword","application-vnd.wordperfect","application-vnd.sun.xml.writer","x-office-document","x-office-document-template","application-x-fictionbook+xml","application-vnd.ms-xpsdocument","application-oxps","application-x-cbr","application-x-cbz","application-x-cb7","application-x-cbt","application-vnd.comicbook+zip","application-x-mobipocket-ebook","application-x-kindle-ebook","application-vnd.amazon.ebook","application-x-hwp","application-vnd.hancom.hwp"],
 L("book-open"): ["application-epub+zip","application-x-ebook","application-x-mobi8-ebook","application-x-fb2","application-x-fb2.zip","application-vnd.amazon.mobi8-ebook","application-x-azw","application-x-azw3","application-x-ibooks"],
 L("table"): ["x-office-spreadsheet","x-office-spreadsheet-template","text-csv","text-tab-separated-values","text-x-csv","application-vnd.oasis.opendocument.spreadsheet","application-vnd.oasis.opendocument.spreadsheet-template","application-vnd.ms-excel","application-vnd.ms-excel.sheet.macroenabled.12","application-vnd.openxmlformats-officedocument.spreadsheetml.sheet","application-vnd.openxmlformats-officedocument.spreadsheetml.template","application-x-gnumeric","application-vnd.sun.xml.calc","application-x-quattropro","application-x-lotus123","application-x-sylk","application-vnd.apple.numbers","application-x-numbers"],
 L("presentation"): ["x-office-presentation","x-office-presentation-template","application-vnd.oasis.opendocument.presentation","application-vnd.oasis.opendocument.presentation-template","application-vnd.ms-powerpoint","application-vnd.openxmlformats-officedocument.presentationml.presentation","application-vnd.openxmlformats-officedocument.presentationml.template","application-vnd.openxmlformats-officedocument.presentationml.slideshow","application-vnd.sun.xml.impress","application-vnd.apple.keynote","application-x-keynote","application-vnd.ms-powerpoint.presentation.macroenabled.12"],
 L("pen-tool","vector-square"): ["x-office-drawing","x-office-drawing-template","application-vnd.oasis.opendocument.graphics","application-vnd.oasis.opendocument.graphics-template","image-svg+xml","image-svg+xml-compressed","image-svg","application-illustrator","application-postscript-eps","image-x-eps","image-x-eps-dummy","application-vnd.sun.xml.draw","application-x-inkscape-svg","image-x-svgz","application-vnd.visio","application-vnd.ms-visio.drawing","application-x-dia-diagram","application-x-kivio","application-x-karbon","application-x-xfig","image-x-xfig","image-x-wmf","image-x-emf","image-emf","image-wmf","application-vnd.corel-draw","application-x-cdr"],
 L("image"): ["image-x-generic","image-png","image-jpeg","image-jpg","image-gif","image-webp","image-bmp","image-x-bmp","image-tiff","image-x-tiff","image-avif","image-heic","image-heif","image-jxl","image-jp2","image-x-icon","image-vnd.microsoft.icon","image-x-ico","image-x-icns","image-x-xpixmap","image-x-xbitmap","image-x-portable-pixmap","image-x-portable-graymap","image-x-portable-bitmap","image-x-portable-anymap","image-x-pcx","image-x-tga","image-x-targa","image-x-dds","image-x-exr","image-x-hdr","image-vnd.radiance","image-x-psd","image-vnd.adobe.photoshop","application-x-krita","image-x-xcf","image-x-gimp-gbr","image-x-gimp-pat","image-x-gimp-gih","application-x-gimp-brush","application-x-gimp-pattern","application-x-gimp-palette","image-x-kra","image-openraster","image-x-xcursor","image-x-sun-raster","image-x-sgi","image-x-pict","image-x-quicktime","image-x-skencil","image-x-canon-cr2","image-x-canon-crw","image-x-nikon-nef","image-x-sony-arw","image-x-adobe-dng","image-x-raw","image-x-dcraw","image-x-fuji-raf","image-x-olympus-orf","image-x-panasonic-raw","image-x-pentax-pef","image-x-samsung-srw","image-x-sigma-x3f","image-x-sony-sr2","image-x-sony-srf","image-x-minolta-mrw","image-x-kodak-dcr","image-x-kodak-kdc","image-x-epson-erf","image-x-hasselblad-3fr","image-x-leaf-mos","image-x-mamiya-mef","image-x-phaseone-cap","image-x-pentax-pef","image-x-fits","image-fits","image-x-apple-pdf","image-apng","image-x-apng","image-x-animated-png","image-x-flif","image-x-jng","image-x-mng","image-x-xpm","image-x-win-bitmap","image-x-ms-bmp","image-x-cmu-raster","image-x-macpaint","image-x-photo-cd","image-x-pixmap","image-x-portable-floatmap","image-x-rgb","image-x-tga-dummy","image-vnd.zbrush.pcx","image-vnd.wap.wbmp","image-vnd.dwg","image-vnd.dxf","image-x-ilbm","image-x-lwo","image-x-lws","image-x-msod","image-x-niff","image-x-pcd","image-x-pict-dummy","image-x-xwindowdump","image-x-compressed-xcf","application-x-xcf","application-x-xcf-gz","application-x-xcf-bz2","application-x-photoshop","image-x-sony-dummy"],
 L("music"): ["audio-x-generic","audio-mpeg","audio-mp3","audio-mp4","audio-x-mp3","audio-x-mpeg","audio-x-wav","audio-wav","audio-flac","audio-x-flac","audio-ogg","audio-x-vorbis+ogg","audio-vorbis","audio-opus","audio-x-opus+ogg","audio-aac","audio-x-aac","audio-x-ms-wma","audio-x-ms-wax","audio-x-aiff","audio-aiff","audio-midi","audio-x-midi","audio-x-matroska","audio-webm","audio-x-m4a","audio-m4a","audio-x-speex","audio-x-speex+ogg","audio-x-ape","audio-x-wavpack","audio-x-musepack","audio-x-tta","audio-x-adpcm","audio-x-it","audio-x-mod","audio-x-s3m","audio-x-xm","audio-x-gsm","audio-x-pn-realaudio","audio-vnd.rn-realaudio","audio-x-realaudio","audio-x-scpls","audio-x-mpegurl","audio-mpegurl","audio-x-ms-asx","audio-x-iriver-pla","audio-prs.sid","audio-x-sid","audio-x-psf","audio-x-psflib","audio-x-minipsf","audio-x-psf-dummy","audio-x-caf","audio-x-amr","audio-amr","audio-amr-wb","audio-x-ac3","audio-ac3","audio-x-eac3","audio-x-dts","audio-x-dsf","audio-x-dff","audio-basic","audio-x-au","audio-x-voc","audio-x-w64","audio-x-ircam","audio-x-paf","audio-x-pvf","audio-x-sds","audio-x-sd2","audio-x-svx","audio-x-htk","audio-x-avr","audio-x-mat4","audio-x-mat5","audio-x-nist","audio-x-rf64","audio-x-wve","audio-x-xi","audio-x-mpegurl-dummy","audio-x-vorbis","audio-x-oggflac","audio-x-flac+ogg","audio-x-ogg","audio-x-opus","audio-x-matroska-dummy","application-ogg","application-x-ogg","application-x-flac","application-x-cue","application-x-musicbrainz-dummy","application-x-sf2","audio-x-sf2","audio-x-soundfont","application-x-ardour","application-x-audacity-project","application-x-lmms-project","application-x-hydrogen","application-x-rosegarden","application-x-musescore","application-x-musescore+xml","application-vnd.recordare.musicxml","application-vnd.recordare.musicxml+xml","application-x-lilypond","text-x-lilypond","application-x-abc","application-x-tuxguitar","application-x-guitar-pro","application-x-gtp","application-x-ptb","application-x-mscx","application-x-mscz","audio-x-mod-dummy"],
 L("clapperboard","video"): ["video-x-generic","video-mp4","video-mpeg","video-x-mpeg","video-x-matroska","video-webm","video-ogg","video-x-ogg","video-quicktime","video-x-msvideo","video-avi","video-x-ms-wmv","video-x-ms-asf","video-x-flv","video-x-theora+ogg","video-3gpp","video-3gpp2","video-vnd.rn-realvideo","video-x-ogm+ogg","video-x-sgi-movie","video-x-m4v","video-x-mpeg2","video-mp2t","video-mp2t-dummy","video-vnd.mpegurl","video-x-ms-wvx","video-x-ms-wm","video-x-nsv","video-x-anim","video-x-fli","video-x-flic","video-x-flv-dummy","video-x-dv","video-x-mng","video-dv","video-x-vob","video-dvd","video-x-ogm","video-x-mjpeg","video-h264","video-h265","video-vp8","video-vp9","video-av1","video-x-xvid","video-x-divx","video-x-mkv","video-x-wmv","video-x-rm","video-x-rmvb","video-x-swf","application-x-shockwave-flash","application-vnd.rn-realmedia","application-vnd.rn-realmedia-vbr","application-x-extension-mp4","application-x-quicktime-media-link","application-x-flash-video","application-mxf","application-x-kdenlive","application-x-shotcut","application-x-openshot","application-x-pitivi","application-x-mlt-playlist","application-vnd.kde.kdenlive","application-x-flowblade","application-x-olive","application-x-blender-video","application-x-davinci"],
 L("archive"): ["package-x-generic","application-zip","application-x-zip","application-x-zip-compressed","application-x-tar","application-x-compressed-tar","application-x-bzip-compressed-tar","application-x-xz-compressed-tar","application-x-lzma-compressed-tar","application-x-zstd-compressed-tar","application-x-lz4-compressed-tar","application-x-lzip-compressed-tar","application-x-lzop-compressed-tar","application-x-tarz","application-gzip","application-x-gzip","application-x-bzip","application-x-bzip2","application-x-xz","application-x-lzma","application-zstd","application-x-zstd","application-x-lz4","application-x-lzip","application-x-lzop","application-x-compress","application-x-7z-compressed","application-x-rar","application-vnd.rar","application-x-rar-compressed","application-x-archive","application-x-cpio","application-x-cpio-compressed","application-x-ar","application-x-arj","application-x-lha","application-x-lzh","application-x-lzh-compressed","application-x-ace","application-x-alz","application-x-zoo","application-x-stuffit","application-x-sit","application-x-sea","application-x-cab","application-vnd.ms-cab-compressed","application-x-gtar","application-x-ustar","application-x-shar","application-x-war","application-x-ear","application-x-jar","application-java-archive","application-x-java-archive","application-x-rpm","application-x-deb","application-vnd.debian.binary-package","application-x-debian-package","application-x-redhat-package-manager","application-x-source-rpm","application-x-pak","application-x-wad","application-x-squashfs","application-vnd.squashfs","application-x-cd-image-dummy","application-x-lrzip","application-x-lrzip-compressed-tar","application-x-lz","application-x-zpaq","application-x-bcpio","application-x-cbr-dummy","application-x-archive-dummy","application-x-gzip-dummy","application-x-zip-dummy","application-x-appimage-dummy","application-x-flatpak-dummy","application-x-xar","application-x-xzpdf","application-x-zstd-compressed-tar-dummy","application-x-tzo","application-x-tzst","application-x-txz","application-x-tbz","application-x-tbz2","application-x-tgz","application-x-tlz","application-x-tlz4","application-x-tarz-dummy","application-x-7zip","application-x-7zip-compressed","application-7zip","application-x-winzip","application-x-winrar","application-x-bz2","application-x-gz","application-x-xz-dummy","application-x-bzip-dummy","application-x-lzma-dummy","application-x-compressed","application-x-gzip-compressed","application-x-tar-compressed"],
 L("package"): ["application-vnd.flatpak","application-vnd.flatpak.ref","application-vnd.flatpak.repo","application-x-appimage","application-vnd.appimage","application-x-iso9660-appimage","application-x-snap","application-vnd.snap","application-x-nix","application-x-nar","application-x-pacman","application-x-pkg","application-x-pkgbuild","application-x-xbps","application-x-apk","application-vnd.android.package-archive","application-x-msi","application-x-ms-installer","application-x-installer","application-x-msdownload-dummy","application-x-gnome-saved-search-dummy","application-x-dpkg","application-x-gem","application-x-cargo-crate","application-x-wheel","application-x-python-wheel","application-x-npm","application-x-tgz-npm","application-x-crate","application-x-vsix","application-vsix","application-x-xpi","application-x-chrome-extension","application-x-crx","application-x-gnome-shell-extension","application-x-oxt","application-x-addon","application-x-extension","application-x-opera-extension","application-x-nex","application-x-safariextz","application-x-package"],
 L("disc"): ["application-x-cd-image","application-x-iso","application-x-iso9660-image","application-x-raw-disk-image","application-x-raw-disk-image-xz-compressed","application-x-cue","application-x-toc","application-x-bin","application-x-nrg","application-x-mds","application-x-ccd","application-x-img","application-vnd.efi.iso","application-vnd.efi.img","application-x-qemu-disk","application-x-qcow2-image","application-x-vmdk","application-x-vdi","application-x-vhd","application-x-vhdx","application-x-virtualbox-vdi","application-x-virtualbox-vmdk","application-x-virtualbox-vhd","application-x-virtualbox-hdd","application-x-virtualbox-ova","application-x-virtualbox-ovf","application-x-vmware-vmdk","application-x-vmware-vmx","application-x-parallels-hdd","application-x-disk-image","application-x-apple-diskimage","application-x-dmg","application-x-ms-wim","application-x-wim","application-x-udf-image","application-x-gamecube-iso-image","application-x-wii-iso-image","application-x-wii-rom","application-x-gamecube-rom","application-x-wbfs","application-x-ciso","application-x-gdi","application-x-chd","application-x-3ds-rom","application-x-nintendo-ds-rom","application-x-nintendo-switch-rom","application-x-n64-rom","application-x-nes-rom","application-x-snes-rom","application-x-gameboy-rom","application-x-gba-rom","application-x-genesis-rom","application-x-sms-rom","application-x-gg-rom","application-x-psx-rom","application-x-ps2-rom","application-x-psp-rom","application-x-saturn-rom","application-x-dreamcast-rom","application-x-atari-rom","application-x-neo-geo-rom","application-x-pc-engine-rom","application-x-amiga-rom","application-x-c64-rom","application-x-zx-rom","application-x-msx-rom","application-x-arcade-rom","application-x-mame-rom","application-x-n64-rom-dummy","application-x-ps3-rom","application-x-xbox-rom","application-x-xbox360-rom","application-x-wiiu-rom","application-x-vita-rom"],
 L("terminal"): ["application-x-shellscript","text-x-script","text-x-shellscript","text-x-sh","text-x-bash","text-x-zsh","text-x-fish","text-x-csh","text-x-ksh","text-x-batch","text-x-bat","application-x-bat","application-x-msdos-program","application-x-ms-dos-executable-dummy","text-x-powershell","application-x-powershell","text-x-ps1","application-x-sh","application-x-csh","application-x-ksh","application-x-zsh","application-x-bash","application-x-fish","application-x-perl-dummy","text-x-awk","application-x-awk","application-x-tcl","text-x-tcl","text-x-expect","application-x-expect","text-x-applescript","application-x-applescript","text-x-vbscript","application-x-vbscript","text-x-lua-dummy","text-x-makefile","text-x-make","application-x-makefile","text-x-automake","text-x-autoconf","text-x-ninja","application-x-ninja","text-x-justfile","text-x-taskfile","text-x-rakefile","text-x-gradle","text-x-groovy-dummy","text-x-meson-dummy","text-x-shell","application-x-shell","application-x-shellscript-dummy","text-x-sh-dummy"],
 L("cog","settings"): ["application-x-sharedlib","application-x-object","application-x-core","application-x-coredump","application-x-executable-dummy","application-x-pie-executable","application-x-ms-dos-executable","application-vnd.microsoft.portable-executable","application-x-msdownload","application-x-dosexec","application-x-wine-extension-ini","application-x-ms-shortcut","application-x-ms-pdb","application-x-pdb","application-x-ms-dll","application-x-dll","application-x-sys","application-x-ms-sys","application-x-so","application-x-elf","application-x-mach-binary","application-x-mach-o","application-x-dylib","application-x-java-class","application-java-vm","application-x-java-applet","application-x-java-jnlp-file","application-x-kde-service","application-x-gnome-saved-search","application-x-ms-ne-executable","application-x-ms-win-executable","application-x-ms-wizard","application-x-ms-wmz","application-x-ms-wmd","application-x-msi-dummy","application-x-wine-extension-msp","application-x-wine-extension-ini-dummy","application-x-wine-extension","application-x-desktop-dummy","application-x-systemd-dummy","application-x-systemd","application-x-systemd-unit","text-x-systemd","application-x-udev","application-x-modprobe","application-x-kernel-module","application-x-ko","application-x-kernel","application-x-initrd","application-x-initramfs","application-x-vmlinuz","application-x-bzimage","application-x-efi","application-x-efi-executable","application-x-uefi","application-x-bios","application-x-firmware","application-x-rom","application-x-flash-rom","application-x-bin-dummy","application-x-hex","application-x-ihex","application-x-srec","application-x-s19","application-x-elf-core","application-x-dump","application-x-crash","application-x-core-dump"],
 L("code-xml","code"): ["text-x-source","text-x-python","text-x-python3","application-x-python-bytecode","text-x-csrc","text-x-chdr","text-x-c++src","text-x-c++hdr","text-x-c","text-x-c++","text-x-objcsrc","text-x-objc++src","text-x-java","text-x-java-source","text-x-kotlin","text-x-scala","text-x-groovy","text-x-rust","text-x-rustsrc","text-rust","text-x-go","text-x-golang","text-x-swift","text-x-csharp","text-x-fsharp","text-x-vb","text-x-vbnet","text-x-javascript","application-javascript","application-x-javascript","text-javascript","text-x-typescript","text-typescript","application-typescript","text-jsx","text-tsx","text-x-jsx","text-x-tsx","application-json","text-json","application-x-json","application-ld+json","application-json5","text-json5","application-x-ndjson","application-jsonlines","text-x-ruby","application-x-ruby","text-x-php","application-x-php","application-x-httpd-php","text-x-perl","application-x-perl","text-x-lua","application-x-lua","text-x-r","text-x-rsrc","text-x-julia","text-x-haskell","text-x-lhs","text-x-ocaml","text-x-elixir","text-x-erlang","text-x-clojure","text-x-lisp","text-x-scheme","text-x-emacs-lisp","text-x-elisp","text-x-dart","text-x-zig","text-x-nim","text-x-d","text-x-pascal","text-x-fortran","text-x-cobol","text-x-ada","text-x-asm","text-x-assembly","text-x-nasm","text-x-vala","text-x-vapi","text-x-genie","text-x-sql","application-sql","text-x-glsl","text-x-hlsl","text-x-wgsl","text-x-cuda","text-x-opencl","text-x-verilog","text-x-vhdl","text-x-systemverilog","text-x-tcl-dummy","text-x-matlab","text-x-octave","text-x-sage","text-x-stata","text-x-sas","text-x-spss","text-html","application-xhtml+xml","text-xml","application-xml","application-x-xml","text-css","text-x-scss","text-x-sass","text-x-less","text-x-styl","text-x-stylus","text-x-svelte","text-x-vue","text-x-astro","text-x-handlebars","text-x-mustache","text-x-jinja","text-x-twig","text-x-erb","text-x-ejs","text-x-pug","text-x-haml","text-x-slim","text-x-markdown-dummy","text-x-graphql","application-graphql","text-x-protobuf","text-x-proto","text-x-thrift","text-x-capnp","text-x-flatbuffers","text-x-avro","application-x-yaml-dummy","text-x-hcl","text-x-terraform","text-x-nix-dummy","text-x-puppet","text-x-ansible","text-x-bazel","text-x-starlark","text-x-cmake-dummy","text-x-qmake","text-x-pro","text-x-qml-dummy","text-x-ui","application-x-gtk-builder","application-x-glade","application-x-designer","application-x-qt-ui","application-x-qt-resource","application-x-qt-project","application-x-qt-translation","application-x-linguist","text-x-gdscript","text-x-godot-resource","text-x-godot-scene","application-x-godot-project","application-x-unity-scene","application-x-unity-prefab","application-x-unity-asset","application-x-unreal-asset","application-x-blueprint","application-x-wasm","application-wasm","text-x-wat","text-x-wast","application-x-webassembly","application-x-ipynb+json","application-x-ipynb","application-x-jupyter-notebook","text-x-sage-dummy","text-x-rmarkdown","text-x-quarto","text-x-org","text-x-latex","text-x-tex-dummy","text-x-diff-dummy","application-x-m4","text-x-m4","text-x-autotools","application-x-gettext","text-x-po-dummy","application-x-awk-dummy","application-x-sed","text-x-sed","text-x-regex","text-x-ebnf","text-x-bnf","text-x-yacc","text-x-lex","text-x-antlr","text-x-peg"],
 L("hash"): ["text-markdown","text-x-markdown","text-x-md","text-x-rst","text-x-restructuredtext","text-x-asciidoc","text-x-textile","text-x-wiki","text-x-creole","text-x-org-mode","text-x-mdx","text-x-markdown-extra","text-x-commonmark","text-x-gfm"],
 L("database"): ["application-x-sqlite3","application-vnd.sqlite3","application-x-sqlite2","application-x-sqlite","application-vnd.sqlite","application-x-db","application-x-dbf","application-x-berkeley-db","application-x-lmdb","application-x-leveldb","application-x-rocksdb","application-x-mdb","application-x-msaccess","application-vnd.ms-access","application-vnd.oasis.opendocument.database","application-vnd.oasis.opendocument.base","application-vnd.sun.xml.base","application-x-kexi","application-x-kexiproject-sqlite3","application-x-kexiproject-shortcut","application-x-kexi-connectiondata","application-x-kexi-dummy","application-x-firebird","application-x-gdb","application-x-fdb","application-x-ibd","application-x-frm","application-x-myd","application-x-myi","application-x-sqlitedb","application-x-sql-dump","application-x-pgdump","application-x-mysqldump","text-x-sql-dump","application-x-redis","application-x-rdb","application-x-mongodb","application-x-bson","application-x-parquet","application-vnd.apache.parquet","application-x-orc","application-x-avro","application-x-hdf","application-x-hdf5","application-x-netcdf","application-x-feather","application-x-arrow","application-vnd.apache.arrow.file","application-x-duckdb","application-vnd.duckdb","application-x-dbm","application-x-gdbm","application-x-tdb","application-x-kyoto","application-x-bdb"],
 L("type"): ["font-x-generic","application-x-font-ttf","application-x-font-otf","application-x-font-woff","application-x-font-woff2","application-font-woff","application-font-woff2","application-font-sfnt","application-vnd.ms-fontobject","application-x-font-type1","application-x-font-pcf","application-x-font-bdf","application-x-font-snf","application-x-font-speedo","application-x-font-linux-psf","application-x-font-ttc","application-x-font-opentype","application-x-font-truetype","application-x-font-eot","application-x-font-afm","application-x-font-pfa","application-x-font-pfb","application-x-font-gf","application-x-font-pk","application-x-font-dvi","application-x-font-vfont","application-x-font-type1-dummy","font-ttf","font-otf","font-woff","font-woff2","font-sfnt","font-collection","font-ttc","font-otc","font-eot","font-pfb","font-pfa","font-bdf","font-pcf","font-psf","font-fon","font-fnt","font-ps1","font-t1","application-x-ttf","application-x-otf","application-x-woff","application-x-woff2","application-x-eot","application-x-pfb","application-x-pfa","application-x-bdf","application-x-pcf","application-x-psf","application-x-fon","application-x-fnt","application-x-ps1","application-x-t1","application-x-font","application-x-fonts","application-x-font-generic","application-x-truetype-font","application-x-opentype-font","application-x-woff-font","application-x-woff2-font","application-x-sfnt-font","application-x-type1-font"],
 L("magnet","share-2"): ["application-x-bittorrent","application-x-torrent","application-x-bittorrent-dummy","x-scheme-handler-magnet","application-x-magnet","application-x-metalink","application-metalink+xml","application-metalink4+xml","application-x-meta4","application-x-metalink4","application-x-aria2","application-x-aria2-dummy","application-x-emule","application-x-ed2k","x-scheme-handler-ed2k","application-x-nzb","application-x-nzb-dummy","application-x-usenet","application-x-edonkey","application-x-dc","x-scheme-handler-dchub","application-x-dcc","application-x-soulseek","x-scheme-handler-slsk","application-x-gnutella","application-x-limewire","application-x-kazaa","application-x-bearshare","application-x-shareaza"],
 L("contact","book-user","users"): ["x-office-address-book","text-vcard","text-x-vcard-dummy","application-vnd.ms-outlook-contact","application-x-contact","application-x-addressbook","text-directory","text-x-vcard-contacts","application-vnd.kde.contact","application-x-vcf","text-vcf","text-x-vcf","application-vcard","application-x-vcard","application-vnd.kde.kaddressbook","application-vnd.gnome.contacts","application-x-evolution-contact","application-x-gnome-contact","application-x-thunderbird-contact","application-x-ldif-dummy","application-x-ldif","text-x-ldif-dummy","text-ldif"],
 L("calendar"): ["x-office-calendar","text-calendar","text-x-calendar","text-x-vcalendar","text-x-ical","application-ics","application-x-ics","application-x-icalendar","application-x-vcalendar","application-vnd.kde.korganizer","application-vnd.gnome.calendar","application-x-evolution-calendar","application-x-gnome-calendar","application-x-thunderbird-calendar","application-x-ical","application-x-ical-dummy","text-ics","text-x-ics","application-ical","application-x-ical-calendar","application-x-calendar","application-calendar","application-calendar+json","application-calendar+xml","application-x-todo","text-x-todo","text-x-todotxt","application-x-taskwarrior","application-x-taskjuggler","application-x-planner","application-x-gnome-planner","application-vnd.kde.calligraplan","application-x-kplato","application-x-projectlibre","application-vnd.ms-project","application-x-ms-project","application-x-mpp","application-x-mpx"],
 L("mail"): ["message-rfc822","message-x-rfc822","message-news","message-partial","message-external-body","application-mbox","application-x-mbox","application-vnd.ms-outlook","application-x-msg","application-x-pst","application-x-ost","application-x-eml","text-x-eml","application-x-emlx","application-x-maildir","application-x-mailbox","application-x-mailarchive","application-x-mailfolder","application-x-evolution-mail","application-x-thunderbird-mail","application-x-kmail","application-x-claws-mail","application-x-sylpheed","application-x-mutt","application-x-mh","application-x-mmdf","application-x-tnef","application-ms-tnef","application-vnd.ms-tnef","application-x-ms-tnef","application-x-tnef-dummy","text-x-mail","text-x-mbox","text-x-message","text-x-eml-dummy","x-scheme-handler-mailto","application-x-mailto","application-x-mailto-dummy"],
 L("globe"): ["text-html-dummy","application-x-mht","application-x-mhtml","message-rfc822-web","application-x-webarchive","application-x-warc","application-warc","application-x-har","application-json-har","application-x-url","application-x-mswinurl","application-x-desktop-url","application-x-xbel","application-xbel","application-x-bookmark","application-x-bookmarks","application-x-netscape-bookmarks","text-x-url","text-x-netscape-bookmarks","text-x-bookmark","text-x-bookmarks","application-rss+xml","application-atom+xml","application-x-opml","text-x-opml-dummy","application-x-feed","application-x-feeds","application-x-rss","application-x-atom","application-x-subscription","x-scheme-handler-http","x-scheme-handler-https","x-scheme-handler-ftp","x-scheme-handler-file","x-scheme-handler-about","x-scheme-handler-unknown","x-scheme-handler-webcal","x-scheme-handler-tel","x-scheme-handler-sms","x-scheme-handler-irc","x-scheme-handler-ircs","x-scheme-handler-xmpp","x-scheme-handler-matrix","x-scheme-handler-mailto"],
 L("file"): ["application-octet-stream","application-x-zerosize","unknown","application-x-generic","application-x-unknown","application-x-binary","application-x-data","application-x-raw","application-x-blob","application-x-dump-dummy","empty","inode-x-generic","inode-blockdevice","inode-chardevice","inode-fifo","inode-socket","inode-symlink","inode-mount-point","inode-x-empty","application-x-empty","application-x-null","application-x-none","application-x-noname","application-x-untitled","application-x-nameless","application-x-temp","application-x-tmp","application-x-backup","application-x-bak","application-x-old","application-x-orig","application-x-rej","application-x-swp","application-x-swap","application-x-lock","application-x-lockfile","application-x-pid","application-x-pidfile","application-x-socket","application-x-sock","application-x-fifo","application-x-pipe","application-x-named-pipe","application-x-device","application-x-dev","application-x-blockdev","application-x-chardev","application-x-symlink","application-x-link","application-x-shortcut","application-x-alias","application-x-junction","application-x-reparse","application-x-mount","application-x-mountpoint","application-x-volume","application-x-partition","application-x-filesystem","application-x-fs","application-x-fuse","application-x-overlay","application-x-bind","application-x-tmpfs","application-x-ramfs","application-x-devtmpfs","application-x-sysfs","application-x-procfs","application-x-debugfs","application-x-securityfs","application-x-cgroup","application-x-cgroup2","application-x-pstore","application-x-bpf","application-x-configfs","application-x-fusectl","application-x-hugetlbfs","application-x-mqueue","application-x-tracefs","application-x-efivarfs","application-x-binfmt","application-x-nsfs","application-x-autofs","application-x-rpc-pipefs","application-x-nfsd","application-x-selinuxfs","application-x-smackfs","application-x-apparmorfs"],
 L("box"): ["model-stl","model-obj","model-gltf+json","model-gltf-binary","model-x-fbx","model-x-3ds","model-vrml","model-x3d+xml","model-x3d+binary","model-x3d+vrml","model-3mf","model-step","model-iges","model-vnd.collada+xml","model-vnd.usdz+zip","model-x-ply","model-x-off","model-x-wrl","application-x-blender","application-x-blend","application-x-blender-dummy","application-x-freecad","application-x-fcstd","application-vnd.freecad","application-x-openscad","application-x-scad","application-x-sketchup","application-x-skp","application-x-3dsmax","application-x-max","application-x-maya","application-x-ma","application-x-mb","application-x-cinema4d","application-x-c4d","application-x-houdini","application-x-hip","application-x-zbrush","application-x-ztl","application-x-substance","application-x-sbs","application-x-spp","application-x-unity","application-x-unitypackage","application-x-unreal","application-x-uasset","application-x-umap","application-x-godot","application-x-tscn","application-x-tres","application-x-gdscript","application-x-dwg","application-x-dxf","application-acad","application-dxf","application-x-autocad","application-x-dwf","application-x-dgn","application-x-ifc","application-x-step","application-x-iges","application-x-stp","application-x-igs","application-x-brep","application-x-brp","application-x-iv","application-x-vrml","application-x-x3d","application-x-collada","application-x-dae","application-x-fbx","application-x-obj","application-x-gltf","application-x-glb","application-x-ply","application-x-stl","application-x-off","application-x-3mf","application-x-amf","application-x-gcode","text-x-gcode","application-x-gcode","application-x-ngc","application-x-nc","application-x-tap","application-x-cnc","application-x-cam","application-x-stl-dummy"],
}


EXTRA_GENERIC = {
 L("gamepad-2"): ["valheim","terraria","stardew-valley","hearthstone","portal-2","dont-starve","dont-starve-together","factorio","rimworld",
   "subnautica","doom","gmod","hedgewars","teeworlds","ddnet","alienarena","crystal-picnic","oxygen-not-included","hyper-light-drifter",
   "hyperbolica","splitgate","supreme-commander-forged-alliance","chess","four-in-a-row","hitori","gnome-2048","gnome-glines","gnome-tali","gbrainy",
   "techmino","org.vinegarhq.sober","hu.kramo.Cartridges","gdlauncher","multimc","ankama-launcher","org.polymc.PolyMC","r2modman","playonlinux"],
 L("joystick","gamepad-2"): ["dolphin-emu","yuzu","rpcs3","ppsspp","melonDS","xemu","shadps4","redream","dosbox","dosbox-staging","atari800",
   "hatari","mednaffe","emulationstation","fs-uae-arcade","fs-uae-launcher","fuse-emulator","pcsx-icon","caprice32","anbox","genymotion","genymotion-player"],
 L("package"): ["gdebi","software-properties","bee-package-manager","spark-store","spark-store-submitter","AppImageLauncher","appimagekit-balena-etcher-electron","flatpak-discover","flatpak-software","muondiscover","aptana","jockey","apport","ubiquity","ubiquity-kde","live-installer","calamares","org.fedoraproject.AnacondaInstaller","system-os-install"],
 L("shield-check","shield"): ["windscribe","riseup-vpn","qopenvpn","clash-verge","preferences-system-network-vpn","autofirma","com.yubico.yubioath","gnome-twofactorauth","com.github.paolostivanin.OTPClient","enteauth","passwordsafe","keyring-manager","stoken-gui","truecrypt","gcr-key","gcr-key-pair","org.kde.kwatchgnupg","kleopatra","gnupg"],
 L("cpu"): ["psensor","hwinfo","cpuinfo","hwloc","kdiskmark","goverlay","pcbnew","pcbnew-nightly","eeschema","eeschema-nightly","gerbview","gerbview-nightly","bitmap2component","pcbcalculator","pcbcalculator-nightly","openrgb","solaar","org.freedesktop.Piper","noisetorch","adriconf"],
 L("audio-waveform","music"): ["mixxx","hydrogen","qjackctl","qsynth","carla","carla-control","cadence","guitarix","lingot","lingot-icon","meterbridge","qjadeo","sc_ide","cockos-reaper","ableton","tenacity","ocenaudio","kwave","soundkonverter","sound-juicer","rubyripper","easytag","kid3","puddletag","picard","exfalso","mudita24","equaliser","musescore"],
 L("music"): ["mpd","goodvibes","pithos","tauonmb","fooyin","minitube","smtube","web-tidal","qqmusic","netease-cloud-music","lx-music-desktop","com.github.neithern.g4music","com.github.louis77.tuner","babe","cider","podcast","podcast-amarok","gpodder","playmymusic","google-music","media-player-banshee","nicotine-plus","amule","frostwire"],
 L("headphones"): ["spotube","deezer-web","web-lounge"],
 L("download"): ["ktorrent","tixati","persepolis","motrix","xdman","uget-icon","jdownloader","freedownloadmanager","gabutdm","kget","bittorrent-sync","lftp","youtube-dl","4kvideodownloader","popcorntime","fluid"],
 L("notebook-pen","file-pen"): ["ghostwriter","focuswriter","retext","cutemarked","notable","marker","uberwriter","words","boostnote","textpieces","cherrytree","tomboy","nota","wiznote","com.toolstack.Folio","buho","basket","xournal","texstudio","kile","poedit","gtranslator","org.gnome.Gtranslator","lyx"],
 L("code-xml","code"): ["glade","anjuta","qtcreator","qtdesigner","devhelp","eclipse-cdt","fleet","ipython","ipython-notebook","grapesjs","sage-notebook","golang-dev","io.elementary.code","org.gnome.dspy","tinkerwell","regextester","sequeler","gda-browser-5.0","oracle-sqldeveloper","staruml","dia","meld","qgit","smartgit","org.gtk.gtk4.NodeEditor","org.gtk.PrintEditor4","kompare","kdiff3"],
 L("calendar"): ["ms-calendar","evolution-tasks","gnome-todo","go-for-it","com.github.dahenson.agenda","kshutdown"],
 L("circle-play","play"): ["cider-music","bomi","vidcutter","videotrimmer","mkvmerge","subtitlecomposer","gnome-subtitles","aegisub","olive-editor","screen-recorder","screenrecorder","qtav","xawtv","vocal","hotspot"],
 L("scan-search","radar"): ["nmap_icon","ipscan","burp","gns3","org.gnome.Connections","virt-viewer","tigervnc","remote-desktop","securecrt","securefx","synergy","barrier","sunlogin_client","sunshine","anydesk-dummy"],
 L("terminal-square","terminal"): ["putty","cool-retro-term","terminix","tabby","alacritty-simple","xterm-color","gksu-root-terminal","utilities-x-terminal","around"],
 L("sliders-horizontal","settings"): ["dconf-editor","gnome-tweak-tool","kvantum","ccsm","grub-customizer","menu-editor","wmtweaks","theme-config","variety","variety-slideshow","org.gnome.Tecla","preferences-color"],
 L("book-open"): ["koodo-reader","sigil","gnome-books","gnome-documents","cozy","cozydrive","calibre-gui-dummy","foxit-reader","acroread","qpdfview","org.kde.qrca","lagrange"],
 L("cloud"): ["pcloud","insync","nutstore","baidunetdisk","nylas","fastmail","gmail-offline","goa-account-google","goa-account-owncloud","online-account","ubuntuone"],
 L("globe"): ["slimjet","org.midori_browser.Midori","qupzilla","yandex-browser","lagrange","liferea","akregator","quiterss","newsflash","fluent-reader","internet-news-reader","web-facebook","web-twitter","web-yahoo","whalebird","tokodon","dev.geopjr.Tuba","com.github.bleakgrey.tootle","cawbird","corebird"],
}
for _g, _names in EXTRA_GENERIC.items():
    GENERIC_APPS.setdefault(_g, []).extend(_names)

# ================================================================== partie 2 : filtrage par les noms de Tela
def names_in(*dirs):
    out = set()
    for d in dirs:
        p = f"{TELA}/{d}"
        if os.path.isdir(p):
            for f in os.listdir(p):
                if f.endswith(".svg"):
                    out.add(f[:-4])
    return out

COLORS = ("blue-","brown-","green-","grey-","orange-","pink-","purple-","red-","teal-","violet-","yellow-","black-","bluegrey-","cyan-","deeporange-","indigo-","lightblue-","lime-","magenta-","manjaro-","nord-","ubuntu-","default-","white-","paleorange-","sakura-","dracula-","gruvbox-","kanagawa-")
strip_color = lambda s: s
tela_places = {n for n in names_in("src/scalable/places", "links/scalable/places") if not n.startswith(COLORS)}
tela_mimes = names_in("src/scalable/mimetypes", "links/scalable/mimetypes")
tela_devices = names_in("src/scalable/devices", "links/scalable/devices")

# FDO standard names we always keep even when Tela lacks them
FDO_KEEP = set(CATEGORIES) | {"start-here", "distributor-logo", "application-default-icon", "application-x-executable",
    "utilities-terminal", "system-file-manager", "accessories-calculator", "accessories-text-editor",
    "preferences-system", "web-browser", "internet-mail", "office-calendar", "folder", "folder-open",
    "inode-directory", "text-x-generic", "image-x-generic", "audio-x-generic", "video-x-generic",
    "package-x-generic", "application-octet-stream", "x-office-document", "x-office-spreadsheet",
    "x-office-presentation", "user-home", "user-desktop", "user-trash", "user-trash-full", "user-bookmarks"}

DEVICES = {
 "drive-harddisk": ("hard-drive",), "drive-harddisk-solidstate": ("hard-drive",), "drive-harddisk-usb": ("usb","hard-drive"),
 "drive-harddisk-ieee1394": ("hard-drive",), "drive-multidisk": ("database","server"), "drive-optical": ("disc",),
 "drive-removable-media": ("usb",), "drive-removable-media-usb": ("usb",), "media-optical": ("disc",),
 "media-flash": ("sd-card","memory-stick"), "media-flash-sd-mmc": ("sd-card","memory-stick"), "media-flash-memory-stick": ("usb",),
 "media-memory": ("memory-stick",), "media-floppy": ("save",), "media-tape": ("tape","disc"),
 "computer-laptop": ("laptop",), "video-display": ("monitor",), "phone": ("smartphone",), "multimedia-player": ("music",),
 "printer": ("printer",), "scanner": ("scan",), "input-keyboard": ("keyboard",), "input-mouse": ("mouse",),
 "input-gaming": ("gamepad-2",), "input-tablet": ("tablet",), "input-touchpad": ("square-dashed",),
 "input-dialpad": ("grip",), "audio-card": ("volume-2",), "audio-headphones": ("headphones",), "audio-headset": ("headset",),
 "audio-speakers": ("speaker",), "audio-input-microphone": ("mic",), "camera-photo": ("camera",), "camera-web": ("webcam",),
 "camera-video": ("video",), "network-card": ("network",), "network-modem": ("router",), "network-firewall": ("shield",),
 "battery": ("battery-full",), "bluetooth": ("bluetooth",), "cpu": ("cpu",), "hifi": ("speaker",), "computer": ("monitor",),
 "network-server": ("server",), "network-vpn": ("shield",), "network-wired": ("cable","ethernet-port"),
 "network-wireless": ("wifi",), "gnome-dev-printer-new": ("printer",), "uninterruptible-power-supply": ("plug-zap","plug"),
 "pda": ("smartphone",), "gpu": ("cpu",), "ram": ("memory-stick",), "memory": ("memory-stick",), "thunderbolt": ("zap",),
 "usb-c": ("usb",), "smartphone": ("smartphone",), "tablet": ("tablet",), "watch": ("watch",), "tv": ("tv",),
 "gamepad": ("gamepad-2",), "joystick": ("joystick",), "webcam": ("webcam",), "projector": ("projector",),
}

PLACE_KEEP = {"user-home","user-desktop","user-trash","user-bookmarks","network-server","network-workgroup",
    "network","computer","user-identity","avatar-default","folder-remote","folder-remote-ftp","folder-remote-ssh",
    "folder-remote-smb","folder-remote-nfs","folder-remote-sftp","folder-remote-davs","distributor-logo","start-here"}
TILE_PLACES = {k: v for k, v in PLACE_TILES.items() if k in PLACE_KEEP}
TILE_PLACES.setdefault("network", ("network",))
TILE_PLACES.setdefault("user-trash-full", ("trash-2",))

# ================================================================== table apps
def candidates(n):
    parts = n.split(".")
    c = [n]
    if len(parts) > 2: c.append(parts[-1])
    c.append(re.sub(r"-(desktop|bin|qt|gtk|stable|beta|nightly|dev|app|client|launcher|studio)$", "", n))
    return c

BLACKLIST = {"note","files","discover","dolphin","oxygen","ring","pix","google","x","r","gtk","qt","kde","bluetooth","genius",
    "showtime","hotwire","crystal","proton","session","javascript","openjdk","deepin","yelp","apostrophe","stadia","appstore",
    "wayland","xdotorg","electron","rss","notepadplusplus","gradio","internetarchive","speedtest","php","wine","foursquare",
    "flickr","monero","binance","tradingview","basecamp","odoo","dota2","lichess","stremio","bilibili","qq","wechat","viber",
    "neteasecloudmusic","tvtime","lbry","deezer","guitarpro","mendeley","metasploit","burpsuite"}
MANUAL = {
 "vlc":"vlcmediaplayer","org.videolan.VLC":"vlcmediaplayer","vlc-qt":"vlcmediaplayer","obs":"obsstudio","obs-studio":"obsstudio",
 "com.obsproject.Studio":"obsstudio","gitlab":"gitlab","nextcloud":"nextcloud","com.nextcloud.desktopclient.nextcloud":"nextcloud",
 "godot":"godotengine","org.godotengine.Godot":"godotengine","flatpak":"flatpak","nixos":"nixos","epicgameslauncher":"epicgames",
 "com.epicgames.launcher":"epicgames","plex":"plex","plexmediaplayer":"plex","tv.plex.PlexDesktop":"plex","twitch":"twitch",
 "reddit":"reddit","mastodon":"mastodon","org.telegram.desktop":"telegram","org.mozilla.firefox":"firefox",
 "org.mozilla.Firefox":"firefox","org.mozilla.Thunderbird":"thunderbird","org.wezfurlong.wezterm":"wezterm",
 "com.mitchellh.ghostty":"ghostty","net.lutris.Lutris":"lutris","org.libreoffice.LibreOffice":"libreoffice",
 "zed":"zedindustries","dev.zed.Zed":"zedindustries","zeditor":"zedindustries","org.gnome.Terminal":"gnometerminal",
 "org.kde.kdenlive":"kdenlive","org.gimp.GIMP":"gimp","org.inkscape.Inkscape":"inkscape","org.blender.Blender":"blender",
 "org.audacityteam.Audacity":"audacity","com.valvesoftware.Steam":"steam","com.discordapp.Discord":"discord",
 "com.spotify.Client":"spotify","org.signal.Signal":"signal","com.brave.Browser":"brave","com.google.Chrome":"googlechrome",
 "io.gitlab.librewolf-community":"librewolf","app.zen_browser.zen":"zenbrowser","io.github.zen_browser.zen":"zenbrowser",
 "org.keepassxc.KeePassXC":"keepassxc","com.bitwarden.desktop":"bitwarden","md.obsidian.Obsidian":"obsidian",
 "org.qbittorrent.qBittorrent":"qbittorrent","org.kde.krita":"krita",
}

MANUAL.update({
 "vesktop":"discord","webcord":"discord","discord-canary":"discord","discord-development":"discord",
 "io.github.milkshiift.GoofCord":"discord","lightcord":"discord",
 "waterfox":"firefox","firefox-developer-icon":"firefox","firefox-trunk":"firefox","firedragon":"firefox",
 "google-chrome-unstable":"googlechrome",
 "viber":"viber","wechat":"wechat","qq":"qq","deezer":"deezer","tradingview":"tradingview","TradingView":"tradingview",
 "monero":"monero","Binance":"binance","binance":"binance","bitcoin128":"bitcoin","ledger-live-desktop":"ledger",
 "flickr":"flickr","foursquare":"foursquare","stremio":"stremio","lbry":"lbry","wine":"wine","r":"r",
 "metasploit":"metasploit","dota2":"dota2","Basecamp":"basecamp",
 "mongodb-compass":"mongodb","robo3t":"mongodb","mysql-workbench":"mysql","pgadmin":"postgresql",
 "sqlitebrowser":"sqlite","sqlitestudio":"sqlite","redisinsight":"redis","insomnia-designer":"insomnia",
 "calibre-gui":"calibre","calibre-viewer":"calibre","calibre-ebook-edit":"calibre",
 "unityhub":"unity","unity-editor-icon":"unity","protonmail-bridge":"protonmail","protonpass":"protonpass",
 "im.vector":"element","riot-web":"element","golang":"go","com.modrinth.ModrinthApp":"modrinth",
 "browser-tor":"torbrowser","jmeter":"apachejmeter","rustrover":"rustrover","com.jgraph.drawio.desktop":"diagramsdotnet",
 "org.fooyin.fooyin":"musicbrainz",
})
for _n, _slug in list(MANUAL.items()):
    if not os.path.exists(f"{SI}/icons/{_slug}.svg"):
        print("  (slug simple-icons introuvable, ignoré)", _n, "->", _slug)
        del MANUAL[_n]

SKIP = {"org.wireshark.gtk","org.wireshark.qt","io.qt.Qt","org.xfce.session","org.kde.plasma.bluetooth","org.gnome.Files","org.gnome.files","io.elementary.files"}

brand_table = {}
for n in sorted(tela):
    if n in SKIP: continue
    for c in candidates(n):
        k = norm(c)
        if k in idx:
            if idx[k] not in BLACKLIST: brand_table[n] = idx[k]
            break
for n, slug in MANUAL.items():
    if os.path.exists(f"{SI}/icons/{slug}.svg"): brand_table[n] = slug

for slug, names in CUSTOM_NAMES.items():
    for n in names:
        if n in tela or n in FDO_KEEP:
            brand_table[n] = slug
for n, slug in list(brand_table.items()):      # les marques de SLUG_LUCIDE gardent leurs noms
    pass

# apps génériques : seulement les noms que Tela connaît (ou FDO), jamais ceux d'une marque
generic = {}
for glyphs, names in GENERIC_APPS.items():
    for n in names:
        if "dummy" in n or n in brand_table: continue
        if n in tela or n in FDO_KEEP:
            generic.setdefault(n, glyphs)

# ================================================================== écriture
INDEX = """[Icon Theme]
Name={name}
Comment=Thème d'icônes natif de Roudix : tuiles sombres/claires, glyphes orange, dossiers Roudix.
Inherits=Adwaita,breeze,hicolor
Example=folder

DisplayDepth=32
DesktopDefault=48
DesktopSizes=16,22,32,48,64,96,128,256
ToolbarDefault=22
ToolbarSizes=16,22,32,48
MainToolbarDefault=22
MainToolbarSizes=16,22,32,48
SmallDefault=16
SmallSizes=16,22,32,48
PanelDefault=48
PanelSizes=16,22,32,48,64,96,128,256
DialogDefault=32
DialogSizes=16,22,32,48,64,128,256
FollowsColorScheme=false
KDE-Extensions=.svg

Directories=scalable/apps,scalable/categories,scalable/devices,scalable/mimetypes,scalable/places

[scalable/apps]
Context=Applications
Size=48
MinSize=8
MaxSize=512
Type=Scalable

[scalable/categories]
Context=Categories
Size=48
MinSize=8
MaxSize=512
Type=Scalable

[scalable/devices]
Context=Devices
Size=48
MinSize=8
MaxSize=512
Type=Scalable

[scalable/mimetypes]
Context=MimeTypes
Size=48
MinSize=8
MaxSize=512
Type=Scalable

[scalable/places]
Context=Places
Size=48
MinSize=8
MaxSize=512
Type=Scalable
"""

def import_source(n):
    """Fichier SVG réel (Tela d'abord, puis Papirus) pour un nom d'app, ou None.
    ROUDIX_NO_IMPORT=1 désactive l'import (thème 100 % permissif, sans dérivés GPL)."""
    if os.environ.get("ROUDIX_NO_IMPORT"): return None
    cands = [f"{TELA}/src/scalable/apps/{n}.svg", f"{TELA}/links/scalable/apps/{n}.svg"]
    if PAPIRUS: cands.append(f"{PAPIRUS}/{n}.svg")
    for pth in cands:
        if os.path.lexists(pth):
            r = os.path.realpath(pth)
            if os.path.exists(r): return r
    return None

stats = {}
def write_set(dirpath, files, aliases):
    """files: slug->svg ; aliases: name->slug (liens symboliques)"""
    os.makedirs(dirpath, exist_ok=True)
    for slug, content in files.items():
        open(f"{dirpath}/{slug}.svg", "w", encoding="utf-8").write(content)
    for n, slug in sorted(aliases.items()):
        if n == slug: continue
        p = f"{dirpath}/{n}.svg"
        if not os.path.lexists(p):
            os.symlink(f"{slug}.svg", p)

def group_by_glyph(table, keep_filter):
    """{name: glyph-candidates} -> (files by canonical name, aliases)"""
    by = {}
    for n, g in table.items():
        if keep_filter(n): by.setdefault(g, []).append(n)
    return by

shutil.rmtree(OUT, ignore_errors=True)
mapping = {"apps_brand": brand_table, "apps_generic": {n: g[0] for n, g in generic.items()}, "apps_imported": {}}

for variant, st in STYLES.items():
    base = f"{OUT}/{variant}"
    os.makedirs(base)
    open(f"{base}/index.theme", "w").write(INDEX.format(name=st["title"]))

    # ---- apps : marques
    files, aliases = {}, {}
    for i, slug in enumerate(sorted(set(brand_table.values()))):
        if slug in SLUG_LUCIDE:
            files[slug] = tile_lucide(st, lucide(*SLUG_LUCIDE[slug]), f"b{i}")
        elif slug in CUSTOM_STROKE:
            files[slug] = tile_lucide(st, CUSTOM_STROKE[slug], f"b{i}")
        else:
            files[slug] = tile_brand(st, slug, f"b{i}")
    aliases.update(brand_table)
    # ---- apps : icônes Tela/Papirus converties en style Roudix (avant : glyphe générique)
    import_done = set()
    src_canon = {}
    vkey = "light" if variant == "Roudix-Light" else "dark"
    for n in sorted(generic):
        srcp = import_source(n)
        if not srcp: continue
        if srcp not in src_canon:
            try:
                res = roudixify.import_inner(srcp, vkey, len(src_canon))
            except Exception:
                res = None
            if not res:
                src_canon[srcp] = None
            else:
                canon = "roudix-" + re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(srcp)[:-4])
                files[canon] = tile_import(st, res[0], res[1], f"t{len(src_canon)}")
                src_canon[srcp] = canon
        if src_canon[srcp]:
            aliases[n] = src_canon[srcp]; import_done.add(n)
            mapping["apps_imported"][n] = ("Tela" if srcp.startswith(os.path.realpath(TELA)) or srcp.startswith(TELA) else "Papirus") + ":" + os.path.basename(srcp)
    # ---- apps : glyphe générique pour les noms sans icône source exploitable
    gi = 0
    rest = {n: g for n, g in generic.items() if n not in import_done}
    for glyphs, names in group_by_glyph(rest, lambda n: True).items():
        inner = lucide(*glyphs)
        if not inner: continue
        canon = f"roudix-generic-{glyphs[0]}"
        files[canon] = tile_lucide(st, inner, f"g{gi}"); gi += 1
        for n in names: aliases[n] = canon
    write_set(f"{base}/scalable/apps", files, aliases)
    stats.setdefault("apps", (len(files), len(aliases)))

    # ---- categories
    files, aliases = {}, {}
    for i, (n, g) in enumerate(sorted(CATEGORIES.items())):
        inner = lucide(*g)
        if inner: files[n] = tile_lucide(st, inner, f"c{i}")
    write_set(f"{base}/scalable/categories", files, {})
    stats.setdefault("categories", (len(files), 0))

    # ---- devices
    files, aliases = {}, {}
    for i, (n, g) in enumerate(sorted(DEVICES.items())):
        if n in tela_devices or n in tela or n in ("computer","network-server"):
            inner = lucide(*g)
            if inner: files[n] = tile_lucide(st, inner, f"d{i}")
    write_set(f"{base}/scalable/devices", files, {})
    stats.setdefault("devices", (len(files), 0))

    # ---- places : dossiers
    files, aliases = {}, {}
    fi = 0
    for n, (g, opened) in sorted(FOLDERS.items()):
        if not (n in tela_places or n in FDO_KEEP): continue
        inner = lucide(*g) if g else None
        if g and not inner: continue
        files[n] = folder(st, inner, f"f{fi}", opened); fi += 1
    # places : tuiles
    for i, (n, g) in sorted(enumerate(sorted(TILE_PLACES.items()))):
        pass
    ti = 0
    for n, g in sorted(TILE_PLACES.items()):
        if n in files: continue
        inner = lucide(*g)
        if inner: files[n] = tile_lucide(st, inner, f"p{ti}"); ti += 1
    # corbeille pleine : badge orange
    t = lucide("trash-2")
    if t:
        badge = f'  <circle cx="35" cy="13" r="4.6" fill="{st["glyph"][1]}" stroke="{st["tile"][1]}" stroke-width="1.4"/>\n'
        files["user-trash-full"] = svg(st, tile_base(st, "tf") + glyph_stroke(st, t, "tf") + badge, "tf")
    # logo Roudix = start-here / distributor-logo
    logo = open(LOGO, encoding="utf-8").read()
    files["start-here"] = logo
    aliases.update({"distributor-logo": "start-here", "distributor-logo-roudix": "start-here", "roudix": "start-here",
                    "roudix-logo": "start-here", "start-here-roudix": "start-here"})
    write_set(f"{base}/scalable/places", files, aliases)
    stats.setdefault("places", (len(files), len(aliases)))

    # ---- mimetypes
    files, aliases = {}, {}
    mi = 0
    for glyphs, names in MIMES.items():
        inner = lucide(*glyphs)
        if not inner: continue
        ns = [n for n in names if "dummy" not in n and (n in tela_mimes or n in FDO_KEEP)]
        if not ns: continue
        canon = ns[0]
        files[canon] = page(st, inner, f"m{mi}"); mi += 1
        for n in ns[1:]: aliases[n] = canon
    # dossier "inode-directory" : réutilise le dossier Roudix
    write_set(f"{base}/scalable/mimetypes", files, aliases)
    os.symlink("../places/folder.svg", f"{base}/scalable/mimetypes/inode-directory.svg") if not os.path.lexists(f"{base}/scalable/mimetypes/inode-directory.svg") else None
    stats.setdefault("mimetypes", (len(files), len(aliases)))

json.dump(mapping, open(f"{OUT}/mapping.json", "w"), indent=1, sort_keys=True)
print("stats (fichiers réels, alias):", stats)
if missing:
    print("glyphes Lucide introuvables:", sorted({c for m in missing for c in m}))
