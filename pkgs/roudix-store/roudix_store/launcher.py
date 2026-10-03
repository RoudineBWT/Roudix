"""Open an installed app from its AppStream desktop-id.

`gtk-launch` is not on PATH on NixOS, and GIO's in-process app cache goes stale
when a rebuild swaps the system profile symlink. So we scan the XDG data dirs
(plus the usual Nix profile locations) for the .desktop file ourselves and
launch it straight from that path.
"""
from __future__ import annotations

import os

EXTRA_DIRS = (
    "/run/current-system/sw/share",
    "/nix/var/nix/profiles/default/share",
)


def data_dirs() -> list[str]:
    home = os.path.expanduser("~")
    user = os.environ.get("USER") or os.path.basename(home)
    dirs = [os.environ.get("XDG_DATA_HOME") or os.path.join(home, ".local/share")]
    dirs += [d for d in os.environ.get("XDG_DATA_DIRS", "").split(":") if d]
    dirs += [os.path.join(home, ".nix-profile/share"), f"/etc/profiles/per-user/{user}/share", *EXTRA_DIRS]
    seen: set[str] = set()
    return [d for d in dirs if not (d in seen or seen.add(d))]


def find_desktop_file(desktop_id: str) -> str | None:
    name = os.path.basename(str(desktop_id))
    if not name.endswith(".desktop"):
        name += ".desktop"
    for base in data_dirs():
        path = os.path.join(base, "applications", name)
        if os.path.isfile(path):
            return path
    return None


def launch(launchables: list[str], context=None) -> tuple[bool, str]:
    """Try each desktop-id in turn. Returns (ok, message)."""
    import gi
    from gi.repository import Gio, GLib

    ids = [str(x) for x in launchables if x]
    if not ids:
        return False, "no launcher available for this package"
    for desktop_id in ids:
        path = find_desktop_file(desktop_id)
        if not path:
            continue
        info = Gio.DesktopAppInfo.new_from_filename(path)
        if info is None:
            continue
        try:
            info.launch([], context)
            return True, os.path.basename(path)
        except GLib.Error as exc:
            return False, str(exc.message)
    return False, "launcher not found — apply the queue first (new apps can need a re-login to show up)"
