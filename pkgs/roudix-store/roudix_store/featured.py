"""Apps the welcome page of roudix-store puts forward, and how they change.

Each entry is what `AppEntry.pkg_names` holds for the app: a nixpkgs attribute name, a Flathub
application id, or a "<flake>#<attr>" reference for the flake packages (roudix.store.flakeSources).
Entries the catalog doesn't have are skipped.

Per source ("nix" / "flatpak") there are two lists:
  pinned : always shown first, in this order
  pool   : the rest of the tiles are drawn from here; the draw changes every ROTATE_DAYS day(s) and is
           the same for everybody on a given day (the date is the seed), so nothing needs the network.

Where the lists come from, first one that has the source wins:
  1. /etc/roudix-store/featured.json (or the file ROUDIX_STORE_FEATURED points at): your own choice
  2. the copy of a remote featured.json kept in ~/.cache/roudix-store, refreshed at most once a day
     in the background; the URL (https only) is roudix.store.featuredUrl, written to
     /etc/roudix-store/featured-url, or the ROUDIX_STORE_FEATURED_URL variable
  3. DEFAULT_FEATURED below

File shape (a plain list is accepted too: it means "pinned", no rotation):
  {"nix": {"pinned": ["roudix-caches#faugus"], "pool": ["firefox", "vlc"]},
   "flatpak": {"pinned": [], "pool": ["org.mozilla.firefox"]}}
"""
from __future__ import annotations

import datetime
import json
import os
import random
import threading
import time
import urllib.request
from typing import Callable

from . import localnix

FEATURED_FILE = os.environ.get("ROUDIX_STORE_FEATURED") or "/etc/roudix-store/featured.json"
URL_FILE = "/etc/roudix-store/featured-url"
CACHE_FILE = os.path.join(localnix.BACKUP_DIR, "featured.json")
META_FILE = os.path.join(localnix.BACKUP_DIR, "featured.meta.json")  # last success / last failure
MAX_FEATURED = 9           # three full rows of tiles
ROTATE_DAYS = 1            # the pool is drawn again every this many days
REMOTE_MAX_AGE = 86400     # look for a newer remote list at most this often
REMOTE_RETRY = 3600        # after a failed check (offline…), wait this long
MAX_BYTES = 256 * 1024     # a remote list bigger than this is ignored
MAX_ENTRIES = 300          # per list

DEFAULT_FEATURED: dict[str, dict[str, list[str]]] = {
    "nix": {
        "pinned": ["roudix-caches#faugus"],
        "pool": [
            "firefox", "vlc", "mpv", "gimp", "krita", "inkscape", "blender", "kdePackages.kdenlive",
            "obs-studio", "audacity", "libreoffice-fresh", "thunderbird", "telegram-desktop", "discord",
            "spotify", "steam", "heroic", "lutris", "bottles", "prismlauncher", "bitwarden-desktop",
            "keepassxc", "qbittorrent", "signal-desktop", "element-desktop", "vscode", "obsidian",
            "handbrake", "godot_4", "darktable", "calibre", "kdePackages.okular",
        ],
    },
    "flatpak": {
        "pinned": [],
        "pool": [
            "org.mozilla.firefox", "org.videolan.VLC", "org.mpv.Mpv", "org.gimp.GIMP", "org.kde.krita",
            "org.inkscape.Inkscape", "org.blender.Blender", "org.kde.kdenlive", "com.obsproject.Studio",
            "org.audacityteam.Audacity", "org.libreoffice.LibreOffice", "org.mozilla.Thunderbird",
            "org.telegram.desktop", "com.discordapp.Discord", "com.spotify.Client",
            "com.valvesoftware.Steam", "com.heroicgameslauncher.hgl", "net.lutris.Lutris",
            "com.usebottles.bottles", "org.prismlauncher.PrismLauncher", "com.bitwarden.desktop",
            "org.keepassxc.KeePassXC", "org.qbittorrent.qBittorrent", "org.signal.Signal",
            "md.obsidian.Obsidian", "fr.handbrake.ghb", "org.godotengine.Godot",
            "org.darktable.Darktable", "org.kde.okular", "com.github.tchx84.Flatseal",
            "net.nokyan.Resources",
        ],
    },
}


