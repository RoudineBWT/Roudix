"""Nix backend for the Roudix Store UI (replaces Nobara's libdnf5 backend).

State is declarative: a package is "installed" when its nixpkgs attribute name
sits in the managed block of local.nix. Install/remove edits that block, then
runs `nh os switch`; if the rebuild fails the files are restored.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import urllib.request
from typing import Callable, Iterable

from . import localnix
from .models import AppEntry

INDEX_CACHE = os.path.join(localnix.BACKUP_DIR, "index.json")
INDEX_URL = "https://channels.nixos.org/nixos-unstable/packages.json.br"
INDEX_MAX_AGE = 7 * 86400


class NixUnavailable(RuntimeError):
    pass


def _reduce_index(raw: dict) -> dict:
    out: dict[str, dict] = {}
    for attr, pkg in raw.get("packages", raw).items():
        meta = pkg.get("meta") or {}
        desc = meta.get("description") or ""
        if not desc or not localnix.NAME_RE.match(attr):
            continue
        home = meta.get("homepage")
        if isinstance(home, list):
            home = home[0] if home else ""
        out[attr] = {
            "version": pkg.get("version", ""),
            "desc": desc,
            "long": (meta.get("longDescription") or "")[:1500],
            "home": home or "",
            "prog": meta.get("mainProgram", ""),
        }
    return out


class NixBackend:
    def __init__(self) -> None:
        self._index: dict[str, dict] | None = None
        self._index_lock = threading.Lock()
        self.installed: dict[str, set[str]] = {"home": set(), "system": set(), "flatpak": set()}
        self.flatpak_actual: set[str] = set()  # what `flatpak list` reports, declared or not
        self.scope = "home"  # set by the UI switch: "home" (user) or "system"
        self.reload_state()
        threading.Thread(target=self._load_index, daemon=True).start()

    # ── state ────────────────────────────────────────────────────────────
    def reload_state(self, force_refresh: bool = False) -> None:
        self.installed = localnix.read_all()
        self.flatpak_actual = self._flatpak_list()
        if force_refresh:
            threading.Thread(target=self._load_index, args=(True,), daemon=True).start()

    def _all_installed(self) -> set[str]:
        return self.installed["home"] | self.installed["system"]

    @staticmethod
    def _flatpak_list() -> set[str]:
        try:
            out = subprocess.run(["flatpak", "list", "--app", "--columns=application"],
                                 capture_output=True, text=True, timeout=15).stdout
        except (OSError, subprocess.SubprocessError):
            return set()
        return {line.strip() for line in out.splitlines() if line.strip()}

    def flatpak_installed(self) -> set[str]:
        return self.installed["flatpak"] | self.flatpak_actual

    def is_declared(self, app: AppEntry) -> bool:
        """True when local.nix owns this app, so the store can remove it."""
        scope = "flatpak" if app.source == "flatpak" else None
        names = self.installed["flatpak"] if scope else self._all_installed()
        return any(p in names for p in app.pkg_names)

    def set_cache_authorization(self, enabled: bool) -> None:  # pkexec handles it
        pass

    def shutdown(self) -> None:
        pass

    # ── nixpkgs index (search beyond the AppStream apps, versions) ───────
    def _load_index(self, force: bool = False) -> None:
        try:
            if not force and os.path.exists(INDEX_CACHE) and time.time() - os.path.getmtime(INDEX_CACHE) < INDEX_MAX_AGE:
                with open(INDEX_CACHE, encoding="utf-8") as fh:
                    idx = json.load(fh)
            else:
                import brotli  # python3Packages.brotli
                req = urllib.request.Request(INDEX_URL, headers={"User-Agent": "roudix-store"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    idx = _reduce_index(json.loads(brotli.decompress(resp.read())))
                os.makedirs(localnix.BACKUP_DIR, exist_ok=True)
                with open(INDEX_CACHE, "w", encoding="utf-8") as fh:
                    json.dump(idx, fh)
        except Exception:
            return  # offline: AppStream apps still work, only extra search is lost
        with self._index_lock:
            self._index = idx

    def _entry_from_index(self, attr: str, info: dict) -> AppEntry:
        return AppEntry(
            appstream_id=attr, name=attr, summary=info["desc"],
            description=info["long"] or info["desc"], pkg_names=[attr],
            homepage_url=info["home"] or None, kind="PACKAGE",
            candidate_version=info["version"] or None,
            installed=attr in self._all_installed(),
            installed_version=(info["version"] or "declared") if attr in self._all_installed() else None,
            repo_ids=["nixpkgs"],
        )

    # ── what the UI asks for ─────────────────────────────────────────────
    def get_repositories(self) -> list[dict[str, str]]:
        return []

    def set_repository_enabled(self, repo_id: str, enabled: bool, event_cb=None) -> tuple[bool, str]:
        return False, "Repositories are managed by the Roudix flake."

    def enrich_apps(self, apps: Iterable[AppEntry]) -> None:
        for app in apps:
            self.refresh_app(app)

    def refresh_apps(self, apps: Iterable[AppEntry]) -> None:
        self.enrich_apps(apps)

    def refresh_app(self, app: AppEntry) -> None:
        if app.source == "flatpak":
            inst = self.flatpak_installed()
            app.installed = any(p in inst for p in app.pkg_names)
            app.installed_version = "flatpak" if app.installed else None
            app.repo_ids = ["flathub"]
            return
        inst = self._all_installed()
        app.installed = any(p in inst for p in app.pkg_names)
        info = (self._index or {}).get(app.primary_pkg or "")
        if info:
            app.candidate_version = info["version"] or app.candidate_version
        app.installed_version = (app.candidate_version or "declared") if app.installed else None
        app.repo_ids = ["nixpkgs"]

    def get_installed_packages(self, repo_id: str = "__all__") -> list[AppEntry]:
        idx = self._index or {}
        out = []
        for attr in sorted(self._all_installed()):
            info = idx.get(attr) or {"desc": "", "long": "", "home": "", "version": ""}
            out.append(self._entry_from_index(attr, info))
        return out

    def get_upgradable_packages(self, repo_id: str = "__all__") -> list[AppEntry]:
        return []  # updates come from `nix flake update` / roudix autoupdate

    def search_packages(self, query: str, repo_id: str = "__all__", limit: int = 200) -> list[AppEntry]:
        idx = self._index
        q = query.strip().lower()
        if not idx or len(q) < 2:
            return []
        scored = []
        for attr, info in idx.items():
            a = attr.lower()
            if a == q or info["prog"].lower() == q:
                s = 0
            elif a.startswith(q):
                s = 1
            elif q in a:
                s = 2
            elif q in info["desc"].lower():
                s = 3
            else:
                continue
            scored.append((s, len(attr), attr))
        scored.sort()
        return [self._entry_from_index(a, idx[a]) for _s, _l, a in scored[:limit]]

    # ── install / remove ─────────────────────────────────────────────────
    def execute_action(self, action: str, pkg_name, event_cb: Callable[[dict], None] | None = None) -> tuple[bool, str]:
        targets = [pkg_name] if isinstance(pkg_name, str) else list(pkg_name)
        return self.apply_changes([(action, p, self.scope) for p in targets], event_cb)

    def apply_changes(self, changes, event_cb: Callable[[dict], None] | None = None) -> tuple[bool, str]:
        """changes: [(action, attr, scope)]. One local.nix write + ONE `nh os switch`."""
        def say(msg: str) -> None:
            if event_cb:
                event_cb({"event": "log", "message": msg})

        new = {s: set(v) for s, v in self.installed.items()}
        for action, pkg, scope in changes:
            scope = scope if scope in new else "home"
            if action == "install":
                new[scope].add(pkg)
            elif action == "remove":
                for s in new:
                    new[s].discard(pkg)
            else:
                return False, f"'{action}' is not supported on Roudix (updates come from the flake)."
        if new == self.installed:
            return True, "Nothing to change."

        saved = localnix.backup_files()
        res = localnix.write_all(new)
        if res is not True:
            localnix.restore_files(saved)
            return False, f"Could not write local.nix: {res}"
        for scope in new:
            if new[scope] != self.installed[scope]:
                say(f"local.nix updated ({scope}): {', '.join(sorted(new[scope] ^ self.installed[scope]))}")
        if new["flatpak"] != self.installed["flatpak"]:
            say("Flatpak apps are installed/removed by nix-flatpak during the switch — this can take a while.")

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
            return False, "Rebuild failed — local.nix restored."
        self.installed = new
        self.flatpak_actual = self._flatpak_list()
        return True, "Applied."
