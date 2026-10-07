"""Flatpak support on demand + first-run AppStream refresh.

* `available()` — is Flatpak really on this system (i.e. roudix.flatpak.enable was applied)?
  When it is not, the store hides its Flatpak catalog and offers to enable it instead.
* `enable_support()` — writes `roudix.flatpak.enable = true;` in hosts/<host>/local.nix,
  runs ONE `nh os switch`, then `flatpak update --appstream`. The caller then asks the
  user to restart the store (the running process was started without Flatpak).
* `needs_first_appstream()` / `update_appstream()` — `flatpak update --appstream`, done
  once (a marker file records the success), so the Flathub catalog is there at first use.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from typing import Callable

from . import localnix
from .i18n import L
from .nix_backend import NixBackend

MARKER = os.path.join(
    os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"),
    "roudix-store", "flatpak-appstream-v1",
)
FALLBACK_BIN = "/run/current-system/sw/bin/flatpak"


def flatpak_bin() -> str | None:
    found = shutil.which("flatpak")
    if found:
        return found
    return FALLBACK_BIN if os.access(FALLBACK_BIN, os.X_OK) else None


def available() -> bool:
    return flatpak_bin() is not None


def needs_first_appstream() -> bool:
    return available() and not os.path.exists(MARKER)


def _has_remote(flatpak: str) -> bool:
    for scope in ("system", "user"):
        try:
            out = subprocess.run([flatpak, "remotes", f"--{scope}", "--columns=name"],
                                 capture_output=True, text=True, timeout=15).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        if any(name.strip() in localnix.FLATPAK_REMOTE_URLS for name in out.splitlines()):
            return True
    return False


def update_appstream(say: Callable[[str], None], wait_for_remote: int = 0) -> bool:
    """`flatpak update --appstream`; the marker is written only if it worked on a real remote.

    wait_for_remote: seconds to wait for nix-flatpak to have added the Flathub remote
    (right after the rebuild that enabled Flatpak)."""
    flatpak = flatpak_bin()
    if not flatpak:
        return False
    deadline = time.monotonic() + wait_for_remote
    while not _has_remote(flatpak):
        if time.monotonic() >= deadline:
            say(L("Aucun dépôt Flatpak pour l'instant — les métadonnées seront récupérées au prochain démarrage.",
                  "No Flatpak remote yet — the metadata will be fetched at the next start."))
            return False
        time.sleep(2)
    code = NixBackend._run_flatpak(flatpak, ["update", "--appstream", "--noninteractive"], say)
    if code != 0:
        return False
    try:
        os.makedirs(os.path.dirname(MARKER), exist_ok=True)
        open(MARKER, "w").close()
    except OSError:
        pass
    return True


def enable_support(say: Callable[[str], None]) -> tuple[bool, str]:
    """Enable roudix.flatpak.enable and rebuild. local.nix is restored if the rebuild fails."""
    saved = localnix.backup_files()
    res = localnix.set_flatpak_enabled(True)
    if res is not True:
        localnix.restore_files(saved)
        return False, L(f"Impossible d'écrire local.nix : {res}", f"Could not write local.nix: {res}")
    say(L("local.nix mis à jour : roudix.flatpak.enable = true", "local.nix updated: roudix.flatpak.enable = true"))

    cmd = ["nh", "os", "switch", "--elevation-strategy", "pkexec",
           "--accept-flake-config", f"path:{localnix.NH_FLAKE}"]
    say("$ " + " ".join(cmd))
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                say(line)
        ok = proc.wait() == 0
    except OSError as exc:
        localnix.restore_files(saved)
        return False, str(exc)
    if not ok:
        localnix.restore_files(saved)
        return False, L("Échec de la reconstruction — local.nix restauré.", "Rebuild failed — local.nix restored.")

    say(L("Récupération du catalogue Flathub…", "Fetching the Flathub catalog…"))
    update_appstream(say, wait_for_remote=40)
    return True, L("Support Flatpak activé.", "Flatpak support enabled.")