# ── reading ──────────────────────────────────────────────────────────────
def _names(value) -> list[str]:
    out: list[str] = []
    if isinstance(value, list):
        for item in value[:MAX_ENTRIES]:
            if isinstance(item, str) and localnix.valid_name(item) and item not in out:
                out.append(item)
    return out


def _parse(data) -> dict[str, dict[str, list[str]]]:
    """{source: {"pinned": [...], "pool": [...]}} from a decoded featured.json; junk is dropped."""
    found: dict[str, dict[str, list[str]]] = {}
    if not isinstance(data, dict):
        return found
    for source in ("nix", "flatpak"):
        value = data.get(source)
        if isinstance(value, list):
            found[source] = {"pinned": _names(value), "pool": []}
        elif isinstance(value, dict):
            found[source] = {"pinned": _names(value.get("pinned")), "pool": _names(value.get("pool"))}
    return found


def _read_json(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def wanted_for(source: str) -> dict[str, list[str]]:
    """{"pinned": [...], "pool": [...]} for "nix" / "flatpak" (see the module docstring for the order)."""
    for path in (FEATURED_FILE, CACHE_FILE):
        entry = _parse(_read_json(path)).get(source)
        if entry and (entry["pinned"] or entry["pool"]):
            return entry
    default = DEFAULT_FEATURED.get(source, {})
    return {"pinned": list(default.get("pinned", [])), "pool": list(default.get("pool", []))}


def select(source: str, exists: Callable[[str], bool], today: datetime.date | None = None,
           limit: int = MAX_FEATURED) -> list[str]:
    """Up to `limit` entries to show: the pinned ones the catalog has, then a draw from the pool that
    only depends on the date (same for everyone, new every ROTATE_DAYS)."""
    wanted = wanted_for(source)
    pinned = [key for key in wanted["pinned"] if exists(key)][:limit]
    pool = [key for key in wanted["pool"] if key not in pinned and exists(key)]
    day = (today or datetime.date.today()).toordinal() // max(1, ROTATE_DAYS)
    random.Random(f"roudix-store:{source}:{day}").shuffle(pool)
    return pinned + pool[:max(0, limit - len(pinned))]


# ── the remote list ──────────────────────────────────────────────────────
def remote_url() -> str:
    url = (os.environ.get("ROUDIX_STORE_FEATURED_URL") or "").strip()
    if not url:
        try:
            with open(URL_FILE, encoding="utf-8") as fh:
                url = fh.read().strip()
        except OSError:
            url = ""
    return url if url.startswith("https://") else ""


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "roudix-store"})
    with urllib.request.urlopen(request, timeout=8) as response:
        return response.read(MAX_BYTES + 1)


def _write_json_atomic(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
    os.replace(tmp, path)


def refresh(url: str | None = None) -> bool:
    """Fetch the remote list if it is due. True when the cached copy changed."""
    url = url or remote_url()
    if not url:
        return False
    meta = _read_json(META_FILE)
    meta = meta if isinstance(meta, dict) else {}
    now = time.time()
    last_ok, last_fail = float(meta.get("last_ok") or 0), float(meta.get("last_fail") or 0)
    if now - last_ok < REMOTE_MAX_AGE:
        return False
    if last_fail > last_ok and now - last_fail < REMOTE_RETRY:
        return False
    try:
        raw = _download(url)
        if len(raw) > MAX_BYTES:
            raise ValueError("featured list too big")
        parsed = _parse(json.loads(raw.decode("utf-8")))
        if not parsed:
            raise ValueError("no usable list in it")
    except (OSError, ValueError):
        meta["last_fail"] = now
        try:
            _write_json_atomic(META_FILE, meta)
        except OSError:
            pass
        return False
    changed = parsed != _parse(_read_json(CACHE_FILE))
    try:
        if changed:
            _write_json_atomic(CACHE_FILE, parsed)
        meta["last_ok"] = now
        _write_json_atomic(META_FILE, meta)
    except OSError:
        return False
    return changed


def refresh_async(on_change: Callable[[], None]) -> None:
    """`refresh()` in a thread; `on_change()` (called from that thread) when the list changed."""
    def worker() -> None:
        if refresh():
            on_change()

    if remote_url():
        threading.Thread(target=worker, daemon=True).start()
