#!/usr/bin/env python3
import gi
import os
import re
import subprocess
import sys
import logging
import configparser

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Pango, Gdk

CONFIG_FILE = os.path.expanduser("~/.config/roudix/hosts/roudix/local.nix")
# roudix.fastfetch.useNix (and any future Home Manager option) doesn't
# live in the system config — it must be written here, or the rebuild
# fails with "The option `roudix.fastfetch' does not exist".
HOME_CONFIG_FILE = os.path.expanduser("~/.config/roudix/modules/home/local.nix")
NH_FLAKE    = os.path.expanduser("~/.config/roudix")

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR   = os.path.join(SCRIPT_DIR, "../share/roudix-switcher/icons")

LOG_DIR     = os.path.expanduser("~/.local/share/roudix-switcher")
LOG_FILE    = os.path.join(LOG_DIR, "switcher.log")
TMP_LOG     = "/tmp/roudix-switcher.log"

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def _detect_lang() -> str:
    """
    Tiny bilingual helper, same fr/en idiom as the installer
    (roudix_installer.i18n.L), but auto-detected from the system locale
    instead of an explicit picker — the switcher has no first-run wizard
    to ask in, it's launched straight into the task at hand.
    """
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        val = os.environ.get(var, "")
        if val:
            return "fr" if val.lower().startswith("fr") else "en"
    return "en"


LANG = _detect_lang()


def L(fr: str, en: str) -> str:
    return fr if LANG == "fr" else en


ENVIRONMENTS = [
    {
        "id":       "niri",
        "name":     "Niri",
        "subtitle": L("Compositeur Wayland en tuilage défilant", "Scrollable tiling Wayland compositor"),
        "icon":     "niri.svg",
    },
    {
        "id":       "hyprland",
        "name":     "Hyprland",
        "subtitle": L("Compositeur Wayland en tuilage dynamique", "Dynamic tiling Wayland compositor"),
        "icon":     "hyprland.svg",
    },
    {
        "id":       "gnome",
        "name":     "GNOME",
        "subtitle": L("GNOME — bureau moderne et convivial", "GNOME — modern and user-friendly desktop"),
        "icon":     "gnome.svg",
    },
    {
        "id":       "kde",
        "name":     "KDE Plasma",
        "subtitle": L("KDE Plasma — environnement hautement personnalisable et complet", "KDE Plasma — Highly customizable and feature-rich desktop environment"),
        "icon":     "kde.svg",
    },
    {
        "id":       "mangowc",
        "name":     "MangoWC",
        "subtitle": L("Compositeur Wayland en tuilage dynamique, léger", "Lightweight dynamic tiling Wayland compositor"),
        "icon":     "mangowc.svg",
    },

     {
         "id":       "umbriel",
         "name":     "Umbriel",
         "subtitle": L(
             "Compositeur Wayland pensé pour l'usage quotidien, avec layouts scrolling/dwindle/master, espaces de travail par sortie, règles de fenêtres, flou, ombres et animations fluides.",
             "a Wayland compositor designed for daily use, with scrolling, dwindle, and master layouts, per-output workspaces, window rules, blur, shadows, and fluid animations.",
         ),
         "icon":     "umbriel.svg",
     },
]

# Graphical shells — available only for niri and hyprland
SHELLS = [
    {
        "id":       "noctalia",
        "name":     "Noctalia",
        "subtitle": L("Shell par défaut de Roudix — soigné et complet", "Roudix default shell — sleek and feature-complete"),
        "icon":     "noctalia.svg",
    },
    {
        "id":       "dms",
        "name":     "DMS",
        "subtitle": L("Shell Roudix minimal et léger", "Minimal and lightweight Roudix shell"),
        "icon":     "dms.svg",
    },
]

CAELESTIA = [
    {
        "id":       "caelestia",
        "name":     "Caelestia",
        "subtitle": L("Shell Roudix élégant, axé sur l'esthétique", "Elegant Roudix shell with a focus on aesthetics"),
        "icon":     "caelestia.svg",
    },
]

UMBRIEL = [
    {
        "id":       "noctalia",
        "name":     "Noctalia",
        "subtitle": L("Shell par défaut de Roudix — soigné et complet", "Roudix default shell — sleek and feature-complete"),
        "icon":     "noctalia.svg",
    },

]

# Compositors that support choosing a graphical shell
SHELL_SUPPORTED_DE    = {"niri", "hyprland", "mangowc", "umbriel"}
CAELESTIA_SUPPORTED_DE = {"hyprland"}
UMBRIEL_SUPPORTED_DE = {"umbriel"}

# ── Tweaks: editor, keyring/portal, gaming apps ───────────────────────────
# These three categories follow the same principle as DE/shell: a value
# chosen among several (enum, written as a string in local.nix), or a set
# of independent booleans. See roudix.editor, roudix.desktopIntegration
# and roudix.gaming.apps.* on the Nix side.

EDITORS = [
    {"id": "zed",    "name": "Zed",     "subtitle": L("Éditeur rapide, accéléré par le GPU (défaut Roudix)", "Fast GPU-accelerated editor (Roudix default)"), "icon": "zed.svg"},
    {"id": "vscode", "name": "VS Code", "subtitle": L("Éditeur de Microsoft, immense écosystème d'extensions", "Microsoft's editor, huge extension ecosystem"),  "icon": "vscode.svg"},
    {"id": "neovim", "name": "Neovim",  "subtitle": L("Basé terminal, piloté au clavier", "Terminal-based, keyboard-driven"),                "icon": "neovim.svg"},
    {"id": "none",   "name": L("Aucun", "None"),    "subtitle": L("N'installer aucun éditeur par défaut", "Don't install a default editor"),                 "icon": "none.svg"},
]

DESKTOP_INTEGRATIONS = [
    {
        "id": "gnome",
        "name": "GNOME",
        "subtitle": L("gnome-keyring + xdg-desktop-portal-gtk/-gnome (défaut)", "gnome-keyring + xdg-desktop-portal-gtk/-gnome (default)"),
        "icon": "gnome.svg",
    },
    {
        "id": "kde",
        "name": "KDE",
        "subtitle": "KWallet + xdg-desktop-portal-kde",
        "icon": "kde.svg",
    },
]
# Only "bare" compositors respect this choice — gnome/kde always keep
# their own native stack.
DESKTOP_INTEGRATION_SUPPORTED_DE = {"niri", "hyprland", "mangowc", "umbriel"}

# roudix.iconTheme (modules/system/icon-theme.nix) — same "bare compositors
# only" scope as desktop integration above: GNOME/KDE always keep their own
# native icon picker (GNOME Settings / System Settings), and Papirus/Tela
# there is whatever the user already chose that way, independent of this.
ICON_THEMES = [
    {
        "id": "papirus",
        "name": "Papirus",
        "subtitle": L("Thème fixe, accent bleu Papirus (défaut)", "Fixed theme, Papirus' own blue accent (default)"),
        "icon": "icon-theme-papirus.svg",
    },
    {
        "id": "tela",
        "name": "Tela",
        "subtitle": L(
            "Recoloré automatiquement sur l'accent Noctalia actuel si roudix.desktop.shell = \"noctalia\" ; sinon Tela classique",
            "Auto-recolored to the current Noctalia accent if roudix.desktop.shell = \"noctalia\"; plain Tela otherwise",
        ),
        "icon": "icon-theme-tela.svg",
    },
    {
        "id": "qogir",
        "name": "Qogir",
        "subtitle": L("Flat coloré, style Material (pkgs.qogir-icon-theme)", "Flat, colorful Material-style set (pkgs.qogir-icon-theme)"),
        "icon": "icon-theme-qogir.svg",
    },
    {
        "id": "whitesur",
        "name": "WhiteSur",
        "subtitle": L("Inspiré macOS Big Sur (pkgs.whitesur-icon-theme)", "macOS Big Sur-inspired (pkgs.whitesur-icon-theme)"),
        "icon": "icon-theme-whitesur.svg",
    },
    {
        "id": "colloid",
        "name": "Colloid",
        "subtitle": L("Flat, teintes douces (pkgs.colloid-icon-theme)", "Flat, soft-toned set (pkgs.colloid-icon-theme)"),
        "icon": "icon-theme-colloid.svg",
    },
]

# On-disk folder names already covered by the curated tiles above — used to
# de-duplicate roudix-switcher's icon-theme scan (see scan_icon_themes())
# so e.g. a scanned "Papirus-Dark" doesn't show up twice next to "Papirus".
KNOWN_ICON_THEME_IDS = {
    "Papirus", "Papirus-Dark", "Papirus-Light",
    "Tela", "Tela-dark", "Tela-light",
    "Tela-dark-noctalia", "Tela-light-noctalia", "Tela-noctalia",
    "Qogir", "Qogir-dark", "Qogir-light", "Qogir-manjaro", "Qogir-manjaro-dark",
    "WhiteSur", "WhiteSur-dark", "WhiteSur-light",
    "Colloid", "Colloid-dark", "Colloid-light",
}

# name -> Nix option (roudix.gaming.apps.<id>.enable), all true by default
GAMING_APPS = [
    {"id": "lutris",        "name": "Lutris",         "key": "roudix.gaming.apps.lutris.enable",        "default": True},
    {"id": "heroic",        "name": "Heroic",         "key": "roudix.gaming.apps.heroic.enable",        "default": True},
    {"id": "faugus",        "name": "Faugus Launcher","key": "roudix.gaming.apps.faugus.enable",        "default": True},
    {"id": "prismlauncher", "name": "Prism Launcher", "key": "roudix.gaming.apps.prismlauncher.enable", "default": True},
    {"id": "modrinth",      "name": "Modrinth",       "key": "roudix.gaming.apps.modrinth.enable",      "default": True},
    {"id": "vintagestory",  "name": "Vintage Story",  "key": "roudix.gaming.apps.vintagestory.enable",  "default": True},
    {"id": "mangohud",      "name": "MangoHud",       "key": "roudix.gaming.apps.mangohud.enable",      "default": True},
]

TERMINALS = [
    {"id": "ghostty",   "name": "Ghostty",   "subtitle": L("Accéléré GPU, défaut Roudix", "GPU-accelerated, Roudix default"), "icon": "ghostty.svg"},
    {"id": "kitty",     "name": "Kitty",     "subtitle": L("Accéléré GPU, riche en fonctionnalités", "GPU-accelerated, feature-rich"),     "icon": "kitty.svg"},
    {"id": "alacritty", "name": "Alacritty", "subtitle": L("Minimaliste, accéléré GPU", "Minimal, GPU-accelerated"),          "icon": "alacritty.svg"},
    {"id": "foot",      "name": "Foot",      "subtitle": L("Léger, natif Wayland", "Lightweight, Wayland-native"),       "icon": "foot.svg"},
    {"id": "wezterm",   "name": "WezTerm",   "subtitle": L("Multiplateforme, configurable en Lua", "Cross-platform, Lua-configurable"),  "icon": "wezterm.svg"},
    {"id": "ptyxis",    "name": "Ptyxis",    "subtitle": L("Terminal de GNOME, conscient des conteneurs", "GNOME's container-aware terminal"),  "icon": "ptyxis.svg"},
    {"id": "konsole",   "name": "Konsole",   "subtitle": L("L'émulateur de terminal de KDE", "KDE's terminal emulator"),           "icon": "konsole.svg"},
]

# roudix.browsers is a LIST (not an enum): several browsers can be
# installed at once. Exposed as a checklist rather than an exclusive
# selector. The first checked entry becomes the default (niri MOD+B
# shortcut) — the same logic already used on the Nix side
# (roudix.browser.default = lib.head cfg.browsers).
BROWSERS = [
    {"id": "brave",                 "name": "Brave"},
    {"id": "brave-beta",            "name": "Brave Beta"},
    {"id": "brave-nightly",         "name": "Brave Nightly"},
    {"id": "brave-origin",          "name": "Brave (Origin)"},
    {"id": "brave-origin-beta",     "name": "Brave (Origin) Beta"},
    {"id": "brave-origin-nightly",  "name": "Brave (Origin) Nightly"},
    {"id": "helium",                "name": "Helium"},
    {"id": "vivaldi",                "name": "Vivaldi"},
    {"id": "chromium",              "name": "Chromium"},
    {"id": "firefox",               "name": "Firefox"},
    {"id": "librewolf",             "name": "LibreWolf"},
    {"id": "google-chrome",         "name": "Google Chrome"},
    {"id": "microsoft-edge",        "name": "Microsoft Edge"},
    {"id": "ungoogled-chromium",    "name": "Ungoogled Chromium"},
]

# roudix.shell: the LOGIN shell (fish/bash) — not to be confused with the
# graphical "shell" (noctalia/dms/caelestia) on the Desktop page.
LOGIN_SHELLS = [
    {"id": "fish", "name": "fish", "subtitle": L("Shell interactif convivial (défaut Roudix)", "Friendly interactive shell (Roudix default)"), "icon": "fish.svg"},
    {"id": "bash", "name": "bash", "subtitle": L("Le shell POSIX classique", "The classic POSIX shell"),                    "icon": "bash.svg"},
]

FILE_MANAGERS = [
    {"id": "nautilus",   "name": "Nautilus (Files)", "subtitle": L("Gestionnaire de fichiers de GNOME", "GNOME's file manager"),   "icon": "nautilus.svg"},
    {"id": "dolphin",    "name": "Dolphin",           "subtitle": L("Gestionnaire de fichiers de KDE", "KDE's file manager"),     "icon": "dolphin.svg"},
    {"id": "nemo",       "name": "Nemo",              "subtitle": L("Gestionnaire de fichiers de Cinnamon", "Cinnamon's file manager"),"icon": "nemo.svg"},
    {"id": "thunar",     "name": "Thunar",            "subtitle": L("Léger, celui de XFCE", "Lightweight, XFCE's file manager"),                "icon": "thunar.svg"},
    {"id": "pcmanfm-qt", "name": "PCManFM-Qt",        "subtitle": L("Léger, en Qt", "Lightweight, Qt-based"),                        "icon": "pcmanfm-qt.svg"},
]
# Like Integration: no effect on gnome/kde, which keep their native manager.
FILE_MANAGER_SUPPORTED_DE = {"niri", "hyprland", "mangowc", "umbriel"}

