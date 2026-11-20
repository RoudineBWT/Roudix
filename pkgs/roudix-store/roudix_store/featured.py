"""Apps the welcome page of roudix-store puts forward.

Each entry is what `AppEntry.pkg_names` holds for the app: a nixpkgs attribute name, a Flathub
application id, or a "<flake>#<attr>" reference for the flake packages (roudix.store.flakeSources).
Entries the catalog doesn't have are skipped, and only the first MAX_FEATURED that exist are shown,
so the lists can stay a bit long.

To change them without touching the code, drop /etc/roudix-store/featured.json (or point
ROUDIX_STORE_FEATURED at a file) shaped like {"nix": ["firefox", ...], "flatpak": ["org.mozilla.firefox", ...]}.
A source missing from the file keeps its default list.
"""
from __future__ import annotations

import json
import os

FEATURED_FILE = os.environ.get("ROUDIX_STORE_FEATURED") or "/etc/roudix-store/featured.json"
MAX_FEATURED = 9  # three full rows of tiles

DEFAULT_FEATURED: dict[str, list[str]] = {
    "nix": [
        "roudix-caches#faugus", "firefox", "vlc", "gimp", "libreoffice-fresh", "obs-studio",
        "steam", "discord", "krita", "blender", "thunderbird", "telegram-desktop",
        "heroic", "lutris", "inkscape", "audacity", "bitwarden-desktop",
    ],
    "flatpak": [
        "org.mozilla.firefox", "org.videolan.VLC", "org.gimp.GIMP", "org.libreoffice.LibreOffice",
        "com.obsproject.Studio", "com.valvesoftware.Steam", "com.discordapp.Discord", "org.kde.krita",
        "org.blender.Blender", "org.mozilla.Thunderbird", "org.telegram.desktop",
        "com.heroicgameslauncher.hgl", "net.lutris.Lutris", "org.inkscape.Inkscape",
        "org.audacityteam.Audacity", "com.bitwarden.desktop",
    ],
}


def featured_for(source: str) -> list[str]:
    """Wanted entries for "nix" / "flatpak": the JSON override if it has the source, else the defaults."""
    try:
        with open(FEATURED_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
        wanted = data.get(source) if isinstance(data, dict) else None
        if isinstance(wanted, list):
            return [str(x) for x in wanted if isinstance(x, str) and x]
    except (OSError, ValueError):
        pass
    return list(DEFAULT_FEATURED.get(source, []))
