"""Nix backend for the Roudix Store UI (replaces Nobara's libdnf5 backend).

State is declarative: a package is "installed" when its nixpkgs attribute name
sits in the managed block of local.nix. Install/remove edits that block, then
runs `nh os switch`; if the rebuild fails the files are restored.

Flatpak-only batches skip the rebuild: they run `flatpak install/uninstall`
directly (then clean unused runtimes) and record the result in local.nix, so a
later rebuild finds nothing to do. A batch that also touches Nix packages still
goes through `nh`, which hands the Flatpak lists to nix-flatpak.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from typing import Callable, Iterable

from . import localnix
from .models import AppEntry
from .i18n import L, LANG

INDEX_CACHE = os.path.join(localnix.BACKUP_DIR, "index.json")
FLAKE_CATALOG = os.environ.get("ROUDIX_STORE_FLAKE_CATALOG") or "/etc/roudix-store/flake-catalog.json"
INDEX_META = os.path.join(localnix.BACKUP_DIR, "index.meta.json")  # etag, last check, last failure
INDEX_URL = "https://channels.nixos.org/nixos-unstable/packages.json.br"
INDEX_MAX_AGE = 7 * 86400   # look for a newer index at most this often
INDEX_RETRY = 3600          # after a failed check (offline…), wait this long before trying again
INDEX_MIN_ENTRIES = 1000    # a cached index smaller than this is considered broken


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
        self._index_load_lock = threading.Lock()  # one (re)load at a time
        self.installed: dict[str, set[str]] = {scope: set() for scope in localnix.SCOPES}
        # what `flatpak list` reports, declared or not: {(app id, remote, "system"|"user")}
        self.flatpak_actual: set[tuple[str, str, str]] = set()
        # what the system / user profiles hold, declared in local.nix or not (Roudix modules, nix profile…):
        # package names per Nix scope, {"user": {...}, "system": {...}}
        self.nix_actual: dict[str, set[str]] = {"user": set(), "system": set()}
        # GUI apps (.desktop files) the profiles expose, whoever installed them — flakes and overlays
        # included: {scope: {desktop id: {Name, Comment, Icon, Categories, pname, version}}}
        self.nix_desktops: dict[str, dict[str, dict[str, str]]] = {"user": {}, "system": {}}
        self._catalog_launchables: set[str] = set()
        # store paths the profiles hold (exact "is this very derivation installed?" for flake packages)
        self.nix_paths: dict[str, set[str]] = {"user": set(), "system": set()}
        # the flakes the store offers, written by roudix.store.flakeSources at the last switch:
        # {flake: {"label": str, "packages": {attr: {pname, version, description, out, alias, name…}}}}
        self.flake_catalog: dict[str, dict] = {}
        self.scope = "home"  # set by the UI switch: "home" (user) or "system"
        self.reload_state()
        # The cached index is read right away (versions are right on the first display), then
        # revalidated in the background — only when it is older than INDEX_MAX_AGE.
        self._index = self._read_index_cache()
        threading.Thread(target=self._load_index, daemon=True).start()

    # ── state ────────────────────────────────────────────────────────────
    def reload_state(self, force_refresh: bool = False) -> None:
        self.installed = localnix.read_all()
        self.flatpak_actual = self._flatpak_list()
        self._load_flake_catalog()
        self._refresh_nix_actual()
        if force_refresh:
            threading.Thread(target=self._load_index, args=(True,), daemon=True).start()

    def _all_installed(self) -> set[str]:
        return self.installed["home"] | self.installed["system"]

    @staticmethod
    def _flatpak_list() -> set[tuple[str, str, str]]:
        try:
            out = subprocess.run(["flatpak", "list", "--app", "--columns=application,origin,installation"],
                                 capture_output=True, text=True, timeout=15).stdout
        except (OSError, subprocess.SubprocessError):
            return set()
        found: set[tuple[str, str, str]] = set()
        for line in out.splitlines():
            parts = [p.strip() for p in line.split("\t")]
            if len(parts) >= 3 and parts[0]:
                found.add((parts[0], parts[1], parts[2]))
        return found

    # ── nix: what is really installed (profiles), whoever put it there ───────
    _ENV_NAMES = {"system-path", "home-manager-path", "user-environment"}  # buildEnvs: look one level deeper

    @staticmethod
    def _store_pname(path: str) -> str:
        """/nix/store/<hash>-vlc-3.0.24 -> "vlc" (name up to the first version-looking part)."""
        name = os.path.basename(path.rstrip("/"))
        name = name.split("-", 1)[1] if "-" in name else name  # drop the hash
        parts: list[str] = []
        for part in name.split("-"):
            if parts and part[:1].isdigit():
                break
            parts.append(part)
        return "-".join(parts)

    @classmethod
    def _profile_paths(cls, profile: str, depth: int = 0) -> set[str]:
        """Store paths a profile / environment points to (one `nix-store --references` away)."""
        real = os.path.realpath(os.path.expanduser(profile))
        if not real.startswith("/nix/store/"):
            return set()
        tool = shutil.which("nix-store") or "/run/current-system/sw/bin/nix-store"
        try:
            out = subprocess.run([tool, "-q", "--references", real], capture_output=True, text=True, timeout=20).stdout
        except (OSError, subprocess.SubprocessError):
            return set()
        paths: set[str] = set()
        for path in out.splitlines():
            if not path.startswith("/nix/store/"):
                continue
            paths.add(path)
            if depth < 1 and cls._store_pname(path) in cls._ENV_NAMES:
                paths |= cls._profile_paths(path, depth + 1)
        return paths

    @classmethod
    def _profile_names(cls, profile: str, depth: int = 0) -> set[str]:
        """Package names a profile / environment points to."""
        return {cls._store_pname(p) for p in cls._profile_paths(profile, depth)}

    @classmethod
    def _nix_paths(cls) -> dict[str, set[str]]:
        user = os.environ.get("USER", "")
        user_profiles = ["~/.nix-profile", "~/.local/state/home-manager/gcroots/current-home/home-path"]
        if user:
            user_profiles.insert(0, f"/etc/profiles/per-user/{user}")
        found_user: set[str] = set()
        for profile in user_profiles:
            found_user |= cls._profile_paths(profile)
        return {"user": found_user, "system": cls._profile_paths("/run/current-system/sw")}

    # Store paths that are environments / generated files, never an app of their own.
    _NOT_APPS = {"system-path", "home-manager-path", "user-environment", "home-manager-files", "etc"}

    @classmethod
    def _app_dirs(cls) -> dict[str, list[str]]:
        user = os.environ.get("USER", "")
        return {
            "system": ["/run/current-system/sw/share/applications"],
            "user": ([f"/etc/profiles/per-user/{user}/share/applications"] if user else []) + [
                os.path.expanduser("~/.nix-profile/share/applications"),
                os.path.expanduser("~/.local/state/home-manager/gcroots/current-home/home-path/share/applications"),
            ],
        }

    @staticmethod
    def _parse_desktop(path: str) -> dict[str, str] | None:
        """[Desktop Entry] keys of a .desktop file, or None when it is not a visible application."""
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
        except OSError:
            return None
        data: dict[str, str] = {}
        in_entry = False
        for line in lines:
            line = line.strip()
            if line.startswith("["):
                if in_entry:
                    break
                in_entry = line == "[Desktop Entry]"
            elif in_entry and "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                data.setdefault(key.strip(), value.strip())
        if data.get("Type", "Application") != "Application":
            return None
        if data.get("NoDisplay", "").lower() == "true" or data.get("Hidden", "").lower() == "true":
            return None
        return data

    @classmethod
    def _desktop_apps(cls) -> dict[str, dict[str, dict[str, str]]]:
        """GUI apps of the system / user profiles, from their .desktop files (nixpkgs, flakes, overlays…)."""
        out: dict[str, dict[str, dict[str, str]]] = {"user": {}, "system": {}}
        for scope, folders in cls._app_dirs().items():
            for folder in folders:
                try:
                    names = sorted(os.listdir(folder))
                except OSError:
                    continue
                for fname in names:
                    if not fname.endswith(".desktop") or fname in out[scope]:
                        continue
                    real = os.path.realpath(os.path.join(folder, fname))
                    if not real.startswith("/nix/store/"):
                        continue
                    store_name = real[len("/nix/store/"):].split("/", 1)[0]  # <hash>-<name>-<version>
                    pname = cls._store_pname(store_name)
                    if not pname or pname in cls._NOT_APPS:
                        continue
                    entry = cls._parse_desktop(real)
                    if entry is None:
                        continue
                    full = store_name.split("-", 1)[1] if "-" in store_name else store_name
                    entry["pname"] = pname
                    entry["version"] = full[len(pname) + 1:] if full.startswith(pname + "-") else ""
                    out[scope][fname] = entry
        return out

    def _refresh_nix_actual(self) -> None:
        """Re-read what the profiles hold: package names plus the GUI apps they expose."""
        self.nix_desktops = self._desktop_apps()
        self.nix_paths = self._nix_paths()
        names = {scope: {self._store_pname(p) for p in paths} for scope, paths in self.nix_paths.items()}
        for scope, entries in self.nix_desktops.items():
            names[scope] |= {entry["pname"] for entry in entries.values()}
        self.nix_actual = names

    # ── nix: where an app is declared, "user" (Home Manager, modules/home) or "system" ──
    @staticmethod
    def nix_scope_key(scope: str, remote: str = "nixpkgs") -> str:
        """local.nix scope for a Nix install: nixpkgs "user" -> "home", "system" -> "system";
        a flake package goes to "home-flake" / "system-flake"."""
        if remote != "nixpkgs":
            return "home-flake" if scope == "user" else "system-flake"
        return "home" if scope == "user" else "system"

    # ── flake packages (the inputs listed in roudix.store.flakeSources) ──────
    def _load_flake_catalog(self) -> None:
        data = self._read_json(FLAKE_CATALOG)
        flakes: dict[str, dict] = {}
        if isinstance(data, dict) and isinstance(data.get("flakes"), dict):
            for flake, spec in data["flakes"].items():
                if not (localnix.NAME_RE.match(flake) and isinstance(spec, dict)):
                    continue
                packages: dict[str, dict] = {}
                for entry in spec.get("packages") or []:
                    attr = entry.get("attr", "") if isinstance(entry, dict) else ""
                    if isinstance(attr, str) and localnix.NAME_RE.match(attr):
                        packages[attr] = entry
                flakes[flake] = {"label": str(spec.get("label") or flake), "packages": packages}
        self.flake_catalog = flakes

    def flake_label(self, remote: str) -> str:
        return self.flake_catalog.get(remote, {}).get("label", remote)

    def _flake_entry(self, ref: str) -> dict | None:
        flake, _sep, attr = ref.partition("#")
        return self.flake_catalog.get(flake, {}).get("packages", {}).get(attr)

    @staticmethod
    def flake_ref_for(app: AppEntry, remote: str) -> str | None:
        return next((ref for ref in app.flake_refs if ref.partition("#")[0] == remote), None)

    def nix_remotes(self, app: AppEntry) -> list[str]:
        """Where a Nix app can come from: "nixpkgs" (unless it only exists in a flake), then its flakes."""
        remotes = [] if app.flake_only else ["nixpkgs"]
        for ref in app.flake_refs:
            flake = ref.partition("#")[0]
            if flake not in remotes:
                remotes.append(flake)
        return remotes or ["nixpkgs"]

    def source_pkg(self, app: AppEntry, remote: str) -> str:
        """The name local.nix records for `app` from `remote`: the attribute, or "<flake>#<attr>"."""
        if remote == "nixpkgs":
            return app.primary_pkg or ""
        return self.flake_ref_for(app, remote) or ""

    def add_flake_apps(self, apps: list[AppEntry]) -> None:
        """Merge the flake catalog into `apps` (idempotent). A package that also exists in nixpkgs
        (same attribute, or its `alias`) becomes one more source of that app; the others become apps
        of their own, searchable like the nixpkgs ones."""
        by_pkg: dict[str, AppEntry] = {}
        known = set()
        for app in apps:
            if app.source != "nix":
                continue
            if app.flake_only:
                known.add(app.appstream_id)
                continue
            for pkg in app.pkg_names:
                by_pkg.setdefault(pkg, app)
        changed = False
        for flake, spec in sorted(self.flake_catalog.items()):
            for attr, entry in sorted(spec["packages"].items()):
                ref = f"{flake}#{attr}"
                nixpkgs_attr = entry.get("alias") or ("" if attr == "default" else attr)
                twin = by_pkg.get(nixpkgs_attr) if nixpkgs_attr else None
                if twin is not None:
                    if ref not in twin.flake_refs:
                        twin.flake_refs.append(ref)
                    continue
                aid = f"flake:{ref}"
                if aid in known:
                    continue
                desc = str(entry.get("description") or "")
                apps.append(AppEntry(
                    appstream_id=aid, name=str(entry.get("name") or attr), summary=desc, description=desc,
                    pkg_names=[attr], homepage_url=str(entry.get("homepage") or "") or None,
                    kind="DESKTOP_APP", source="nix", flake_refs=[ref], flake_only=True,
                    candidate_version=str(entry.get("version") or "") or None, repo_ids=[flake],
                ))
                known.add(aid)
                changed = True
        if changed:
            apps.sort(key=lambda item: item.name.casefold())

    def _flake_variants_installed(self, app: AppEntry, scope: str) -> set[str]:
        """pnames of this app's flake variants that are installed (exact store path) in `scope`."""
        found: set[str] = set()
        for ref in app.flake_refs:
            entry = self._flake_entry(ref)
            if entry and entry.get("out") and entry["out"] in self.nix_paths.get(scope, ()):
                found.add(str(entry.get("pname") or ""))
        return found

    def nix_state(self, app: AppEntry, scope: str, remote: str = "nixpkgs") -> str | None:
        """"declared" when local.nix holds `app` (from `remote`) for the "user" or "system" scope (the
        store can remove it); "external" when it is installed there by something else (Roudix modules,
        nix profile…: the store only shows it); else None."""
        key = self.nix_scope_key(scope, remote)
        if remote != "nixpkgs":
            ref = self.flake_ref_for(app, remote)
            if not ref:
                return None
            if ref in self.installed.get(key, ()):
                return "declared"
            entry = self._flake_entry(ref) or {}
            if entry.get("out") and entry["out"] in self.nix_paths.get(scope, ()):
                return "external"  # this very derivation
            if app.flake_only:  # nothing in nixpkgs to confuse it with: the name is enough
                names = {str(entry.get("pname") or ""), str(entry.get("attr") or "")} - {""}
                if names & self.nix_actual.get(scope, set()):
                    return "external"
            return None
        if any(p in self.installed.get(key, ()) for p in app.pkg_names):
            return "declared"
        variants = self._flake_variants_installed(app, scope)  # same pname as the nixpkgs one, but not it
        if any(p in self.nix_actual.get(scope, ()) and p not in variants for p in app.pkg_names):
            return "external"
        # same app under another package name: its .desktop file gives it away
        if not variants and any(os.path.basename(str(l)) in self.nix_desktops.get(scope, {}) for l in app.launchables):
            return "external"
        return None

    def nix_installed_sources(self, app: AppEntry) -> list[tuple[str, str]]:
        """[(remote, scope)] where `app` is installed or declared; store-managed ones first."""
        found = []
        for order, remote in enumerate(self.nix_remotes(app)):
            for scope in ("user", "system"):
                state = self.nix_state(app, scope, remote)
                if state:
                    found.append((0 if state == "declared" else 1, order, scope, remote))
        return [(remote, scope) for _rank, _order, scope, remote in sorted(found)]

    def still_installed(self, app: AppEntry) -> bool:
        """Is `app` installed anywhere (declared or external)? Used after a removal."""
        if app.source == "flatpak":
            return bool(self.flatpak_installed_sources(app))
        if app.source == "nix":
            return bool(self.nix_installed_sources(app))
        return False

    # ── flatpak: remote (flathub / flathub-beta) x scope (system / user) ──
    @staticmethod
    def flatpak_scope_key(remote: str, system: bool) -> str:
        """local.nix scope that holds (remote, system|user) Flatpak ids."""
        return localnix.FLATPAK_SCOPES[(remote, system)]

    def flatpak_state(self, app: AppEntry, remote: str, scope: str) -> str | None:
        """"declared" (local.nix owns it, so the store can remove it), "external" (installed by
        hand) or None, for `app` from `remote` in the "system" or "user" installation."""
        key = localnix.FLATPAK_SCOPES[(remote, scope == "system")]
        if any(p in self.installed.get(key, ()) for p in app.pkg_names):
            return "declared"
        if any((p, remote, scope) in self.flatpak_actual for p in app.pkg_names):
            return "external"
        return None

    def flatpak_installed_sources(self, app: AppEntry) -> list[tuple[str, str]]:
        """[(remote, scope)] where `app` is installed or declared; store-managed ones first."""
        found = []
        for remote in localnix.FLATPAK_REMOTE_LABELS:
            for scope in ("system", "user"):
                state = self.flatpak_state(app, remote, scope)
                if state:
                    found.append((0 if state == "declared" else 1, remote, scope))
        return [(remote, scope) for _rank, remote, scope in sorted(found)]

    def set_cache_authorization(self, enabled: bool) -> None:  # pkexec handles it
        pass

    def shutdown(self) -> None:
        pass

    # ── nixpkgs index (search beyond the AppStream apps, versions) ───────
    @staticmethod
    def _read_json(path: str):
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return None

    @staticmethod
    def _write_json_atomic(path: str, data) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = f"{path}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        os.replace(tmp, path)  # an interrupted write never leaves a truncated cache behind

    def _read_index_cache(self) -> dict[str, dict] | None:
        """The index on disk, however old (stale-while-revalidate); a broken file is dropped."""
        idx = self._read_json(INDEX_CACHE)
        if isinstance(idx, dict) and len(idx) >= INDEX_MIN_ENTRIES:
            return idx
        if os.path.exists(INDEX_CACHE):
            try:
                os.remove(INDEX_CACHE)
            except OSError:
                pass
        return None

    @staticmethod
    def _download_index(meta: dict):
        """(index, etag, last_modified), or None when the server says it hasn't changed (304)."""
        headers = {"User-Agent": "roudix-store"}
        if meta.get("etag"):
            headers["If-None-Match"] = meta["etag"]
        elif meta.get("last_modified"):
            headers["If-Modified-Since"] = meta["last_modified"]
        try:
            resp = urllib.request.urlopen(urllib.request.Request(INDEX_URL, headers=headers), timeout=60)
        except urllib.error.HTTPError as exc:
            if exc.code == 304:
                return None
            raise
        with resp:
            raw = resp.read()
            etag, last_modified = resp.headers.get("ETag"), resp.headers.get("Last-Modified")
        import brotli  # python3Packages.brotli
        idx = _reduce_index(json.loads(brotli.decompress(raw)))
        if len(idx) < INDEX_MIN_ENTRIES:
            raise ValueError("the downloaded index looks empty")
        return idx, etag, last_modified

    def _load_index(self, force: bool = False) -> None:
        """Keep the cached index and revalidate it when due: a conditional request, so an unchanged
        index costs one tiny 304 instead of a full download. Offline: the cached index is kept and
        the next attempt waits INDEX_RETRY. `force` (refresh button) skips the waiting only."""
        with self._index_load_lock:
            if self._index is None:
                cached = self._read_index_cache()
                if cached is not None:
                    with self._index_lock:
                        self._index = cached
            meta = self._read_json(INDEX_META)
            meta = meta if isinstance(meta, dict) else {}
            if "checked" not in meta and os.path.exists(INDEX_CACHE):
                meta["checked"] = os.path.getmtime(INDEX_CACHE)  # cache older than the meta file
            now = time.time()
            if self._index is not None and not force:
                if now - meta.get("checked", 0) < INDEX_MAX_AGE or now - meta.get("failed", 0) < INDEX_RETRY:
                    return
            try:
                fresh = self._download_index(meta if self._index is not None else {})
                if fresh is None:  # unchanged
                    meta["checked"] = now
                    meta.pop("failed", None)
                else:
                    idx, etag, last_modified = fresh
                    self._write_json_atomic(INDEX_CACHE, idx)
                    meta = {"checked": now, "etag": etag, "last_modified": last_modified}
                    with self._index_lock:
                        self._index = idx
            except Exception:
                meta["failed"] = now  # offline: AppStream apps and the cached index still work
            try:
                self._write_json_atomic(INDEX_META, meta)
            except OSError:
                pass

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
        return False, L("Les dépôts sont gérés par le flake Roudix.", "Repositories are managed by the Roudix flake.")

    def enrich_apps(self, apps: Iterable[AppEntry]) -> None:
        if isinstance(apps, list):
            self.add_flake_apps(apps)  # in place: flake packages join the catalog before their state is computed
        apps = list(apps)
        self._catalog_launchables = {os.path.basename(str(l)) for app in apps if app.source == "nix" for l in app.launchables}
        for app in apps:
            self.refresh_app(app)

    def refresh_apps(self, apps: Iterable[AppEntry]) -> None:
        self.enrich_apps(apps)

    def refresh_app(self, app: AppEntry) -> None:
        if app.source == "flatpak":
            sources = self.flatpak_installed_sources(app)
            app.installed = bool(sources)
            app.installed_version = (
                "flatpak (" + ", ".join(f"{localnix.FLATPAK_REMOTE_LABELS[r]} {s}" for r, s in sources) + ")"
            ) if sources else None
            return  # repo_ids already holds the remotes that carry the app
        sources = self.nix_installed_sources(app)  # declared in local.nix or found in a profile
        app.installed = bool(sources)
        remotes = self.nix_remotes(app)
        entry = self._flake_entry(app.flake_refs[0]) if app.flake_only and app.flake_refs else None
        if entry:
            app.candidate_version = str(entry.get("version") or "") or app.candidate_version
            self._adopt_desktop_info(app, str(entry.get("pname") or ""))
        elif not app.flake_only:
            info = (self._index or {}).get(app.primary_pkg or "")
            if info:
                app.candidate_version = info["version"] or app.candidate_version
        declared = any(self.nix_state(app, scope, remote) == "declared" for remote in remotes for scope in ("user", "system"))
        app.installed_version = (app.candidate_version or ("declared" if declared else "installed")) if app.installed else None
        app.repo_ids = remotes

    def _adopt_desktop_info(self, app: AppEntry, pname: str) -> None:
        """A flake-only app has no AppStream data: borrow its icon, categories and launcher from the
        .desktop file once it is installed."""
        for entries in self.nix_desktops.values():
            for fname, desk in entries.items():
                if pname and desk.get("pname") == pname:
                    if fname not in app.launchables:
                        app.launchables.append(fname)
                    icon = desk.get("Icon") or ""
                    if icon and not app.icon_name and not app.icon_path:
                        if icon.startswith("/"):
                            app.icon_path = icon if os.path.exists(icon) else None
                        else:
                            app.icon_name = icon
                    if not app.categories and desk.get("Categories"):
                        app.categories = [c for c in desk["Categories"].split(";") if c]

    def get_installed_packages(self, repo_id: str = "__all__") -> list[AppEntry]:
        idx = self._index or {}
        out = []
        for attr in sorted(self._all_installed()):
            info = idx.get(attr) or {"desc": "", "long": "", "home": "", "version": ""}
            out.append(self._entry_from_index(attr, info))
        return out + self._external_apps(set(self._all_installed()))

    def _external_apps(self, declared: set[str]) -> list[AppEntry]:
        """GUI apps installed in the profiles that the AppStream catalog doesn't know (flakes, overlays,
        Roudix modules…): one entry per package so they show up under Installed."""
        flake_pnames = {str(e.get("pname") or "") for spec in self.flake_catalog.values() for e in spec["packages"].values()}
        grouped: dict[str, tuple[dict[str, str], list[str]]] = {}
        for scope in ("system", "user"):
            for fname, entry in self.nix_desktops.get(scope, {}).items():
                if fname in self._catalog_launchables or entry["pname"] in declared or entry["pname"] in flake_pnames:
                    continue
                grouped.setdefault(entry["pname"], (entry, []))[1].append(fname)
        out: list[AppEntry] = []
        for pname, (entry, ids) in sorted(grouped.items()):
            fr = LANG == "fr"
            name = (entry.get("Name[fr]") if fr else None) or entry.get("Name") or pname
            summary = (entry.get("Comment[fr]") if fr else None) or entry.get("Comment") or entry.get("GenericName") or ""
            icon = entry.get("Icon") or ""
            out.append(AppEntry(
                appstream_id=f"external:{pname}", name=name, summary=summary, description=summary,
                pkg_names=[pname], categories=[c for c in entry.get("Categories", "").split(";") if c],
                launchables=sorted(set(ids)),
                icon_name=None if icon.startswith("/") else (icon or None),
                icon_path=icon if icon.startswith("/") and os.path.exists(icon) else None,
                kind="DESKTOP_APP", installed=True, installed_version=entry.get("version") or "installed",
            ))
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

    @staticmethod
    def _apply_one(state: dict[str, set[str]], action: str, pkg: str, scope: str) -> str | None:
        """Apply one change to a {scope: names} state; returns an error text or None."""
        scope = scope if scope in state else "home"
        if action == "install":
            state[scope].add(pkg)
        elif action == "remove":
            if scope in localnix.FLATPAK_SCOPE_INFO or scope in localnix.FLAKE_SCOPES:
                state[scope].discard(pkg)  # stable/beta of one app id, or one flake package: independent
            else:
                for s in ("home", "system"):
                    state[s].discard(pkg)
        else:
            return L(f"« {action} » n'est pas géré sur Roudix (les mises à jour viennent du flake).", f"'{action}' is not supported on Roudix (updates come from the flake).")
        return None

    def apply_changes(self, changes, event_cb: Callable[[dict], None] | None = None) -> tuple[bool, str]:
        """changes: [(action, attr, scope)].

        Flatpak-only batch: `flatpak install/uninstall` directly, no rebuild.
        Anything touching Nix packages: one local.nix write + ONE `nh os switch`."""
        def say(msg: str) -> None:
            if event_cb:
                event_cb({"event": "log", "message": msg})

        new = {s: set(v) for s, v in self.installed.items()}
        for action, pkg, scope in changes:
            error = self._apply_one(new, action, pkg, scope)
            if error:
                return False, error
        flatpak_only = bool(changes) and all(scope in localnix.FLATPAK_SCOPE_INFO for _a, _p, scope in changes)
        if new == self.installed and not flatpak_only:  # flatpak ones may still act on what is really installed
            return True, L("Rien à changer.", "Nothing to change.")
        if all(new[s] == self.installed[s] for s in localnix.NIX_SCOPES):
            return self._apply_flatpak_direct(changes, say)

        saved = localnix.backup_files()
        res = localnix.write_all(new)
        if res is not True:
            localnix.restore_files(saved)
            return False, L(f"Impossible d'écrire local.nix : {res}", f"Could not write local.nix: {res}")
        for scope in new:
            if new[scope] != self.installed[scope]:
                changed = ', '.join(sorted(new[scope] ^ self.installed[scope]))
                say(L(f"local.nix mis à jour ({scope}) : {changed}", f"local.nix updated ({scope}): {changed}"))
        if any(new[k] != self.installed[k] for k in localnix.FLATPAK_SCOPE_INFO):
            say(L("Les apps Flatpak sont installées/supprimées par nix-flatpak pendant le switch — ça peut prendre un moment.", "Flatpak apps are installed/removed by nix-flatpak during the switch — this can take a while."))

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
        self.installed = new
        self.flatpak_actual = self._flatpak_list()
        self._refresh_nix_actual()
        return True, L("Appliqué.", "Applied.")

    # ── flatpak without a rebuild ───────────────────────────────────────
    @staticmethod
    def _run_flatpak(flatpak: str, args: list[str], say: Callable[[str], None]) -> int:
        say("$ flatpak " + " ".join(args))
        try:
            proc = subprocess.Popen([flatpak, *args], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            for raw in proc.stdout:
                # progress bars redraw one line with \r: keep the last state of each
                line = next((p.strip() for p in reversed(raw.split("\r")) if p.strip()), "")
                if line:
                    say(line)
            return proc.wait()
        except OSError as exc:
            say(str(exc))
            return 1

    @staticmethod
    def _flatpak_branch(flatpak: str, pkg: str, remote: str, scope: str) -> str | None:
        """Branch of the installed ref, so an uninstall hits exactly that one (stable vs beta)."""
        try:
            out = subprocess.run([flatpak, "list", "--app", f"--{scope}", "--columns=application,origin,branch"],
                                 capture_output=True, text=True, timeout=15).stdout
        except (OSError, subprocess.SubprocessError):
            return None
        for line in out.splitlines():
            parts = [p.strip() for p in line.split("\t")]
            if len(parts) >= 3 and parts[0] == pkg and parts[1] == remote:
                return parts[2]
        return None

    def _ensure_flatpak_remote(self, flatpak: str, remote: str, scope: str, say: Callable[[str], None]) -> bool:
        try:
            out = subprocess.run([flatpak, "remotes", f"--{scope}", "--columns=name"],
                                 capture_output=True, text=True, timeout=15).stdout
        except (OSError, subprocess.SubprocessError):
            out = ""
        if remote in {line.strip() for line in out.splitlines()}:
            return True
        url = localnix.FLATPAK_REMOTE_URLS.get(remote)
        if not url:
            say(L(f"Dépôt Flatpak inconnu « {remote} ».", f"Unknown Flatpak remote '{remote}'."))
            return False
        say(L(f"Ajout du dépôt {remote} à l'installation {scope}…", f"Adding the {remote} remote to the {scope} installation…"))
        return self._run_flatpak(flatpak, ["remote-add", "--if-not-exists", f"--{scope}", remote, url], say) == 0

    def _apply_flatpak_direct(self, changes, say: Callable[[str], None]) -> tuple[bool, str]:
        flatpak = shutil.which("flatpak")
        if not flatpak:
            return False, L("flatpak est introuvable dans le PATH.", "flatpak was not found in PATH.")
        say(L("Flatpak uniquement — application directe avec flatpak, sans reconstruction.", "Flatpak only — applying with flatpak directly, no rebuild."))
        actual = self._flatpak_list()
        final = {s: set(v) for s, v in self.installed.items()}
        failures: list[str] = []
        cleanup: set[str] = set()
        for action, pkg, key in changes:
            if key not in localnix.FLATPAK_SCOPE_INFO:
                continue
            remote, scope = localnix.FLATPAK_SCOPE_INFO[key]
            where = f"{localnix.FLATPAK_REMOTE_LABELS.get(remote, remote)}, {scope}"
            present = (pkg, remote, scope) in actual
            if action == "install":
                if present:
                    say(L(f"{pkg} est déjà installé ({where}) — enregistrement seulement.", f"{pkg} is already installed ({where}) — only recording it."))
                else:
                    if not self._ensure_flatpak_remote(flatpak, remote, scope, say):
                        failures.append(L(f"{pkg} : dépôt {remote} indisponible", f"{pkg}: remote {remote} unavailable"))
                        continue
                    ref = f"{pkg}//beta" if remote == "flathub-beta" else pkg
                    code = self._run_flatpak(flatpak, ["install", "--noninteractive", "-y", f"--{scope}", remote, ref], say)
                    if code != 0:
                        hint = L(" (les installations système demandent une autorisation via polkit)", " (system installs ask for authorization through polkit)") if scope == "system" else ""
                        failures.append(L(f"{pkg} : échec de flatpak install{hint}", f"{pkg}: flatpak install failed{hint}"))
                        continue
                final[key].add(pkg)
            else:  # remove
                if present:
                    branch = self._flatpak_branch(flatpak, pkg, remote, scope)
                    ref = f"{pkg}//{branch}" if branch else pkg
                    code = self._run_flatpak(flatpak, ["uninstall", "--noninteractive", "-y", f"--{scope}", ref], say)
                    if code != 0:
                        failures.append(L(f"{pkg} : échec de flatpak uninstall", f"{pkg}: flatpak uninstall failed"))
                        continue
                    cleanup.add(scope)
                else:
                    say(L(f"{pkg} n'est pas installé ({where}) — retrait de local.nix seulement.", f"{pkg} is not installed ({where}) — only dropping it from local.nix."))
                final[key].discard(pkg)
        for scope in sorted(cleanup):
            say(L(f"Nettoyage des runtimes inutilisés ({scope})…", f"Cleaning unused runtimes ({scope})…"))
            self._run_flatpak(flatpak, ["uninstall", "--unused", "--noninteractive", "-y", f"--{scope}"], say)

        if final != self.installed:
            saved = localnix.backup_files()
            res = localnix.write_all(final)
            if res is not True:
                localnix.restore_files(saved)
                return False, L(f"Les changements Flatpak ont été appliqués mais local.nix n'a pas pu être écrit : {res}", f"Flatpak changes were applied but local.nix could not be written: {res}")
            for key in localnix.FLATPAK_SCOPE_INFO:
                if final[key] != self.installed[key]:
                    changed = ', '.join(sorted(final[key] ^ self.installed[key]))
                    say(L(f"local.nix mis à jour ({key}) : {changed}", f"local.nix updated ({key}): {changed}"))
            self.installed = final
        self.flatpak_actual = self._flatpak_list()
        if failures:
            return False, "; ".join(failures)
        return True, L("Appliqué.", "Applied.")