MATRIX_CLIENTS = [
    {"id": "element", "name": "Element", "subtitle": L("Client Matrix complet (défaut)", "Full-featured Matrix client (default)"),      "icon": "element.svg"},
    {"id": "cinny",   "name": "Cinny",   "subtitle": L("Client Matrix léger", "Lightweight Matrix client"),                 "icon": "cinny.svg"},
    {"id": "none",    "name": L("Aucun", "None"),    "subtitle": L("N'installer aucun client Matrix", "Don't install a Matrix client"),     "icon": "none.svg"},
]

DISCORD_OPTIONS = [
    {"id": "vencord", "name": "Vencord", "subtitle": L("Discord avec Vencord déjà patché (défaut)", "Discord with Vencord already patched in (default)"), "icon": "vencord.svg"},
    {"id": "vanilla", "name": "Vanilla", "subtitle": L("Discord sans aucun patch client", "Discord with no client patches"),            "icon": "discord.svg"},
    {"id": "none",    "name": L("Aucun", "None"),    "subtitle": L("N'installer aucun client Discord", "Don't install a Discord client"),           "icon": "none.svg"},
]

TELEGRAM_OPTIONS = [
    {"id": "telegram", "name": "Telegram", "subtitle": L("Client officiel Telegram Desktop", "Official Telegram Desktop client"), "icon": "telegram.svg"},
    {"id": "ayugram",  "name": "AyuGram",  "subtitle": L("Fork non-officiel : mode fantôme, anti-suppression...", "Unofficial fork: ghost mode, anti-recall..."), "icon": "ayugram.svg"},
    {"id": "none",     "name": L("Aucun", "None"), "subtitle": L("N'installer aucun client Telegram", "Don't install a Telegram client"), "icon": "none.svg"},
]

VIDEO_PLAYERS = [
    {"id": "vlc",       "name": "VLC",       "subtitle": L("Le plus large support de formats (défaut)", "Widest format/codec support (default)"), "icon": "vlc.svg"},
    {"id": "clapper",   "name": "Clapper",   "subtitle": L("Lecteur GTK4 moderne", "Modern GTK4 player"), "icon": "clapper.svg"},
    {"id": "mpv",       "name": "mpv",       "subtitle": L("+ yt-dlp — minimaliste, streaming/URL", "+ yt-dlp — minimal, URL/streaming support"), "icon": "mpv.svg"},
    {"id": "celluloid", "name": "Celluloid", "subtitle": L("Interface GTK pour mpv", "GTK front-end for mpv"), "icon": "celluloid.svg"},
    {"id": "none",      "name": L("Aucun", "None"), "subtitle": L("N'installer aucun lecteur vidéo", "Don't install a video player"), "icon": "none.svg"},
]

TORRENT_CLIENTS = [
    {"id": "qbittorrent", "name": "qBittorrent", "subtitle": L("Complet, basé sur Qt", "Feature-rich, Qt-based"), "icon": "qbittorrent.svg"},
    {"id": "fragments",   "name": "Fragments",   "subtitle": L("Client GNOME/libadwaita minimaliste", "Minimal GNOME/libadwaita client"), "icon": "fragments.svg"},
    {"id": "deluge",      "name": "Deluge",      "subtitle": L("Basé sur des plugins, léger", "Plugin-based, lightweight"), "icon": "deluge.svg"},
    {"id": "none",        "name": L("Aucun", "None"), "subtitle": L("N'installer aucun client torrent", "Don't install a torrent client"), "icon": "none.svg"},
]

RGB_BACKENDS = [
    {"id": "openlinkhub", "name": "OpenLinkHub", "subtitle": L("Pour périphériques compatibles Corsair iCUE", "For Corsair iCUE-compatible devices"), "icon": "openlinkhub.svg"},
    {"id": "openrgb",     "name": "OpenRGB",      "subtitle": L("Support RGB multi-marques", "Multi-brand RGB support"),                   "icon": "openrgb.svg"},
    {"id": "none",        "name": L("Aucun", "None"),         "subtitle": L("Aucun backend RGB", "No RGB backend"),                           "icon": "none.svg"},
]

# TODO: fill in with the IDs of the Zen mods actually in use (native
# store https://zen-browser.app/mods or Sine — same ID list either way,
# only the Nix target changes based on roudix.zen.sine.enable). Once
# filled in, each mod becomes toggleable like the browsers.
# Example: {"id": "zen-internet", "name": "Zen Internet"},
ZEN_MODS = [
    # Confirmed (chrome/sine-mods/): UUID folder = the official theme-store one
    {"id": "ad97bb70-0066-4e42-9b5f-173a5e42c6fc", "name": "SuperPins"},
    # Confirmed directly from the chrome/sine-mods/ listing — these are
    # literally folder names, not UUIDs.
    {"id": "Arc-2.0", "name": "Arc 2.0"},
    {"id": "context-menu-icons", "name": "Context Menu Icons"},
    {"id": "floating-statusbar", "name": "Floating Statusbar"},
    {"id": "unloaded-tabs", "name": "Unloaded Tabs"},
    {"id": "new-icons", "name": "New Icons"},
    {"id": "Nebula", "name": "Nebula"},
    # Confirmed (identified from chrome/sine-mods/)
    {"id": "3c8ebf69-1042-49b1-8f08-9178f9490659", "name": "Better Music Bar"},
    {"id": "jvynuz3kn-hjd9pvfmg-vonasfop9", "name": "zen-container-halo"},
]

# Extra gaming tweaks (alongside the launchers) — same boolean keys as
# GAMING_APPS but shown in a separate group on the Gaming page.
GAMING_EXTRAS = [
    {"id": "ananicy", "name": L("Ananicy (ordonnanceur process)", "Ananicy (process scheduler)"), "key": "roudix.gaming.ananicy.enable", "default": False},
    {"id": "gtaFix",  "name": L("Correctif hosts GTA Online", "GTA Online hosts fix"),     "key": "roudix.hosts.gtaFix.enable",   "default": False},
]

# roudix.zen.variant — enum, exposed as a SelectorGroup (like EDITORS).
ZEN_VARIANTS = [
    {"id": "twilight",          "name": "Twilight",             "subtitle": L("Nightly de Zen Beta, miroir maintenu par le dev du flake (défaut Roudix)", "Nightly build of Zen Beta, mirrored by the flake maintainer (Roudix default)"), "icon": "zen-twilight.svg"},
    {"id": "beta",               "name": "Beta",                 "subtitle": L("Basé sur Firefox (build normale), évolue moins vite, le plus stable", "Firefox-based (regular release), slower-moving, most stable"),               "icon": "zen.svg"},
]

# roudix.contentCreation.videoEditor — enum, exposed as a SelectorGroup.
VIDEO_EDITORS = [
    {"id": "kdenlive",              "name": "Kdenlive",              "subtitle": L("Éditeur libre basé sur KDE (défaut Roudix)", "Free KDE-based editor (Roudix default)"),                    "icon": "kdenlive.svg"},
    {"id": "davinci-resolve",        "name": "DaVinci Resolve",       "subtitle": L("Édition gratuite — étalonnage, VFX, niveau pro", "Free edition — color grading, VFX, pro-grade"),                 "icon": "davinci-resolve.svg"},
    {"id": "davinci-resolve-studio", "name": "DaVinci Resolve Studio","subtitle": L("Édition payante de ci-dessus — licence Blackmagic requise", "Paid edition of the above — requires a Blackmagic license"),"icon": "davinci-resolve.svg"},
    {"id": "shotcut",                 "name": "Shotcut",               "subtitle": L("Léger, multiplateforme, basé sur FFmpeg", "Lightweight, cross-platform, FFmpeg-based"),                        "icon": "shotcut.svg"},
    {"id": "none",                    "name": L("Aucun", "None"),                  "subtitle": L("N'installer aucun éditeur vidéo", "Don't install a default video editor"),                                "icon": "none.svg"},
]

# roudix.contentCreation.obs.plugins.<id>.enable — one boolean per plugin
# (like GAMING_APPS), so ToggleListGroup + _diff_bool_items like the rest
# rather than a list. Aitum Multistream replaces obs-multi-rtmp: it's the
# multistreaming plugin actively maintained by the Aitum team (already
# known for obs-vertical-canvas), with independent encoders/bitrate per
# platform.
OBS_PLUGINS = [
    {"id": "vkcapture",              "name": L("VKCapture (capture jeux Vulkan/OpenGL)", "VKCapture (Vulkan/OpenGL game capture)"),              "key": "roudix.contentCreation.obs.plugins.vkcapture.enable",              "default": True},
    {"id": "pipewireAudioCapture",   "name": L("Pipewire Audio Capture (audio par application)", "Pipewire Audio Capture (per-app audio)"),      "key": "roudix.contentCreation.obs.plugins.pipewireAudioCapture.enable",   "default": True},
    {"id": "backgroundRemoval",      "name": L("Background Removal (fond virtuel IA)", "Background Removal (AI virtual background)"),                "key": "roudix.contentCreation.obs.plugins.backgroundRemoval.enable",      "default": False},
    {"id": "moveTransition",         "name": L("Move Transition (animations de sources)", "Move Transition (source animations)"),             "key": "roudix.contentCreation.obs.plugins.moveTransition.enable",         "default": False},
    {"id": "aitumMultistream",       "name": L("Aitum Multistream (stream multi-plateformes)", "Aitum Multistream (multi-platform streaming)"),        "key": "roudix.contentCreation.obs.plugins.aitumMultistream.enable",       "default": False},
    {"id": "gstreamer",              "name": L("GStreamer (sources/sorties supplémentaires)", "GStreamer (extra sources/outputs)"),         "key": "roudix.contentCreation.obs.plugins.gstreamer.enable",              "default": False},
    {"id": "compositeBlur",          "name": L("Composite Blur (flou/verre dépoli)", "Composite Blur (blur/glass filters)"),                  "key": "roudix.contentCreation.obs.plugins.compositeBlur.enable",          "default": False},
    {"id": "advancedSceneSwitcher",  "name": L("Advanced Scene Switcher (changement de scène auto)", "Advanced Scene Switcher (automated scene switching)"),  "key": "roudix.contentCreation.obs.plugins.advancedSceneSwitcher.enable",  "default": False},
    {"id": "inputOverlay",           "name": L("Input Overlay (clavier/souris/manette à l'écran)", "Input Overlay (on-screen keyboard/mouse/gamepad)"),    "key": "roudix.contentCreation.obs.plugins.inputOverlay.enable",           "default": False},
    {"id": "waveform",                "name": L("Waveform (spectre/waveform audio)", "Waveform (audio waveform/spectrum)"),                   "key": "roudix.contentCreation.obs.plugins.waveform.enable",                "default": False},
]

# Independent toggles on the Content Creation page (like SYSTEM_TOGGLES).
CONTENT_CREATION_TOGGLES = [
    {"id": "obs",           "name": "OBS Studio",                       "key": "roudix.contentCreation.obs.enable",                    "default": True},
    {"id": "virtualCamera", "name": L("Webcam virtuelle (v4l2loopback)", "Virtual camera (v4l2loopback)"),   "key": "roudix.contentCreation.virtualCamera.enable",          "default": True},
    {"id": "chatterino",    "name": L("Chatterino2 (chat Twitch tiers)", "Chatterino2 (third-party Twitch chat)"),   "key": "roudix.contentCreation.streaming.chatterino.enable",   "default": False},
]


# Independent system toggles, unrelated to each other — grouped into a
# "System" page rather than creating one category per option.
SYSTEM_TOGGLES = [
    {"id": "flatpak",        "name": "Flatpak",                          "key": "roudix.flatpak.enable",        "default": False},
    {"id": "virtualization", "name": L("Virtualisation (QEMU/KVM)", "Virtualization (QEMU/KVM)"),        "key": "roudix.virtualization.enable",  "default": False},
    {"id": "waydroid",       "name": L("Waydroid (apps Android)", "Waydroid (Android apps)"),          "key": "roudix.waydroid.enable",        "default": False},
    {"id": "mesaGit",        "name": L("Mesa-git (pilotes GPU bleeding-edge)", "Mesa-git (bleeding-edge GPU drivers)"), "key": "roudix.mesa.useGit",        "default": False},
    {"id": "autoupdate",     "name": L("Auto-update (git pull + rebuild programmé)", "Auto-update (scheduled git pull + rebuild)"), "key": "roudix.autoupdate.enable", "default": False},
    {"id": "undervoltAmd",   "name": L("Undervolt GPU AMD (LACT)", "AMD GPU undervolt (LACT)"),         "key": "roudix.undervolt.only-amd.enable", "default": False},
    # "file": roudix.fastfetch.useNix is a Home Manager option (defined in
    # modules/home/fastfetch.nix), not a system option — so it must be
    # written to HOME_CONFIG_FILE, not CONFIG_FILE.
    {"id": "fastfetchNix",   "name": L("Config fastfetch Roudix", "Roudix fastfetch config"),          "key": "roudix.fastfetch.useNix",       "default": True, "file": HOME_CONFIG_FILE},
    {"id": "fstrim",         "name": L("Fstrim (TRIM auto pour SSD/NVMe)", "Fstrim (automatic TRIM for SSD/NVMe)"), "key": "roudix.fstrim.enable",          "default": True},
    {"id": "vmGuest",        "name": L("Invité VM (QEMU/Spice agent)", "VM guest (QEMU/Spice agent)"),     "key": "roudix.vmGuest.enable",         "default": False},
]


def shells_for_de(de_id: str) -> list:
    """Return the shell list appropriate for the given DE."""
    if de_id in UMBRIEL_SUPPORTED_DE:
        return UMBRIEL
    return SHELLS + (CAELESTIA if de_id in CAELESTIA_SUPPORTED_DE else [])


# ── Logging setup ─────────────────────────────────────────────────────────────

def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.FileHandler(TMP_LOG, mode="w", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

log = logging.getLogger("roudix-switcher")


# ── Helpers ───────────────────────────────────────────────────────────────────

def strip_ansi(text):
    return ANSI_ESCAPE.sub('', text)


def get_current_de():
    try:
        with open(CONFIG_FILE) as f:
            for line in f:
                if "roudix.desktop.type" in line:
                    m = re.search(r'"(\w+)"', line)
                    if m:
                        return m.group(1)
    except Exception:
        pass
    return "niri"


def get_current_shell():
    try:
        with open(CONFIG_FILE) as f:
            for line in f:
                if "roudix.desktop.shell" in line:
                    m = re.search(r'"(\w+)"', line)
                    if m:
                        return m.group(1)
    except Exception:
        pass
    return "noctalia"


def _insert_before_closing_brace(content: str, line: str) -> str:
    """Same insert-if-absent strategy as set_shell: append just before the
    final closing brace, or at EOF if the file doesn't end with one."""
    new = content.rstrip()
    if new.endswith("}"):
        return new[:-1] + f"  {line}\n}}"
    return content + f"\n{line}\n"


def get_string_option(key: str, default: str) -> str:
    """Read a `key = "value";` line (roudix.editor, roudix.desktopIntegration...)."""
    try:
        with open(CONFIG_FILE) as f:
            for line in f:
                if key in line:
                    m = re.search(re.escape(key) + r'\s*=\s*"([^"]*)"', line)
                    if m:
                        return m.group(1)
    except Exception:
        pass
    return default


def set_string_option(key: str, value: str):
    try:
        with open(CONFIG_FILE) as f:
            content = f.read()
        pattern = re.escape(key) + r'\s*=\s*"[^"]*"'
        if re.search(pattern, content):
            new = re.sub(pattern, f'{key} = "{value}"', content)
        else:
            new = _insert_before_closing_brace(content, f'{key} = "{value}";')
        with open(CONFIG_FILE, "w") as f:
            f.write(new)
        log.info("Configuration updated: %s set to '%s'.", key, value)
        return True
    except Exception as e:
        log.error("Failed to write configuration: %s", e)
        return str(e)


def get_bool_option(key: str, default: bool, path: str = None) -> bool:
    """Read a `key = true;`/`key = false;` line (roudix.gaming.apps.*.enable...).
    `path` lets callers target a config file other than the system
    CONFIG_FILE — e.g. HOME_CONFIG_FILE for Home Manager options."""
    path = path or CONFIG_FILE
    try:
        with open(path) as f:
            for line in f:
                if key in line:
                    m = re.search(re.escape(key) + r"\s*=\s*(true|false)", line)
                    if m:
                        return m.group(1) == "true"
    except Exception:
        pass
    return default


def set_bool_option(key: str, value: bool, path: str = None):
    """Write a `key = true;`/`key = false;` line. `path` lets callers target
    a config file other than the system CONFIG_FILE (see get_bool_option)."""
    path = path or CONFIG_FILE
    try:
        with open(path) as f:
            content = f.read()
        val = "true" if value else "false"
        pattern = re.escape(key) + r"\s*=\s*(true|false)"
        if re.search(pattern, content):
            new = re.sub(pattern, f"{key} = {val}", content)
        else:
            new = _insert_before_closing_brace(content, f"{key} = {val};")
        with open(path, "w") as f:
            f.write(new)
        log.info("Configuration updated: %s set to %s.", key, val)
        return True
    except Exception as e:
        log.error("Failed to write configuration: %s", e)
        return str(e)


def get_list_option(key: str, default: list) -> list:
    """Read a `key = [ "a" "b" ];` line (roudix.browsers...)."""
    try:
        with open(CONFIG_FILE) as f:
            content = f.read()
        m = re.search(re.escape(key) + r"\s*=\s*\[([^\]]*)\]", content)
        if m:
            return re.findall(r'"([^"]*)"', m.group(1))
    except Exception:
        pass
    return default


def set_list_option(key: str, values: list):
    try:
        with open(CONFIG_FILE) as f:
            content = f.read()
        rendered = "[ " + " ".join(f'"{v}"' for v in values) + " ]" if values else "[ ]"
        pattern = re.escape(key) + r"\s*=\s*\[[^\]]*\]"
        if re.search(pattern, content):
            new = re.sub(pattern, f"{key} = {rendered}", content)
        else:
            new = _insert_before_closing_brace(content, f"{key} = {rendered};")
        with open(CONFIG_FILE, "w") as f:
            f.write(new)
        log.info("Configuration updated: %s set to %s.", key, rendered)
        return True
    except Exception as e:
        log.error("Failed to write configuration: %s", e)
        return str(e)


def _diff_bool_items(items: list, states: dict) -> dict:
    """Compare each item's current Nix value to its widget state; return
    {id: (key, new_val, name, file)} for the ones that changed. Shared by
    every checklist group (gaming apps, gaming extras, system toggles).
    Each item carries its own Nix default under "default", and may carry
    an explicit target config file under "file" (defaults to CONFIG_FILE —
    see HOME_CONFIG_FILE for Home Manager-only options like fastfetch)."""
    changes = {}
    for item in items:
        file = item.get("file", CONFIG_FILE)
        cur_val = get_bool_option(item["key"], item.get("default", False), path=file)
        new_val = states[item["id"]]
        if new_val != cur_val:
            changes[item["id"]] = (item["key"], new_val, item["name"], file)
    return changes


def set_de(de_id):
    try:
        with open(CONFIG_FILE) as f:
            content = f.read()
        new = re.sub(
            r'roudix\.desktop\.type\s*=\s*"[^"]*"',
            f'roudix.desktop.type = "{de_id}"',
            content,
        )
        with open(CONFIG_FILE, "w") as f:
            f.write(new)
        log.info("Configuration updated: desktop type set to '%s'.", de_id)
        return True
    except Exception as e:
        log.error("Failed to write configuration: %s", e)
        return str(e)


def set_shell(shell_id):
    """Write roudix.desktop.shell to config, adding the line if absent."""
    try:
        with open(CONFIG_FILE) as f:
            content = f.read()

        if re.search(r'roudix\.desktop\.shell\s*=\s*"[^"]*"', content):
            new = re.sub(
                r'roudix\.desktop\.shell\s*=\s*"[^"]*"',
                f'roudix.desktop.shell = "{shell_id}"',
                content,
            )
        else:
            # Insert after roudix.desktop.type line if present
            de_line = re.search(r'(roudix\.desktop\.type\s*=\s*"[^"]*";)', content)
            if de_line:
                new = content[:de_line.end()] + f'\n  roudix.desktop.shell = "{shell_id}";' + content[de_line.end():]
            else:
                new = content.rstrip()
                if new.endswith("}"):
                    new = new[:-1] + f'  roudix.desktop.shell = "{shell_id}";\n}}'
                else:
                    new = content + f'\n  roudix.desktop.shell = "{shell_id}";\n'

        with open(CONFIG_FILE, "w") as f:
            f.write(new)
        log.info("Configuration updated: desktop shell set to '%s'.", shell_id)
        return True
    except Exception as e:
        log.error("Failed to write configuration: %s", e)
        return str(e)


# id (as used in EDITORS/TERMINALS/FILE_MANAGERS/etc.) -> standard
# freedesktop icon name to try in the icon theme *actually active* on this
# session (Papirus, Tela, whatever roudix.iconTheme is set to — this reads
# live via Gtk.IconTheme, it doesn't care which one) before falling back to
# roudix-switcher's own bundled SVG.
#
# Deliberately NOT exhaustive: only apps I'm confident ship a real icon in
# mainstream themes belong here. Niche/branded apps most themes don't cover
# (Zen Twilight/Beta, Helium, AyuGram, Ghostty, Clapper, Fragments, Ptyxis,
# Faugus, Vintage Story, ...) are left out on purpose, so they always use
# the bundled custom SVG instead of a missed or wrong-guess lookup. Safe to
# extend: has_icon() below just no-ops (silent fallback) for any entry that
# turns out not to exist in a given theme, it never breaks anything.
APP_ICON_THEME_NAMES = {
    # Editors
    "vscode":     "code",
    "neovim":     "nvim",
    "zed":        "zed",
    # Terminals
    "kitty":      "kitty",
    "alacritty":  "Alacritty",
    "wezterm":    "org.wezfurlong.wezterm",
    "konsole":    "org.kde.konsole",
    # File managers
    "nautilus":   "org.gnome.Nautilus",
    "dolphin":    "org.kde.dolphin",
    "nemo":       "nemo",
    "thunar":     "org.xfce.thunar",
    "pcmanfm-qt": "pcmanfm-qt",
    # Matrix / chat
    "element":    "im.riot.Riot",
    "vencord":    "discord",
    "vanilla":    "discord",
    "telegram":   "telegram",
    # Video players
    "vlc":        "vlc",
    "mpv":        "mpv",
    "celluloid":  "io.github.celluloid_player.Celluloid",
    # Torrent clients
    "qbittorrent": "qbittorrent",
    "deluge":     "deluge",
}


def load_icon(icon_filename, dark, icon_theme_name=None):
    """Load icon from dark/ or light/ subfolder, fallback to theme icon.

    icon_theme_name, when given, is tried FIRST against whatever GTK icon
    theme is actually active on this session — if that theme (Papirus,
    Tela, ...) really ships this app's icon, that's what gets shown, so the
    switcher's own icons track the user's chosen theme instead of staying
    fixed art forever. Falls through to icon_filename (bundled art) the
    moment the active theme doesn't have it, silently and safely — this is
    exactly the fallback that avoids ever needing to hand-copy a theme's
    icon file into roudix-switcher for apps that DO exist in the theme
    (Brave, VLC, Dolphin, ...); only apps genuinely missing from every
    mainstream theme (Zen Twilight, AyuGram, Helium, ...) still need real,
    hand-drawn art of their own.

    If icon_filename isn't a bundled SVG (no .svg extension) and no theme
    icon matched, it's treated as a literal GTK icon-theme name instead —
    used for entries built at runtime with no dedicated artwork shipped in
    icons/, e.g. icon themes found by scan_icon_themes()."""
    if icon_theme_name:
        display = Gdk.Display.get_default()
        if display is not None:
            gtk_icon_theme = Gtk.IconTheme.get_for_display(display)
            if gtk_icon_theme.has_icon(icon_theme_name):
                img = Gtk.Image.new_from_icon_name(icon_theme_name)
                img.set_pixel_size(32)
                return img
    if os.path.isabs(icon_filename) and os.path.isfile(icon_filename):
        img = Gtk.Image.new_from_file(icon_filename)
        img.set_pixel_size(32)
        return img
    if not icon_filename.endswith(".svg"):
        img = Gtk.Image.new_from_icon_name(icon_filename)
        img.set_pixel_size(32)
        return img
    theme = "dark" if dark else "light"
    path = os.path.join(ICONS_DIR, theme, icon_filename)
    if os.path.exists(path):
        img = Gtk.Image.new_from_file(path)
    else:
        fallback = os.path.join(ICONS_DIR, icon_filename)
        if os.path.exists(fallback):
            img = Gtk.Image.new_from_file(fallback)
        else:
            # Use a generic terminal icon for shells when no dedicated icon exists
            img = Gtk.Image.new_from_icon_name("utilities-terminal-symbolic")
    img.set_pixel_size(32)
    return img


# roudix.iconTheme id -> the on-disk variant folder default.nix's preview
# packages actually install, used to find each theme's real "folder" icon.
ICON_THEME_PREVIEW_FOLDERS = {
    "papirus":  "Papirus-Dark",
    "tela":     "Tela-dark",
    "qogir":    "Qogir-dark",
    "whitesur": "WhiteSur-dark",
    "colloid":  "Colloid-dark",
}

# Where a theme's most recognizable, always-present glyph usually lives —
# checked in order, first match wins.
_FOLDER_ICON_CANDIDATES = (
    "scalable/places/folder.svg",
    "scalable/places/folder-symbolic.svg",
    "48/places/folder.svg",
    "48x48/places/folder.svg",
    "32/places/folder.svg",
    "48/places/folder.png",
)


def _theme_preview_icon(theme_dir):
    """The theme's own 'folder' icon — a live, always-accurate preview
    instead of hand-drawn placeholder art. Returns None if theme_dir
    doesn't ship one under any of the usual layouts (uncommon, but not
    every theme follows convention), in which case callers fall back to
    a bundled placeholder or a generic symbolic icon."""
    for rel in _FOLDER_ICON_CANDIDATES:
        path = os.path.join(theme_dir, rel)
        if os.path.isfile(path):
            return path
    return None


def curated_icon_theme_preview(theme_id):
    """Real preview for one of Roudix's curated ids (ICON_THEME_PREVIEW_FOLDERS),
    searched across ROUDIX_ICON_THEME_PREVIEW_PATH (set by default.nix from
    the actual nixpkgs icon-theme packages). None outside the Nix build —
    e.g. running this script directly for testing — where callers keep
    ICON_THEMES' bundled placeholder SVG instead."""
    folder = ICON_THEME_PREVIEW_FOLDERS.get(theme_id)
    if not folder:
        return None
    for root in os.environ.get("ROUDIX_ICON_THEME_PREVIEW_PATH", "").split(":"):
        if not root:
            continue
        preview = _theme_preview_icon(os.path.join(root, folder))
        if preview:
            return preview
    return None


def _icon_theme_search_dirs():
    """Where GTK/dconf-consuming apps actually look for icon themes:
    every icons/ dir on XDG_DATA_DIRS (covers the system profile and the
    home-manager per-user profile on NixOS) plus ~/.local/share/icons and
    ~/.icons — the latter isn't always on XDG_DATA_DIRS but GTK always
    checks it directly, and it's where tela-icon.nix drops its
    Noctalia-recolored variants."""
    dirs = []
    xdg_data_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
    for base in xdg_data_dirs.split(":"):
        if base:
            dirs.append(os.path.join(base, "icons"))
    xdg_data_home = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    dirs.append(os.path.join(xdg_data_home, "icons"))
    dirs.append(os.path.expanduser("~/.icons"))
    return dirs


def scan_icon_themes():
    """Find icon themes installed beyond Roudix's curated set (ICON_THEMES)
    — a nixpkgs package the user added themselves in modules/home/local.nix,
    or a theme dropped by hand into ~/.icons.

    Safety: this only ever returns a plain theme *name* (the folder's own
    name) for display and, if picked, for roudix.iconTheme — never a Nix
    package reference. gtk-theme.nix treats any name outside its curated
    ids as a literal string with no package to install, so a scanned pick
    can't inject anything into local.nix or break a rebuild — an
    invalid/incomplete theme just falls back to hicolor icons at runtime,
    exactly like a typo in a manual mkForce override would.
    """
    found = {}
    for base in _icon_theme_search_dirs():
        if not os.path.isdir(base):
            continue
        try:
            entries = sorted(os.listdir(base))
        except OSError:
            continue
        for entry in entries:
            if entry in found or entry in KNOWN_ICON_THEME_IDS:
                continue
            if entry.lower() in ("hicolor", "default", "locolor"):
                continue
            # A raw " or newline in a folder name would break the Nix
            # string literal roudix-switcher writes — reject rather than
            # risk it, even though real icon themes never do this.
            if '"' in entry or "\n" in entry:
                continue
            index_path = os.path.join(base, entry, "index.theme")
            if not os.path.isfile(index_path):
                continue
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                parser.read(index_path, encoding="utf-8")
            except (OSError, configparser.Error, UnicodeDecodeError):
                continue
            if not parser.has_section("Icon Theme"):
                continue
            # No app-icon directories declared: it's a cursor theme or
            # similarly unusable as a GTK icon theme, not a real pick.
            if not parser.get("Icon Theme", "Directories", fallback="").strip():
                continue
            display_name = parser.get("Icon Theme", "Name", fallback=entry).strip() or entry
            theme_dir = os.path.join(base, entry)
            preview = _theme_preview_icon(theme_dir)
            found[entry] = {
                "id": entry,
                "name": display_name,
                "subtitle": base,
                "icon": preview or "preferences-desktop-theme-symbolic",
            }
    return sorted(found.values(), key=lambda t: t["name"].lower())


# ── Reusable selector widget ──────────────────────────────────────────────────

class SelectorGroup(Gtk.Box):
    """
    A labelled ListBox of radio-like rows.
    items   — list of dicts with keys: id, name, subtitle, icon
    current — currently selected id
    dark    — whether the theme is dark (for icon loading)
    """

    def __init__(self, title: str, items: list, current: str, dark: bool):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        label = Gtk.Label()
        label.set_markup(f"<b>{title}</b>")
        label.set_halign(Gtk.Align.START)
        self.append(label)

        self.selected_id = current
        self.icon_widgets: dict[str, tuple] = {}
        self.rows: dict[str, Gtk.CheckButton] = {}
        self._dark = dark
        self._row_widgets: dict[str, Adw.ActionRow] = {}

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.add_css_class("boxed-list")
        self.append(self.list_box)

        for item in items:
            self._append_item(item)

    def _append_item(self, item: dict):
        row = Adw.ActionRow()
        row.set_title(item["name"])
        row.set_subtitle(item["subtitle"])

        icon = load_icon(item["icon"], self._dark, APP_ICON_THEME_NAMES.get(item["id"]))
        self.icon_widgets[item["id"]] = (icon, item["icon"])
        row.add_prefix(icon)

        if item.get("disabled"):
            row.set_sensitive(False)
        else:
            check = Gtk.CheckButton()
            check.set_valign(Gtk.Align.CENTER)
            if item["id"] == self.selected_id:
                check.set_active(True)
            check.connect("toggled", self._on_toggled, item["id"])
            row.add_suffix(check)
            self.rows[item["id"]] = check

        self._row_widgets[item["id"]] = row
        self.list_box.append(row)

    def add_item(self, item: dict):
        """Append a new item row (e.g. caelestia) if not already present."""
        if item["id"] not in self._row_widgets:
            self._append_item(item)

    def remove_item(self, item_id: str):
        """Remove a row by id. If it was selected, fall back to the first row."""
        row = self._row_widgets.pop(item_id, None)
        if row is None:
            return
        self.list_box.remove(row)
        self.icon_widgets.pop(item_id, None)
        self.rows.pop(item_id, None)
        # If the removed item was selected, select the first available
        if self.selected_id == item_id:
            first = next(iter(self.rows), None)
            if first:
                self.rows[first].set_active(True)
                self.selected_id = first

    def sync_items(self, items: list):
        """Reconcile displayed rows with the given item list (add missing, remove extras)."""
        wanted_ids = [item["id"] for item in items]

        # Remove rows that should no longer appear
        for existing_id in list(self._row_widgets.keys()):
            if existing_id not in wanted_ids:
                self.remove_item(existing_id)

        # Add missing rows
        for item in items:
            if item["id"] not in self._row_widgets:
                self.add_item(item)

        # Safety net: if the current selection is no longer valid
        if self.selected_id not in wanted_ids and wanted_ids:
            first = wanted_ids[0]
            if first in self.rows:
                self.rows[first].set_active(True)
                self.selected_id = first

    def _on_toggled(self, check, item_id):
        if check.get_active():
            self.selected_id = item_id
            for key, other in self.rows.items():
                if key != item_id:
                    other.handler_block_by_func(self._on_toggled)
                    other.set_active(False)
                    other.handler_unblock_by_func(self._on_toggled)

    def update_icons(self, dark: bool):
        self._dark = dark
        theme = "dark" if dark else "light"
        for env_id, (img_widget, icon_filename) in self.icon_widgets.items():
            path = os.path.join(ICONS_DIR, theme, icon_filename)
            if os.path.exists(path):
                img_widget.set_from_file(path)
            else:
                fallback = os.path.join(ICONS_DIR, icon_filename)
                if os.path.exists(fallback):
                    img_widget.set_from_file(fallback)


class ToggleListGroup(Gtk.Box):
    """List of independent on/off switches (not mutually exclusive) — used
    for the gaming apps checklist. Unlike SelectorGroup, any number of items
    can be active at once."""

    def __init__(self, title: str, items: list, current: dict):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        if title:
            label = Gtk.Label()
            label.set_markup(f"<b>{title}</b>")
            label.set_halign(Gtk.Align.START)
            self.append(label)

        self.switches: dict[str, Gtk.Switch] = {}

        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.add_css_class("boxed-list")
        self.append(list_box)

        for item in items:
            row = Adw.ActionRow()
            row.set_title(item["name"])
            sw = Gtk.Switch()
            sw.set_valign(Gtk.Align.CENTER)
            sw.set_active(current.get(item["id"], True))
            row.add_suffix(sw)
            row.set_activatable_widget(sw)
            self.switches[item["id"]] = sw
            list_box.append(row)

    def get_states(self) -> dict:
        return {item_id: sw.get_active() for item_id, sw in self.switches.items()}

    def set_states(self, states: dict):
        """Refresh every switch from a fresh {id: bool} dict — used when the
        underlying Nix list changes source (e.g. Zen mods vs zen.sine.mods
        depending on the Sine toggle)."""
        for item_id, sw in self.switches.items():
            sw.set_active(states.get(item_id, False))


# ── Main window ───────────────────────────────────────────────────────────────

class RoudixSwitcherWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title(L("Roudix — Personnalisation", "Roudix — Customizer"))
        self.set_default_size(760, 640)
        self.set_resizable(True)

        # Force an opaque background on the content area: on some
        # compositors (Hyprland/niri blur-behind, etc.), a semantic CSS
        # class like "view" isn't always enough to stop the desktop's blur
        # from showing through behind a short page (few options = a large
        # "empty" area under the content). So we force an explicit
        # background-color via a dedicated provider, using the window's
        # real background color (@window_bg_color) to stay consistent in
        # both light and dark mode.
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(
            b".roudix-content-bg { background-color: @window_bg_color; }"
        )
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        current_de    = get_current_de()
        current_shell = get_current_shell()
        log.info("Current desktop environment: %s", current_de)
        log.info("Current shell: %s", current_shell)

        # ── Style manager ─────────────────────────────────────────────────
        self.style_manager = Adw.StyleManager.get_default()
        self.style_manager.connect("notify::dark", self.on_theme_changed)
        dark = self.style_manager.get_dark()

        # ── Main layout ───────────────────────────────────────────────────
        toolbar = Adw.ToolbarView()
        self.set_content(toolbar)

        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(920)
        clamp.set_tightening_threshold(600)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)

        # ── Description ───────────────────────────────────────────────────
        desc = Gtk.Label()
        desc.set_markup(
            L(
                "<b>Personnalise ton Roudix</b>\n"
                "<span size='small'>Choisis ton bureau, ton shell et tes réglages ci-dessous.\n"
                "Le système reconstruira après ta sélection — ça peut prendre quelques minutes.</span>",
                "<b>Customize your Roudix</b>\n"
                "<span size='small'>Pick your desktop, shell and tweaks below.\n"
                "The system will rebuild after your selection — this may take a few minutes.</span>",
            )
        )
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_wrap(True)
        main_box.append(desc)

        # ── Sidebar (categories) + content pages ────────────────────────────
        # Layout inspired by a "GLF Customizer"-style preferences panel:
        # a category list on the left, the selected category's detail on
        # the right. Each page stays faithful to the underlying Nix
        # option's real shape (single-choice list for an enum, independent
        # switches for a set of booleans) rather than forcing everything
        # into checkboxes.
        split_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        split_row.set_vexpand(True)

        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar_box.set_size_request(190, -1)

        self.category_list = Gtk.ListBox()
        self.category_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.category_list.add_css_class("navigation-sidebar")
        self.category_list.set_vexpand(True)

        CATEGORIES = [
            ("desktop",     L("Bureau", "Desktop")),
            ("gaming",      "Gaming"),
            ("content_creation", L("Création de contenu", "Content Creation")),
            ("editor",      L("Éditeur", "Editor")),
            ("terminal",    "Terminal"),
            ("browser",     L("Navigateur", "Browser")),
            ("login_shell", L("Shell de connexion", "Login Shell")),
            ("filemanager", L("Gestionnaire de fichiers", "File Manager")),
            ("chat",        L("Client de chat", "Chat Client")),
            ("system",      L("Système", "System")),
            ("integration", L("Intégration", "Integration")),
            ("icon_theme", L("Thème d'icônes", "Icon Theme")),
        ]
        self._category_rows = {}
        for cat_id, cat_name in CATEGORIES:
            row = Gtk.ListBoxRow()
            row_label = Gtk.Label(label=cat_name, halign=Gtk.Align.START)
            row_label.set_margin_start(10)
            row_label.set_margin_top(8)
            row_label.set_margin_bottom(8)
            row.set_child(row_label)
            row.category_id = cat_id
            self._category_rows[cat_id] = row
            self.category_list.append(row)

        sidebar_box.append(self.category_list)

        # Only "Gaming" has a real notion of "N/M enabled" (packages that
        # get installed or not) — the other categories are exclusive
        # choices with no honest equivalent to that counter.
        self.gaming_counter_label = Gtk.Label(xalign=0)
        self.gaming_counter_label.add_css_class("dim-label")
        self.gaming_counter_label.set_margin_start(10)
        self.gaming_counter_label.set_margin_top(6)
        self.gaming_counter_label.set_margin_bottom(10)
        sidebar_box.append(self.gaming_counter_label)

        split_row.append(sidebar_box)
        split_row.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        self.content_stack = Gtk.Stack()
        self.content_stack.set_hexpand(True)
        self.content_stack.set_valign(Gtk.Align.START)
        # Without this (vhomogeneous default = True), the Stack always
        # requests the height of its TALLEST page (System, the longest),
        # even while showing Login Shell — which would cancel out the
        # shrinking wanted below.
        self.content_stack.set_vhomogeneous(False)
        # CROSSFADE forces the Stack to keep, for the duration of the
        # transition, a size equal to the MAX of both pages (old + new) —
        # and on some GTK4 versions this "inflated" size stays stuck after
        # the transition instead of shrinking back to the displayed page's
        # real height. That's what creates the large empty area under a
        # short page (Browser, Gaming...) after coming from a longer page
        # (System). NONE avoids the problem entirely: each page is
        # measured on its own, never retaining a previous page's size.
        self.content_stack.set_transition_type(Gtk.StackTransitionType.NONE)

        content_scroll = Gtk.ScrolledWindow()
        content_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content_scroll.set_hexpand(True)
        # Fill all the vertical space actually available in the window
        # (like the sidebar right next to it) instead of an arbitrary
        # fixed cap (480px): on a resized/maximized window, that cap left
        # a large unfilled gap below the whole panel. With vexpand + FILL,
        # the panel (sidebar + options) uses all available height;
        # AUTOMATIC only shows a scrollbar if a page's content exceeds
        # that height.
        content_scroll.set_vexpand(True)
        content_scroll.set_valign(Gtk.Align.FILL)
        # Opaque theme background, so the area under a short page doesn't
        # let the window's blurred background show through.
        content_scroll.add_css_class("roudix-content-bg")
        content_scroll.set_child(self.content_stack)
        split_row.append(content_scroll)
        self.content_scroll = content_scroll

        main_box.append(split_row)

        # ── "Desktop" page: DE + shell ───────────────────────────────────
        desktop_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        desktop_page.set_margin_top(4)
        desktop_page.set_margin_start(16)
        desktop_page.set_margin_end(16)
        desktop_page.set_margin_bottom(16)

        self.de_selector = SelectorGroup(
            L("Environnement de bureau", "Desktop environment"),
            ENVIRONMENTS,
            current_de,
            dark,
        )
        for de_id, check in self.de_selector.rows.items():
            check.connect("toggled", self._on_de_toggled)
        desktop_page.append(self.de_selector)

        initial_shells = shells_for_de(current_de)
        if current_shell not in {s["id"] for s in initial_shells}:
            current_shell = "noctalia"

        self.shell_selector = SelectorGroup(
            L("Shell graphique", "Graphical shell"),
            initial_shells,
            current_shell,
            dark,
        )
        self.shell_selector.set_visible(current_de in SHELL_SUPPORTED_DE)
        desktop_page.append(self.shell_selector)

        # roudix.umbriel.scratchpadApps (modules/system/desktop/umbriel.nix) —
        # Umbriel only: toggles chat/Spotify apps between fixed tiling
        # (false, default) and named scratchpads (true).
        self.scratchpad_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.scratchpad_row.set_margin_top(8)
        scratchpad_label = Gtk.Label(label=L("Apps en scratchpad (Umbriel)", "Umbriel scratchpad apps"), halign=Gtk.Align.START)
        scratchpad_label.set_hexpand(True)
        self.scratchpad_switch = Gtk.Switch()
        self.scratchpad_switch.set_valign(Gtk.Align.CENTER)
        self.scratchpad_switch.set_active(get_bool_option("roudix.umbriel.scratchpadApps", False))
        self.scratchpad_row.append(scratchpad_label)
        self.scratchpad_row.append(self.scratchpad_switch)
        self.scratchpad_row.set_visible(current_de in UMBRIEL_SUPPORTED_DE)
        desktop_page.append(self.scratchpad_row)

        self.scratchpad_note = Gtk.Label(
            label=L(
                "Umbriel uniquement — Discord/Telegram et Spotify vivent dans des "
                "scratchpads nommés (affichés/masqués via un raccourci) au lieu de "
                "rester tuilés sur une sortie/espace de travail fixe.",
                "Umbriel only — Discord/Telegram and Spotify live in named "
                "scratchpads (shown/hidden with a shortcut) instead of "
                "staying tiled on a fixed output/workspace.",
            ),
        )
        self.scratchpad_note.add_css_class("dim-label")
        self.scratchpad_note.set_wrap(True)
        self.scratchpad_note.set_halign(Gtk.Align.START)
        self.scratchpad_note.set_visible(current_de in UMBRIEL_SUPPORTED_DE)
        desktop_page.append(self.scratchpad_note)

        self.content_stack.add_named(desktop_page, "desktop")

        # ── "Gaming" page: master switch + apps checklist ─────────────────
        gaming_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        gaming_page.set_margin_top(4)
        gaming_page.set_margin_start(16)
        gaming_page.set_margin_end(16)
        gaming_page.set_margin_bottom(16)

        gaming_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        gaming_title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        gtitle = Gtk.Label(label="Gaming", halign=Gtk.Align.START)
        gtitle.add_css_class("title-2")
        gsubtitle = Gtk.Label(
            label=L("Lanceurs et outils installés pour le gaming.", "Launchers and tools installed for gaming."),
            halign=Gtk.Align.START,
        )
        gsubtitle.add_css_class("dim-label")
        gaming_title_box.append(gtitle)
        gaming_title_box.append(gsubtitle)
        gaming_title_box.set_hexpand(True)
        gaming_header.append(gaming_title_box)

        cur_gaming_master = get_bool_option("roudix.gaming.enable", True)
        self.gaming_master_switch = Gtk.Switch()
        self.gaming_master_switch.set_valign(Gtk.Align.CENTER)
        self.gaming_master_switch.set_active(cur_gaming_master)
        gaming_header.append(self.gaming_master_switch)
        gaming_page.append(gaming_header)
        gaming_page.append(Gtk.Separator())

        gaming_current = {app["id"]: get_bool_option(app["key"], app["default"]) for app in GAMING_APPS}
        self.gaming_apps_group = ToggleListGroup("", GAMING_APPS, gaming_current)
        self.gaming_apps_group.set_sensitive(cur_gaming_master)
        gaming_page.append(self.gaming_apps_group)

        extras_label = Gtk.Label(halign=Gtk.Align.START)
        extras_label.set_markup("<b>Tweaks</b>")
        extras_label.set_margin_top(8)
        gaming_page.append(extras_label)
        gaming_extras_current = {e["id"]: get_bool_option(e["key"], e["default"]) for e in GAMING_EXTRAS}
        self.gaming_extras_group = ToggleListGroup("", GAMING_EXTRAS, gaming_extras_current)
        gaming_page.append(self.gaming_extras_group)

        self.gaming_master_switch.connect("notify::active", self._on_gaming_master_toggled)
        for sw in self.gaming_apps_group.switches.values():
            sw.connect("notify::active", lambda *_: self._update_gaming_counter())

        self.content_stack.add_named(gaming_page, "gaming")

        # ── "Content Creation" page: OBS + plugins + video editor + extras ──
        cc_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        cc_page.set_margin_top(4)
        cc_page.set_margin_start(16)
        cc_page.set_margin_end(16)
        cc_page.set_margin_bottom(16)

        cc_master_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cc_master_label = Gtk.Label(label=L("Création de contenu", "Content Creation"), halign=Gtk.Align.START)
        cc_master_label.set_hexpand(True)
        self.cc_master_switch = Gtk.Switch()
        self.cc_master_switch.set_valign(Gtk.Align.CENTER)
        self.cc_master_switch.set_active(get_bool_option("roudix.contentCreation.enable", True))
        cc_master_row.append(cc_master_label)
        cc_master_row.append(self.cc_master_switch)
        cc_page.append(cc_master_row)

        cc_current = {t["id"]: get_bool_option(t["key"], t["default"]) for t in CONTENT_CREATION_TOGGLES}
        self.cc_group = ToggleListGroup("", CONTENT_CREATION_TOGGLES, cc_current)
        cc_page.append(self.cc_group)

        current_obs_plugins = {p["id"]: get_bool_option(p["key"], p["default"]) for p in OBS_PLUGINS}
        self.obs_plugins_group = ToggleListGroup(L("Plugins OBS", "OBS plugins"), OBS_PLUGINS, current_obs_plugins)
        cc_page.append(self.obs_plugins_group)

        current_video_editor = get_string_option("roudix.contentCreation.videoEditor", "kdenlive")
        self.video_editor_selector = SelectorGroup(L("Éditeur vidéo", "Video editor"), VIDEO_EDITORS, current_video_editor, dark)
        cc_page.append(self.video_editor_selector)

        def _update_cc_cascade(*_):
            active = self.cc_master_switch.get_active()
            self.cc_group.set_sensitive(active)
            self.obs_plugins_group.set_sensitive(active)
            self.video_editor_selector.set_sensitive(active)

        self.cc_master_switch.connect("notify::active", _update_cc_cascade)
        _update_cc_cascade()

        self.content_stack.add_named(cc_page, "content_creation")

        # ── "Editor" page ──────────────────────────────────────────────────
        editor_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        editor_page.set_margin_top(4)
        editor_page.set_margin_start(16)
        editor_page.set_margin_end(16)
        editor_page.set_margin_bottom(16)

        current_editor = get_string_option("roudix.editor", "zed")
        self.editor_selector = SelectorGroup(L("Éditeur par défaut", "Default editor"), EDITORS, current_editor, dark)
        editor_page.append(self.editor_selector)

        self.content_stack.add_named(editor_page, "editor")

        # ── "Terminal" page ─────────────────────────────────────────────────
        terminal_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        terminal_page.set_margin_top(4)
        terminal_page.set_margin_start(16)
        terminal_page.set_margin_end(16)
        terminal_page.set_margin_bottom(16)

        current_terminal = get_string_option("roudix.terminal", "ghostty")
        self.terminal_selector = SelectorGroup(L("Terminal par défaut", "Default terminal"), TERMINALS, current_terminal, dark)
        terminal_page.append(self.terminal_selector)

        self.content_stack.add_named(terminal_page, "terminal")

        # ── "Browser" page: checklist (roudix.browsers is a list) ──────────
        browser_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        browser_page.set_margin_top(4)
        browser_page.set_margin_start(16)
        browser_page.set_margin_end(16)
        browser_page.set_margin_bottom(16)

        btitle = Gtk.Label(label=L("Navigateur", "Browser"), halign=Gtk.Align.START)
        btitle.add_css_class("title-2")
        bsubtitle = Gtk.Label(
            label=L(
                "Coche-en autant que tu veux — le premier coché ci-dessous devient "
                "le défaut (raccourci MOD+B de niri).",
                "Pick any number — the first one checked below becomes the "
                "default (niri's MOD+B shortcut).",
            ),
            halign=Gtk.Align.START,
        )
        bsubtitle.add_css_class("dim-label")
        bsubtitle.set_wrap(True)
        browser_page.append(btitle)
        browser_page.append(bsubtitle)
        browser_page.append(Gtk.Separator())

        current_browsers = set(get_list_option("roudix.browsers", ["brave"]))
        browser_current = {b["id"]: (b["id"] in current_browsers) for b in BROWSERS}
        self.browser_group = ToggleListGroup("", BROWSERS, browser_current)
        browser_page.append(self.browser_group)

        # Zen Browser lives separately on the Nix side (its own flake
        # input, not in browserDefs): an enable switch + a mod-loader
        # choice (native vs Sine, mutually exclusive on the Nix side) + a
        # mods checklist that reads/writes roudix.zen.mods or
        # roudix.zen.sine.mods depending on the Sine switch state. The
        # Sine switch only makes sense if Zen is enabled, and the mods
        # checklist only if Sine is too — so the three are chained in
        # cascade rather than always visible.
        zen_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        zen_row.set_margin_top(8)
        zen_label = Gtk.Label(label="Zen Browser", halign=Gtk.Align.START)
        zen_label.set_hexpand(True)
        self.zen_switch = Gtk.Switch()
        self.zen_switch.set_valign(Gtk.Align.CENTER)
        self.zen_switch.set_active(get_bool_option("roudix.zen.enable", False))
        zen_row.append(zen_label)
        zen_row.append(self.zen_switch)
        browser_page.append(zen_row)

        current_zen_variant = get_string_option("roudix.zen.variant", "twilight")
        self.zen_variant_selector = SelectorGroup(L("Canal Zen", "Zen channel"), ZEN_VARIANTS, current_zen_variant, dark)
        browser_page.append(self.zen_variant_selector)

        self.sine_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sine_label = Gtk.Label(label=L("Chargeur de mods Sine", "Sine mod loader"), halign=Gtk.Align.START)
        sine_label.set_hexpand(True)
        self.sine_switch = Gtk.Switch()
        self.sine_switch.set_valign(Gtk.Align.CENTER)
        current_sine = get_bool_option("roudix.zen.sine.enable", False)
        self.sine_switch.set_active(current_sine)
        self.sine_row.append(sine_label)
        self.sine_row.append(self.sine_switch)
        browser_page.append(self.sine_row)

        self.sine_note = Gtk.Label(
            label=L(
                "Les mods natifs Zen et les mods Sine ne peuvent pas être actifs en "
                "même temps — la liste ci-dessous cible toujours celui qui est activé.",
                "Native Zen mods and Sine mods can't be active at the same "
                "time — the list below always targets whichever is on.",
            ),
        )
        self.sine_note.add_css_class("dim-label")
        self.sine_note.set_wrap(True)
        self.sine_note.set_halign(Gtk.Align.START)
        browser_page.append(self.sine_note)

        zen_mods_current_ids = set(
            get_list_option("roudix.zen.sine.mods" if current_sine else "roudix.zen.mods", [])
        )
        zen_mods_current = {m["id"]: (m["id"] in zen_mods_current_ids) for m in ZEN_MODS}
        self.zen_mods_group = ToggleListGroup(L("Mods", "Mods"), ZEN_MODS, zen_mods_current)
        browser_page.append(self.zen_mods_group)

        self.zen_mods_placeholder = None
        if not ZEN_MODS:
            self.zen_mods_placeholder = Gtk.Label(
                label=L(
                    "Aucun mod listé pour l'instant — ajoute tes IDs de mods à ZEN_MODS dans le script.",
                    "No mods listed yet — add your mod IDs to ZEN_MODS in the script.",
                ),
            )
            self.zen_mods_placeholder.add_css_class("dim-label")
            self.zen_mods_placeholder.set_halign(Gtk.Align.START)
            browser_page.append(self.zen_mods_placeholder)

        def _update_zen_cascade(*_):
            zen_on = self.zen_switch.get_active()
            sine_on = self.sine_switch.get_active()
            self.zen_variant_selector.set_visible(zen_on)
            self.sine_row.set_visible(zen_on)
            show_mods = zen_on and sine_on
            self.sine_note.set_visible(show_mods)
            self.zen_mods_group.set_visible(show_mods)
            if self.zen_mods_placeholder is not None:
                self.zen_mods_placeholder.set_visible(show_mods)

        def _on_sine_toggled(sw, _param):
            is_sine = sw.get_active()
            ids = set(get_list_option("roudix.zen.sine.mods" if is_sine else "roudix.zen.mods", []))
            self.zen_mods_group.set_states({m["id"]: (m["id"] in ids) for m in ZEN_MODS})
            _update_zen_cascade()

        self.zen_switch.connect("notify::active", _update_zen_cascade)
        self.sine_switch.connect("notify::active", _on_sine_toggled)
        _update_zen_cascade()

        self.content_stack.add_named(browser_page, "browser")

        # ── "Login Shell" page ──────────────────────────────────────────────
        login_shell_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        login_shell_page.set_margin_top(4)
        login_shell_page.set_margin_start(16)
        login_shell_page.set_margin_end(16)
        login_shell_page.set_margin_bottom(16)

        current_login_shell = get_string_option("roudix.shell", "fish")
        self.login_shell_selector = SelectorGroup(L("Shell de connexion", "Login shell"), LOGIN_SHELLS, current_login_shell, dark)
        login_shell_page.append(self.login_shell_selector)

        login_shell_note = Gtk.Label(
            label=L(
                "C'est le shell de connexion de ton terminal — pas le shell graphique "
                "de la page Bureau (noctalia/dms/caelestia).",
                "This is your terminal login shell — not the graphical shell "
                "under Desktop (noctalia/dms/caelestia).",
            ),
        )
        login_shell_note.add_css_class("dim-label")
        login_shell_note.set_wrap(True)
        login_shell_note.set_halign(Gtk.Align.START)
        login_shell_page.append(login_shell_note)

        self.content_stack.add_named(login_shell_page, "login_shell")

        # ── "File Manager" page (niri/hyprland/mangowc/umbriel only) ───────
        filemanager_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        filemanager_page.set_margin_top(4)
        filemanager_page.set_margin_start(16)
        filemanager_page.set_margin_end(16)
        filemanager_page.set_margin_bottom(16)

        current_filemanager = get_string_option("roudix.fileManager", "nautilus")
        self.filemanager_selector = SelectorGroup(L("Gestionnaire de fichiers", "File manager"), FILE_MANAGERS, current_filemanager, dark)
        filemanager_page.append(self.filemanager_selector)

        self.content_stack.add_named(filemanager_page, "filemanager")

        # ── "Chat Client" page ──────────────────────────────────────────────
        chat_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        chat_page.set_margin_top(4)
        chat_page.set_margin_start(16)
        chat_page.set_margin_end(16)
        chat_page.set_margin_bottom(16)

        current_matrix = get_string_option("roudix.matrixClient", "element")
        self.matrix_selector = SelectorGroup(L("Client Matrix", "Matrix client"), MATRIX_CLIENTS, current_matrix, dark)
        chat_page.append(self.matrix_selector)

        current_discord = get_string_option("roudix.discord", "vencord")
        self.discord_selector = SelectorGroup("Discord", DISCORD_OPTIONS, current_discord, dark)
        chat_page.append(self.discord_selector)

        current_telegram = get_string_option("roudix.telegram", "none")
        self.telegram_selector = SelectorGroup("Telegram", TELEGRAM_OPTIONS, current_telegram, dark)
        chat_page.append(self.telegram_selector)

        self.content_stack.add_named(chat_page, "chat")

        # ── "System" page: independent toggles + RGB backend ───────────────
        system_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        system_page.set_margin_top(4)
        system_page.set_margin_start(16)
        system_page.set_margin_end(16)
        system_page.set_margin_bottom(16)

        # roudix.undervolt.only-amd.enable (undervolt.nix) sets
        # amdgpu.ppfeaturemask, irrelevant on Nvidia/Intel — no point
        # showing this switch on a machine where hardware.myGpu isn't
        # "amd"/"amd-legacy" (see hosts/roudix/local.nix).
        current_gpu = get_string_option("hardware.myGpu", "amd")
        self.system_toggles = [
            t for t in SYSTEM_TOGGLES
            if t["id"] != "undervoltAmd" or current_gpu in ("amd", "amd-legacy")
        ]
        system_current = {
            t["id"]: get_bool_option(t["key"], t["default"], path=t.get("file", CONFIG_FILE))
            for t in self.system_toggles
        }
        self.system_group = ToggleListGroup(L("Interrupteurs", "Toggles"), self.system_toggles, system_current)
        system_page.append(self.system_group)

        current_rgb = get_string_option("roudix.rgb", "none")
        self.rgb_selector = SelectorGroup(L("Backend RGB", "RGB backend"), RGB_BACKENDS, current_rgb, dark)
        system_page.append(self.rgb_selector)

        current_video_player = get_string_option("roudix.videoPlayer", "vlc")
        self.video_player_selector = SelectorGroup(L("Lecteur vidéo", "Video player"), VIDEO_PLAYERS, current_video_player, dark)
        system_page.append(self.video_player_selector)

        current_torrent_client = get_string_option("roudix.torrentClient", "none")
        self.torrent_client_selector = SelectorGroup(L("Client torrent", "Torrent client"), TORRENT_CLIENTS, current_torrent_client, dark)
        system_page.append(self.torrent_client_selector)

        self.content_stack.add_named(system_page, "system")

        # ── "Integration" page: keyring/portal backend ─────────────────────
        integration_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        integration_page.set_margin_top(4)
        integration_page.set_margin_start(16)
        integration_page.set_margin_end(16)
        integration_page.set_margin_bottom(16)

        current_integration = get_string_option("roudix.desktopIntegration", "gnome")
        self.integration_selector = SelectorGroup(
            L("Backend keyring et portail", "Keyring & portal backend"),
            DESKTOP_INTEGRATIONS,
            current_integration,
            dark,
        )
        integration_page.append(self.integration_selector)

        integration_note = Gtk.Label(
            label=L(
                "S'applique uniquement à niri, Hyprland, MangoWC et Umbriel — "
                "GNOME et KDE gardent toujours leur propre stack native.",
                "Only applies to niri, Hyprland, MangoWC and Umbriel — "
                "GNOME and KDE always keep their own native stack.",
            ),
        )
        integration_note.add_css_class("dim-label")
        integration_note.set_wrap(True)
        integration_note.set_halign(Gtk.Align.START)
        integration_page.append(integration_note)

        self.content_stack.add_named(integration_page, "integration")

        # ── "Icon Theme" page: Papirus vs Tela (bare compositors only) ─────
        icon_theme_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        icon_theme_page.set_margin_top(4)
        icon_theme_page.set_margin_start(16)
        icon_theme_page.set_margin_end(16)
        icon_theme_page.set_margin_bottom(16)

        current_icon_theme = get_string_option("roudix.iconTheme", "papirus")
        # Scanned once per app launch, not on every redraw — icon themes
        # don't appear/disappear mid-session, and re-walking the icon dirs
        # on each toggle would just be wasted I/O.
        detected_icon_themes = scan_icon_themes()
        curated_icon_themes = []
        for item in ICON_THEMES:
            preview = curated_icon_theme_preview(item["id"])
            entry = dict(item)
            if preview:
                entry["icon"] = preview  # real folder glyph, not placeholder art
            curated_icon_themes.append(entry)
        self.icon_theme_selector = SelectorGroup(
            L("Thème d'icônes", "Icon theme"),
            curated_icon_themes + detected_icon_themes,
            current_icon_theme,
            dark,
        )
        icon_theme_page.append(self.icon_theme_selector)

        if detected_icon_themes:
            detected_note = Gtk.Label(
                label=L(
                    f"{len(detected_icon_themes)} thème(s) supplémentaire(s) détecté(s) sur le système "
                    "(paquet ajouté à la main, ou posé dans ~/.icons).",
                    f"{len(detected_icon_themes)} additional theme(s) detected on the system "
                    "(a package you added by hand, or dropped into ~/.icons).",
                ),
            )
            detected_note.add_css_class("dim-label")
            detected_note.set_wrap(True)
            detected_note.set_halign(Gtk.Align.START)
            icon_theme_page.append(detected_note)

        icon_theme_note = Gtk.Label(
            label=L(
                "S'applique uniquement à niri, Hyprland, MangoWC et Umbriel — "
                "GNOME et KDE gardent leur propre sélecteur d'icônes natif. "
                "Avec Tela, la première recoloration se fait au prochain "
                "changement de thème/accent Noctalia.",
                "Only applies to niri, Hyprland, MangoWC and Umbriel — "
                "GNOME and KDE keep their own native icon picker. With Tela, "
                "the first recolor happens on the next Noctalia theme/accent "
                "change.",
            ),
        )
        icon_theme_note.add_css_class("dim-label")
        icon_theme_note.set_wrap(True)
        icon_theme_note.set_halign(Gtk.Align.START)
        icon_theme_page.append(icon_theme_note)

        self.content_stack.add_named(icon_theme_page, "icon_theme")

        self.content_stack.set_visible_child_name("desktop")
        self.category_list.select_row(self._category_rows["desktop"])
        self.category_list.connect("row-selected", self._on_category_selected)

        self._update_gaming_counter()
        self._update_integration_visibility(current_de)
        self._update_filemanager_visibility(current_de)
        self._update_icon_theme_visibility(current_de)

        # ── Integrated terminal ───────────────────────────────────────────
        # Hidden by default: while no rebuild is running, this frame is
        # useless and just reserves space unnecessarily below the options
        # (the empty block you'd otherwise see). It's only revealed once a
        # rebuild actually starts (see on_apply).
        self.term_frame = Gtk.Frame()
        self.term_frame.add_css_class("card")
        self.term_frame.set_visible(False)
        term_frame = self.term_frame

        term_scroll = Gtk.ScrolledWindow()
        term_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        term_scroll.set_size_request(-1, 180)
        term_scroll.set_vexpand(False)

        self.term_view = Gtk.TextView()
        self.term_view.set_editable(False)
        self.term_view.set_cursor_visible(False)
        self.term_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.term_view.set_monospace(True)
        self.term_view.set_left_margin(10)
        self.term_view.set_right_margin(10)
        self.term_view.set_top_margin(8)
        self.term_view.set_bottom_margin(8)

        # Dark terminal background via CSS
        # No custom CSS — inherit theme colors (follows dynamic accent/wallpaper)
        self.term_view.add_css_class("card")

        self.term_buf = self.term_view.get_buffer()

        # Text tags for coloured output
        self.tag_section  = self.term_buf.create_tag("section",  foreground="#5e81ac", weight=Pango.Weight.BOLD)
        self.tag_info     = self.term_buf.create_tag("info",     foreground="#c8c8c8")
        self.tag_ok       = self.term_buf.create_tag("ok",       foreground="#a3be8c")
        self.tag_error    = self.term_buf.create_tag("error",    foreground="#bf616a")
        self.tag_warn     = self.term_buf.create_tag("warn",     foreground="#ebcb8b")
        self.tag_dim      = self.term_buf.create_tag("dim",      foreground="#555555")

        # Progress bar (thin, below the terminal)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_pulse_step(0.07)
        self.progress_bar.set_visible(False)

        # Status label (success / error summary)
        self.status = Gtk.Label(label="")
        self.status.set_justify(Gtk.Justification.CENTER)
        self.status.set_wrap(True)
        self.status.set_lines(2)
        self.status.set_ellipsize(Pango.EllipsizeMode.END)
        self.status.set_valign(Gtk.Align.CENTER)

        # Kept for API compatibility — no longer shown, output goes to terminal
        self.log_label = Gtk.Label(label="")
        self.log_label.set_visible(False)

        term_scroll.set_child(self.term_view)
        term_frame.set_child(term_scroll)

        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_box.append(term_frame)
        status_box.append(self.progress_bar)
        status_box.append(self.status)
        main_box.append(status_box)

        self._pulse_source = None

        clamp.set_child(main_box)
        scroll.set_child(clamp)
        toolbar.set_content(scroll)

        # ── Buttons ───────────────────────────────────────────────────────
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_margin_top(8)
        btn_box.set_margin_bottom(16)
        btn_box.set_margin_start(16)
        btn_box.set_margin_end(16)
        btn_box.set_homogeneous(True)

        self.exit_btn = Gtk.Button(label=L("Quitter", "Exit"))
        self.exit_btn.connect("clicked", lambda _: self.close())
        btn_box.append(self.exit_btn)

        self.apply_btn = Gtk.Button(label=L("Appliquer et reconstruire", "Apply & Rebuild"))
        self.apply_btn.add_css_class("suggested-action")
        self.apply_btn.connect("clicked", self.on_apply)
        btn_box.append(self.apply_btn)

        toolbar.add_bottom_bar(btn_box)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _term_append(self, text: str, tag_name: str = "info"):
        """Append a line to the integrated terminal (must be called from the main thread)."""
        buf = self.term_buf
        end_iter = buf.get_end_iter()
        tag = buf.get_tag_table().lookup(tag_name)
        if tag:
            buf.insert_with_tags(end_iter, text + "\n", tag)
        else:
            buf.insert(end_iter, text + "\n")
        # Auto-scroll to bottom
        adj = self.term_view.get_parent().get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    def _term_clear(self):
        self.term_buf.set_text("")

    def _pick_tag(self, line: str) -> str:
        lo = line.lower()
        if line.startswith("="):
            return "section"
        if any(w in lo for w in ("error", "failed", "✗", "fail")):
            return "error"
        if any(w in lo for w in ("warning", "warn")):
            return "warn"
        if any(w in lo for w in ("done", "success", "✓", "completed", "ok")):
            return "ok"
        if line.startswith("Running") or line.startswith("Checking"):
            return "dim"
        return "info"

    def _start_progress(self):
        self.progress_bar.set_visible(True)
        self.status.set_label("")
        if self._pulse_source is None:
            self._pulse_source = GLib.timeout_add(80, self._do_pulse)

    def _do_pulse(self):
        self.progress_bar.pulse()
        return True

    def _stop_progress(self):
        if self._pulse_source is not None:
            GLib.source_remove(self._pulse_source)
            self._pulse_source = None
        self.progress_bar.set_visible(False)

    def _on_category_selected(self, listbox, row):
        if row is None:
            return
        self.content_stack.set_visible_child_name(row.category_id)
        # Safety net: forces the ScrolledWindow to re-measure against the
        # newly shown page rather than keeping the (potentially larger)
        # previous page's allocation.
        self.content_scroll.queue_resize()

    def _on_gaming_master_toggled(self, sw, _param):
        active = sw.get_active()
        self.gaming_apps_group.set_sensitive(active)
        self._update_gaming_counter()

    def _update_gaming_counter(self):
        if not self.gaming_master_switch.get_active():
            self.gaming_counter_label.set_label(L("Gaming désactivé", "Gaming disabled"))
            return
        states = self.gaming_apps_group.get_states()
        enabled = sum(1 for v in states.values() if v)
        self.gaming_counter_label.set_label(
            L(f"{enabled}/{len(states)} apps gaming activées", f"{enabled}/{len(states)} gaming apps enabled")
        )

    def _update_integration_visibility(self, de_id: str):
        """Cache la page Integration pour gnome/kde (sans effet dessus) et
        retombe sur Desktop si elle était sélectionnée."""
        supported = de_id in DESKTOP_INTEGRATION_SUPPORTED_DE
        row = self._category_rows["integration"]
        row.set_visible(supported)
        if not supported and self.category_list.get_selected_row() is row:
            self.category_list.select_row(self._category_rows["desktop"])

    def _update_filemanager_visibility(self, de_id: str):
        """Cache la page File Manager pour gnome/kde (sans effet dessus) et
        retombe sur Desktop si elle était sélectionnée."""
        supported = de_id in FILE_MANAGER_SUPPORTED_DE
        row = self._category_rows["filemanager"]
        row.set_visible(supported)
        if not supported and self.category_list.get_selected_row() is row:
            self.category_list.select_row(self._category_rows["desktop"])

    def _update_icon_theme_visibility(self, de_id: str):
        """Cache la page Icon Theme pour gnome/kde (sans effet dessus, ils
        gardent leur propre sélecteur natif) et retombe sur Desktop si elle
        était sélectionnée."""
        supported = de_id in DESKTOP_INTEGRATION_SUPPORTED_DE
        row = self._category_rows["icon_theme"]
        row.set_visible(supported)
        if not supported and self.category_list.get_selected_row() is row:
            self.category_list.select_row(self._category_rows["desktop"])

    def _on_de_toggled(self, check, *_):
        """Affiche/cache le shell selector et met à jour la liste selon le DE choisi."""
        new_de  = self.de_selector.selected_id
        visible = new_de in SHELL_SUPPORTED_DE
        self.shell_selector.set_visible(visible)
        self._update_integration_visibility(new_de)
        self._update_filemanager_visibility(new_de)
        self._update_icon_theme_visibility(new_de)

        umbriel_visible = new_de in UMBRIEL_SUPPORTED_DE
        self.scratchpad_row.set_visible(umbriel_visible)
        self.scratchpad_note.set_visible(umbriel_visible)

        if not visible:
            return

        # Reconciles the displayed shell list with the ones expected for
        # this DE (e.g.: switching to Umbriel → Noctalia only; back to
        # Hyprland → Noctalia/DMS + Caelestia, etc.)
        self.shell_selector.sync_items(shells_for_de(new_de))

        log.debug(
            "DE changed to '%s' — shell selector updated (shells: %s)",
            new_de,
            [item["id"] for item in shells_for_de(new_de)],
        )

    def on_theme_changed(self, style_manager, _param):
        dark = style_manager.get_dark()
        log.debug("Theme changed — dark: %s", dark)
        self.de_selector.update_icons(dark)
        self.shell_selector.update_icons(dark)
        self.integration_selector.update_icons(dark)
        self.editor_selector.update_icons(dark)
        self.terminal_selector.update_icons(dark)
        self.login_shell_selector.update_icons(dark)
        self.filemanager_selector.update_icons(dark)
        self.matrix_selector.update_icons(dark)
        self.discord_selector.update_icons(dark)
        self.telegram_selector.update_icons(dark)
        self.rgb_selector.update_icons(dark)
        self.video_player_selector.update_icons(dark)
        self.torrent_client_selector.update_icons(dark)

    # ── Apply logic ───────────────────────────────────────────────────────

    def on_apply(self, btn):
        new_de    = self.de_selector.selected_id
        cur_de    = get_current_de()
        cur_shell = get_current_shell()

        de_changed = new_de != cur_de

        # The shell only matters for niri/hyprland/mangowc/umbriel
        shell_relevant = new_de in SHELL_SUPPORTED_DE
        new_shell      = self.shell_selector.selected_id if shell_relevant else cur_shell
        shell_changed  = shell_relevant and (new_shell != cur_shell)

        # Keyring/portal — only relevant for bare compositors
        integration_relevant = new_de in DESKTOP_INTEGRATION_SUPPORTED_DE
        cur_integration = get_string_option("roudix.desktopIntegration", "gnome")
        new_integration = self.integration_selector.selected_id if integration_relevant else cur_integration
        integration_changed = integration_relevant and (new_integration != cur_integration)

        # Default editor
        cur_editor = get_string_option("roudix.editor", "zed")
        new_editor = self.editor_selector.selected_id
        editor_changed = new_editor != cur_editor

        # Default terminal
        cur_terminal = get_string_option("roudix.terminal", "ghostty")
        new_terminal = self.terminal_selector.selected_id
        terminal_changed = new_terminal != cur_terminal

        # Browsers (list) + Zen (separate switch)
        cur_browsers = get_list_option("roudix.browsers", ["brave"])
        new_browsers = [b["id"] for b in BROWSERS if self.browser_group.get_states()[b["id"]]]
        browsers_changed = new_browsers != cur_browsers

        cur_zen = get_bool_option("roudix.zen.enable", False)
        new_zen = self.zen_switch.get_active()
        zen_changed = new_zen != cur_zen

        cur_zen_variant = get_string_option("roudix.zen.variant", "twilight")
        new_zen_variant = self.zen_variant_selector.selected_id
        zen_variant_changed = new_zen_variant != cur_zen_variant

        # roudix.umbriel.scratchpadApps — only makes sense under Umbriel,
        # but nothing prevents reading/writing the switch even hidden (it
        # keeps its previous state while not shown).
        cur_scratchpad = get_bool_option("roudix.umbriel.scratchpadApps", False)
        new_scratchpad = self.scratchpad_switch.get_active()
        scratchpad_changed = new_scratchpad != cur_scratchpad

        cur_sine = get_bool_option("roudix.zen.sine.enable", False)
        new_sine = self.sine_switch.get_active()
        sine_changed = new_sine != cur_sine

        # The mods list targets roudix.zen.mods or roudix.zen.sine.mods
        # based on the chosen Sine state (not the previous one) — that's
        # the one that will be active once the rebuild is done.
        zen_mods_key = "roudix.zen.sine.mods" if new_sine else "roudix.zen.mods"
        cur_zen_mods = get_list_option(zen_mods_key, [])
        new_zen_mods = [m["id"] for m in ZEN_MODS if self.zen_mods_group.get_states()[m["id"]]]
        zen_mods_changed = new_zen_mods != cur_zen_mods

        # Gaming apps: independent booleans, only touch the ones that changed
        gaming_changes = _diff_bool_items(GAMING_APPS, self.gaming_apps_group.get_states())

        # Extra gaming tweaks (ananicy, GTA fix)
        gaming_extras_changes = _diff_bool_items(GAMING_EXTRAS, self.gaming_extras_group.get_states())

        # Master switch for the gaming group
        cur_gaming_master = get_bool_option("roudix.gaming.enable", True)
        new_gaming_master = self.gaming_master_switch.get_active()
        gaming_master_changed = new_gaming_master != cur_gaming_master

        # Content creation: master switch + independent toggles + OBS
        # plugins (list) + video editor (enum)
        cur_cc_master = get_bool_option("roudix.contentCreation.enable", True)
        new_cc_master = self.cc_master_switch.get_active()
        cc_master_changed = new_cc_master != cur_cc_master

        cc_changes = _diff_bool_items(CONTENT_CREATION_TOGGLES, self.cc_group.get_states())

        obs_plugins_changes = _diff_bool_items(OBS_PLUGINS, self.obs_plugins_group.get_states())

        cur_video_editor = get_string_option("roudix.contentCreation.videoEditor", "kdenlive")
        new_video_editor = self.video_editor_selector.selected_id
        video_editor_changed = new_video_editor != cur_video_editor

        # Login shell (fish/bash)
        cur_login_shell = get_string_option("roudix.shell", "fish")
        new_login_shell = self.login_shell_selector.selected_id
        login_shell_changed = new_login_shell != cur_login_shell

        # File manager — only relevant on bare compositors
        filemanager_relevant = new_de in FILE_MANAGER_SUPPORTED_DE
        cur_filemanager = get_string_option("roudix.fileManager", "nautilus")
        new_filemanager = self.filemanager_selector.selected_id if filemanager_relevant else cur_filemanager
        filemanager_changed = filemanager_relevant and (new_filemanager != cur_filemanager)

        # Matrix client
        cur_matrix = get_string_option("roudix.matrixClient", "element")
        new_matrix = self.matrix_selector.selected_id
        matrix_changed = new_matrix != cur_matrix

        # Discord
        cur_discord = get_string_option("roudix.discord", "vencord")
        new_discord = self.discord_selector.selected_id
        discord_changed = new_discord != cur_discord

        # Telegram
        cur_telegram = get_string_option("roudix.telegram", "none")
        new_telegram = self.telegram_selector.selected_id
        telegram_changed = new_telegram != cur_telegram

        # Independent system toggles
        system_changes = _diff_bool_items(self.system_toggles, self.system_group.get_states())

        # RGB backend
        cur_rgb = get_string_option("roudix.rgb", "none")
        new_rgb = self.rgb_selector.selected_id
        rgb_changed = new_rgb != cur_rgb

        # Video player
        cur_video_player = get_string_option("roudix.videoPlayer", "vlc")
        new_video_player = self.video_player_selector.selected_id
        video_player_changed = new_video_player != cur_video_player

        # Torrent client
        cur_torrent_client = get_string_option("roudix.torrentClient", "none")
        new_torrent_client = self.torrent_client_selector.selected_id
        torrent_client_changed = new_torrent_client != cur_torrent_client

        # Icon theme
        cur_icon_theme = get_string_option("roudix.iconTheme", "papirus")
        new_icon_theme = self.icon_theme_selector.selected_id
        icon_theme_changed = new_icon_theme != cur_icon_theme

        if not any([de_changed, shell_changed, integration_changed, editor_changed,
                    terminal_changed, browsers_changed, zen_changed, zen_variant_changed, sine_changed,
                    zen_mods_changed, scratchpad_changed,
                    login_shell_changed, filemanager_changed, matrix_changed,
                    discord_changed, telegram_changed,
                    system_changes, rgb_changed, video_player_changed, torrent_client_changed,
                    icon_theme_changed,
                    gaming_changes, gaming_extras_changes, gaming_master_changed,
                    cc_master_changed, cc_changes, obs_plugins_changes, video_editor_changed]):
            log.info("No changes detected — nothing to do.")
            self.status.set_markup(
                L(
                    "<span color='gray'>Aucun changement détecté — rien à faire.</span>",
                    "<span color='gray'>No changes detected — nothing to do.</span>",
                )
            )
            return

        # Build a human-readable summary of what will change
        _en = L("activé", "enabled")
        _dis = L("désactivé", "disabled")
        _none = L("aucun", "none")
        changes = []
        if de_changed:
            changes.append(f"{L('Bureau', 'Desktop')}: <b>{cur_de}</b> → <b>{new_de}</b>")
        if shell_changed:
            changes.append(f"{L('Shell', 'Shell')}: <b>{cur_shell}</b> → <b>{new_shell}</b>")
        if integration_changed:
            changes.append(f"{L('Keyring/portail', 'Keyring/portal')}: <b>{cur_integration}</b> → <b>{new_integration}</b>")
        if editor_changed:
            changes.append(f"{L('Éditeur', 'Editor')}: <b>{cur_editor}</b> → <b>{new_editor}</b>")
        if terminal_changed:
            changes.append(f"{L('Terminal', 'Terminal')}: <b>{cur_terminal}</b> → <b>{new_terminal}</b>")
        if browsers_changed:
            changes.append(f"{L('Navigateurs', 'Browsers')}: <b>{', '.join(new_browsers) or _none}</b>")
        if zen_changed:
            changes.append(f"Zen Browser: <b>{_en if new_zen else _dis}</b>")
        if zen_variant_changed:
            changes.append(f"{L('Canal Zen', 'Zen channel')}: <b>{cur_zen_variant}</b> → <b>{new_zen_variant}</b>")
        if sine_changed:
            changes.append(f"{L('Chargeur de mods Sine', 'Sine mod loader')}: <b>{_en if new_sine else _dis}</b>")
        if zen_mods_changed:
            changes.append(f"{L('Mods Zen', 'Zen mods')}: <b>{', '.join(new_zen_mods) or _none}</b>")
        if scratchpad_changed:
            changes.append(f"{L('Apps en scratchpad (Umbriel)', 'Umbriel scratchpad apps')}: <b>{_en if new_scratchpad else _dis}</b>")
        if login_shell_changed:
            changes.append(f"{L('Shell de connexion', 'Login shell')}: <b>{cur_login_shell}</b> → <b>{new_login_shell}</b>")
        if filemanager_changed:
            changes.append(f"{L('Gestionnaire de fichiers', 'File manager')}: <b>{cur_filemanager}</b> → <b>{new_filemanager}</b>")
        if matrix_changed:
            changes.append(f"{L('Client Matrix', 'Matrix client')}: <b>{cur_matrix}</b> → <b>{new_matrix}</b>")
        if discord_changed:
            changes.append(f"Discord: <b>{cur_discord}</b> → <b>{new_discord}</b>")
        if telegram_changed:
            changes.append(f"Telegram: <b>{cur_telegram}</b> → <b>{new_telegram}</b>")
        if rgb_changed:
            changes.append(f"{L('Backend RGB', 'RGB backend')}: <b>{cur_rgb}</b> → <b>{new_rgb}</b>")
        if video_player_changed:
            changes.append(f"{L('Lecteur vidéo', 'Video player')}: <b>{cur_video_player}</b> → <b>{new_video_player}</b>")
        if torrent_client_changed:
            changes.append(f"{L('Client torrent', 'Torrent client')}: <b>{cur_torrent_client}</b> → <b>{new_torrent_client}</b>")
        if icon_theme_changed:
            changes.append(f"{L('Thème d\'icônes', 'Icon theme')}: <b>{cur_icon_theme}</b> → <b>{new_icon_theme}</b>")
        if gaming_master_changed:
            changes.append(f"Gaming: <b>{_en if new_gaming_master else _dis}</b>")
        for _key, new_val, name, _file in gaming_changes.values():
            changes.append(f"{name}: <b>{_en if new_val else _dis}</b>")
        for _key, new_val, name, _file in gaming_extras_changes.values():
            changes.append(f"{name}: <b>{_en if new_val else _dis}</b>")
        if cc_master_changed:
            changes.append(f"{L('Création de contenu', 'Content Creation')}: <b>{_en if new_cc_master else _dis}</b>")
        for _key, new_val, name, _file in cc_changes.values():
            changes.append(f"{name}: <b>{_en if new_val else _dis}</b>")
        for _key, new_val, name, _file in obs_plugins_changes.values():
            changes.append(f"{name}: <b>{_en if new_val else _dis}</b>")
        if video_editor_changed:
            changes.append(f"{L('Éditeur vidéo', 'Video editor')}: <b>{cur_video_editor}</b> → <b>{new_video_editor}</b>")
        for _key, new_val, name, _file in system_changes.values():
            changes.append(f"{name}: <b>{_en if new_val else _dis}</b>")
        body_changes = "\n".join(changes)

        pending = {
            "de_changed": de_changed, "new_de": new_de,
            "shell_changed": shell_changed, "new_shell": new_shell,
            "integration_changed": integration_changed, "new_integration": new_integration,
            "editor_changed": editor_changed, "new_editor": new_editor,
            "terminal_changed": terminal_changed, "new_terminal": new_terminal,
            "browsers_changed": browsers_changed, "new_browsers": new_browsers,
            "zen_changed": zen_changed, "new_zen": new_zen,
            "zen_variant_changed": zen_variant_changed, "new_zen_variant": new_zen_variant,
            "sine_changed": sine_changed, "new_sine": new_sine,
            "zen_mods_changed": zen_mods_changed, "new_zen_mods": new_zen_mods, "zen_mods_key": zen_mods_key,
            "scratchpad_changed": scratchpad_changed, "new_scratchpad": new_scratchpad,
            "login_shell_changed": login_shell_changed, "new_login_shell": new_login_shell,
            "filemanager_changed": filemanager_changed, "new_filemanager": new_filemanager,
            "matrix_changed": matrix_changed, "new_matrix": new_matrix,
            "discord_changed": discord_changed, "new_discord": new_discord,
            "telegram_changed": telegram_changed, "new_telegram": new_telegram,
            "rgb_changed": rgb_changed, "new_rgb": new_rgb,
            "video_player_changed": video_player_changed, "new_video_player": new_video_player,
            "torrent_client_changed": torrent_client_changed, "new_torrent_client": new_torrent_client,
            "icon_theme_changed": icon_theme_changed, "new_icon_theme": new_icon_theme,
            "gaming_master_changed": gaming_master_changed, "new_gaming_master": new_gaming_master,
            "gaming_changes": gaming_changes,
            "gaming_extras_changes": gaming_extras_changes,
            "system_changes": system_changes,
            "cc_master_changed": cc_master_changed, "new_cc_master": new_cc_master,
            "cc_changes": cc_changes,
            "obs_plugins_changes": obs_plugins_changes,
            "video_editor_changed": video_editor_changed, "new_video_editor": new_video_editor,
        }

        dialog = Adw.AlertDialog()
        dialog.set_heading(L("Appliquer les changements ?", "Apply changes?"))
        dialog.set_body(
            f"{body_changes}\n\n"
            + L(
                "« Appliquer maintenant » bascule ta session en cours immédiatement "
                "(certaines choses, comme le bureau/shell, ne prennent pleinement effet "
                "qu'après une déconnexion). « Appliquer au prochain démarrage » prépare "
                "juste la nouvelle génération — rien ne change avant le redémarrage.",
                "Apply now switches your running session immediately (a few things, "
                "like the desktop/shell, only fully take effect after you log out). "
                "Apply at next boot just prepares the new generation — nothing "
                "changes until you restart.",
            )
        )
        # body_changes contains Pango markup (<b>...</b>) to highlight the
        # values that change — without this, AlertDialog would display the
        # tags literally instead of interpreting them.
        dialog.set_body_use_markup(True)
        dialog.add_response("cancel", L("Annuler", "Cancel"))
        dialog.add_response("boot", L("Appliquer au prochain démarrage", "Apply at Next Boot"))
        dialog.add_response("switch", L("Appliquer maintenant", "Apply Now"))
        dialog.set_response_appearance("switch", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("switch")
        dialog.set_close_response("cancel")
        dialog.connect("response", self.on_confirm_response, pending)
        dialog.present(self)

    def on_confirm_response(self, dialog, response, pending):
        if response not in ("boot", "switch"):
            log.info("User cancelled the rebuild dialog.")
            return
        mode = response  # "boot" (next reboot) or "switch" (right now)

        if pending["de_changed"]:
            result = set_de(pending["new_de"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config DE : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing DE config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["shell_changed"]:
            result = set_shell(pending["new_shell"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config shell : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing shell config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["integration_changed"]:
            result = set_string_option("roudix.desktopIntegration", pending["new_integration"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config keyring/portal : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing keyring/portal config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["editor_changed"]:
            result = set_string_option("roudix.editor", pending["new_editor"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config editor : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing editor config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["terminal_changed"]:
            result = set_string_option("roudix.terminal", pending["new_terminal"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config terminal : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing terminal config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["browsers_changed"]:
            result = set_list_option("roudix.browsers", pending["new_browsers"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config browsers : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing browsers config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["zen_changed"]:
            result = set_bool_option("roudix.zen.enable", pending["new_zen"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config Zen Browser : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing Zen Browser config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["zen_variant_changed"]:
            result = set_string_option("roudix.zen.variant", pending["new_zen_variant"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config Zen channel : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing Zen channel config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["sine_changed"]:
            result = set_bool_option("roudix.zen.sine.enable", pending["new_sine"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config Sine : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing Sine config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["zen_mods_changed"]:
            result = set_list_option(pending["zen_mods_key"], pending["new_zen_mods"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config Zen mods : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing Zen mods config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["scratchpad_changed"]:
            result = set_bool_option("roudix.umbriel.scratchpadApps", pending["new_scratchpad"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config Umbriel scratchpad : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing Umbriel scratchpad config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["login_shell_changed"]:
            result = set_string_option("roudix.shell", pending["new_login_shell"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config login shell : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing login shell config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["filemanager_changed"]:
            result = set_string_option("roudix.fileManager", pending["new_filemanager"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config file manager : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing file manager config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["matrix_changed"]:
            result = set_string_option("roudix.matrixClient", pending["new_matrix"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config Matrix client : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing Matrix client config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["discord_changed"]:
            result = set_string_option("roudix.discord", pending["new_discord"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config Discord : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing Discord config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["telegram_changed"]:
            result = set_string_option("roudix.telegram", pending["new_telegram"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config Telegram : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing Telegram config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["rgb_changed"]:
            result = set_string_option("roudix.rgb", pending["new_rgb"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config RGB backend : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing RGB backend config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["video_player_changed"]:
            result = set_string_option("roudix.videoPlayer", pending["new_video_player"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config lecteur vidéo : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing video player config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["torrent_client_changed"]:
            result = set_string_option("roudix.torrentClient", pending["new_torrent_client"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config client torrent : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing torrent client config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["icon_theme_changed"]:
            result = set_string_option("roudix.iconTheme", pending["new_icon_theme"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config thème d'icônes : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing icon theme config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["gaming_master_changed"]:
            result = set_bool_option("roudix.gaming.enable", pending["new_gaming_master"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config gaming : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing gaming config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        for key, new_val, name, file in pending["gaming_changes"].values():
            result = set_bool_option(key, new_val, path=file)
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config {name} : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing {name} config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        for key, new_val, name, file in pending["gaming_extras_changes"].values():
            result = set_bool_option(key, new_val, path=file)
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config {name} : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing {name} config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["cc_master_changed"]:
            result = set_bool_option("roudix.contentCreation.enable", pending["new_cc_master"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config Content Creation : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing Content Creation config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        for key, new_val, name, file in pending["cc_changes"].values():
            result = set_bool_option(key, new_val, path=file)
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config {name} : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing {name} config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        for key, new_val, name, file in pending["obs_plugins_changes"].values():
            result = set_bool_option(key, new_val, path=file)
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config {name} : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing {name} config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        if pending["video_editor_changed"]:
            result = set_string_option("roudix.contentCreation.videoEditor", pending["new_video_editor"])
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config video editor : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing video editor config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        for key, new_val, name, file in pending["system_changes"].values():
            result = set_bool_option(key, new_val, path=file)
            if result is not True:
                self.status.set_markup(
                    L(f"<span color='red'>Erreur d'écriture — config {name} : {GLib.markup_escape_text(result)}</span>", f"<span color='red'>Error writing {name} config: {GLib.markup_escape_text(result)}</span>")
                )
                return

        self.status.set_markup("")
        GLib.idle_add(self.term_frame.set_visible, True)
        GLib.idle_add(self._term_clear)
        GLib.idle_add(self._term_append, "=" * 50, "section")
        GLib.idle_add(self._term_append, L("Notes importantes :", "Important Notices:"), "section")
        GLib.idle_add(self._term_append, "=" * 50, "section")
        GLib.idle_add(self._term_append, L("Aucun problème signalé pour le moment.", "No issues currently reported."), "info")
        GLib.idle_add(self._term_append, "", "dim")
        GLib.idle_add(self._term_append, "=" * 50, "section")
        GLib.idle_add(self._start_progress)
        self.apply_btn.set_sensitive(False)
        self.exit_btn.set_sensitive(False)

        log.info(
            "Starting NixOS rebuild (nh os %s) — DE: %s, shell: %s",
            mode,
            pending["new_de"] if pending["de_changed"] else "(unchanged)",
            pending["new_shell"] if pending["shell_changed"] else "(unchanged)",
        )

        import threading
        threading.Thread(target=self.run_rebuild, args=(mode,), daemon=True).start()

    def run_rebuild(self, mode: str = "boot"):
        try:
            cmd_str = (
                f"{L('Lancement', 'Running')}: nh os {mode} --elevation-strategy pkexec "
                f"--accept-flake-config {NH_FLAKE}"
            )
            log.info(cmd_str)
            GLib.idle_add(self._term_append, cmd_str, "dim")
            GLib.idle_add(self._term_append, L("Vérification des dépôts...", "Checking repositories..."), "dim")

            proc = subprocess.Popen(
                [
                    "nh", "os", mode,
                    "--elevation-strategy", "pkexec",
                    "--accept-flake-config", f"path:{NH_FLAKE}",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            # Read char-by-char to handle \r (in-place timer updates from nh).
            # \r resets the current line buffer; \n commits it to the terminal.
            _buf = ""
            for ch in iter(lambda: proc.stdout.read(1), ""):
                if ch == "\r":
                    _buf = ""  # discard in-place overwrite
                elif ch == "\n":
                    line = strip_ansi(_buf).strip()
                    _buf = ""
                    if line:
                        log.info(line)
                        GLib.idle_add(self._term_append, line, self._pick_tag(line))
                else:
                    _buf += ch
            if _buf.strip():
                line = strip_ansi(_buf).strip()
                if line:
                    log.info(line)
                    GLib.idle_add(self._term_append, line, self._pick_tag(line))

            proc.wait()

            if proc.returncode != 0:
                raise subprocess.CalledProcessError(proc.returncode, "nh")

            log.info("Rebuild completed successfully.")
            GLib.idle_add(self._term_append, "", "dim")
            if mode == "switch":
                GLib.idle_add(self._term_append, L("✓ Reconstruction terminée et appliquée à ta session en cours.", "✓ Rebuild completed and applied to your running session."), "ok")
                GLib.idle_add(
                    self.status.set_markup,
                    L(
                        "<span color='green'>✓ Terminé ! Appliqué maintenant — certaines choses "
                        "(bureau/shell) peuvent encore nécessiter une déconnexion pour prendre "
                        "pleinement effet.</span>",
                        "<span color='green'>✓ Done! Applied now — some things (desktop/shell) "
                        "may still need a logout to fully take effect.</span>",
                    ),
                )
            else:
                GLib.idle_add(self._term_append, L("✓ Reconstruction terminée avec succès. Redémarre pour appliquer les changements.", "✓ Rebuild completed successfully. Reboot to apply changes."), "ok")
                GLib.idle_add(
                    self.status.set_markup,
                    L(
                        "<span color='green'>✓ Terminé ! Redémarre pour appliquer les changements.</span>",
                        "<span color='green'>✓ Done! Reboot to apply changes.</span>",
                    ),
                )
            GLib.idle_add(self._stop_progress)

        except subprocess.CalledProcessError as e:
            log.error("Rebuild failed (exit code %d).", e.returncode)
            GLib.idle_add(self._term_append, "", "dim")
            GLib.idle_add(self._term_append, L(f"✗ Échec de la reconstruction (code de sortie {e.returncode}).", f"✗ Rebuild failed (exit code {e.returncode})."), "error")
            GLib.idle_add(self._stop_progress)
            GLib.idle_add(
                self.status.set_markup,
                L(
                    "<span color='red'>✗ Échec de la reconstruction. Consulte <tt>~/.local/share/roudix-switcher/switcher.log</tt> pour les détails.</span>",
                    "<span color='red'>✗ Rebuild failed. Check <tt>~/.local/share/roudix-switcher/switcher.log</tt> for details.</span>",
                ),
            )
        except Exception as e:
            log.exception("Unexpected error during rebuild.")
            GLib.idle_add(self._term_append, "", "dim")
            GLib.idle_add(self._term_append, L(f"✗ Erreur inattendue : {e}", f"✗ Unexpected error: {e}"), "error")
            GLib.idle_add(self._stop_progress)
            GLib.idle_add(
                self.status.set_markup,
                L(
                    f"<span color='red'>✗ Erreur inattendue : {GLib.markup_escape_text(str(e))}</span>",
                    f"<span color='red'>✗ Unexpected error: {GLib.markup_escape_text(str(e))}</span>",
                ),
            )
        finally:
            GLib.idle_add(self.apply_btn.set_sensitive, True)
            GLib.idle_add(self.exit_btn.set_sensitive, True)


# ── Application ───────────────────────────────────────────────────────────────

class RoudixSwitcherApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.roudix.switcher")
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        win = RoudixSwitcherWindow(app)
        win.present()


def main():
    setup_logging()
    log.info("=== Roudix Switcher started ===")
    app = RoudixSwitcherApp()
    sys.exit(app.run(sys.argv))


if __name__ == "__main__":
    main()
