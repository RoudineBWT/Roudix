from __future__ import annotations

import os
import platform
import re
import sys
from urllib.parse import unquote, urlparse
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .models import AppEntry


DEBUG_ICONS = os.environ.get("APPSTORE_DEBUG_ICONS") == "1"
DEBUG_ICON_FILTER = os.environ.get("APPSTORE_DEBUG_ICON_FILTER", "").strip().casefold()
_SEEN_ICON_DEBUG: set[tuple[str | None, str | None, str]] = set()


def _debug_enabled_for(entry_name: str | None, app_id: str | None, pkg_names: list[str] | None) -> bool:
    if not DEBUG_ICONS:
        return False
    haystack = " ".join(
        [entry_name or "", app_id or "", " ".join(pkg_names or [])]
    ).casefold()
    return not DEBUG_ICON_FILTER or DEBUG_ICON_FILTER in haystack


def _icon_debug(entry_name: str | None, app_id: str | None, pkg_names: list[str] | None, message: str) -> None:
    if not _debug_enabled_for(entry_name, app_id, pkg_names):
        return
    key = (entry_name, app_id, message)
    if key in _SEEN_ICON_DEBUG:
        return
    _SEEN_ICON_DEBUG.add(key)
    print(f"[ICON DEBUG] {entry_name or app_id or '<unknown>'}: {message}", file=sys.stderr)


class AppStreamUnavailable(RuntimeError):
    pass


class _HTMLToTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag in {"p", "div", "section", "br", "ul", "ol"}:
            self.parts.append("\n")
        elif tag == "li":
            self.parts.append("\n• ")

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag in {"p", "div", "section"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        self.parts.append(data)

    def get_text(self) -> str:
        text = unescape("".join(self.parts))
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        return text.strip()


FLATPAK_APPSTREAM = "/var/lib/flatpak/appstream"
# Remotes the store knows about, in display order. libappstream's pool can't be
# used for them: every Flatpak remote reports origin="flatpak", a stable/beta pair
# of the same app collapses into ONE pool component, and a user remote named like
# a system one replaces it. So each remote's appstream.xml.gz is parsed on its own.
FLATPAK_REMOTES = ("flathub", "flathub-beta")


def _flatpak_roots() -> list[Path]:
    """appstream dirs of the system installation, then of the user installation."""
    data_home = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return [Path(FLATPAK_APPSTREAM), Path(data_home) / "flatpak" / "appstream"]


def _flatpak_icon_by_id(active: Path, app_id: str) -> str | None:
    """Flathub cached icons are <app-id>.png under <active>/icons/<size>/ (or icons/<origin>/<size>/)."""
    icons = active / "icons"
    if not icons.is_dir():
        return None
    for size in ("128x128", "64x64", "256x256"):
        for pattern in (f"{size}/{app_id}.png", f"*/{size}/{app_id}.png"):
            match = next(icons.glob(pattern), None)
            if match:
                return str(match)
    return None


class AppStreamCatalog:
    def __init__(self) -> None:
        try:
            import gi

            gi.require_version("AppStream", "1.0")
            from gi.repository import AppStream  # type: ignore
        except Exception as exc:  # pragma: no cover - environment dependent
            raise AppStreamUnavailable(
                "Could not import AppStream GI bindings. Install the 'appstream' package "
                "and ensure AppStream-1.0.typelib is available."
            ) from exc

        self.AppStream = AppStream
        self.pool = AppStream.Pool()
        # nixos-appstream-data: AppStream catalog for nixpkgs (pkgname == nixpkgs
        # attribute, icons shipped alongside). The Nix wrapper exports its path.
        root = os.environ.get("ROUDIX_STORE_CATALOG")
        if root and os.path.isdir(root):
            self.pool.reset_extra_data_locations()
            self.pool.set_load_std_data_locations(False)  # no OS desktop files/metainfo noise
            self.pool.add_extra_data_location(root, AppStream.FormatStyle.CATALOG)
        # Flatpak remotes are read separately (see _load_flatpak), never through the pool.
        self.pool.remove_flags(AppStream.PoolFlags.LOAD_FLATPAK)

    def load(self) -> list[AppEntry]:
        self.pool.load()
        apps: list[AppEntry] = []
        for component in self._as_list(self.pool.get_components()):
            entry = self._component_to_entry(component)
            if entry:
                apps.append(entry)

        apps.extend(self._load_flatpak())
        apps.sort(key=lambda item: item.name.casefold())
        return apps

    def _load_flatpak(self) -> list[AppEntry]:
        """One entry per (app id, remote): stable and beta are separate apps, and the
        system and user copies of a remote are merged (the install scope is the user's pick)."""
        out: list[AppEntry] = []
        seen: set[tuple[str, str]] = set()
        arch = platform.machine()
        for root in _flatpak_roots():
            if not root.is_dir():
                continue
            for remote in FLATPAK_REMOTES:
                # layout: <root>/<remote>/<arch>/active/appstream.xml.gz (+ icons/)
                for active in sorted(root.glob(f"{remote}/{arch}/active")):
                    xml = next((f for f in (active / "appstream.xml.gz", active / "appstream.xml") if f.is_file()), None)
                    if xml is None:
                        continue
                    for component in self._parse_flatpak_file(xml, remote):
                        entry = self._flatpak_entry(component, remote, active)
                        if entry is None:
                            continue
                        key = (entry.appstream_id, remote)
                        if key in seen:
                            continue
                        seen.add(key)
                        out.append(entry)
        return out

    def _parse_flatpak_file(self, xml: Path, remote: str) -> list[Any]:
        from gi.repository import Gio  # type: ignore

        metadata = self.AppStream.Metadata()
        metadata.set_format_style(self.AppStream.FormatStyle.CATALOG)
        try:
            metadata.parse_file(Gio.File.new_for_path(str(xml)), self.AppStream.FormatKind.XML)
        except Exception as exc:  # a broken remote must not take the whole store down
            print(f"[roudix-store] could not read {xml}: {exc}", file=sys.stderr)
            return []
        return self._as_list(metadata.get_components())

    def search(self, query: str) -> list[AppEntry]:
        if not query.strip():
            return self.load()
        apps: list[AppEntry] = []
        for component in self._as_list(self.pool.search(query)):
            entry = self._component_to_entry(component)
            if entry:
                apps.append(entry)
        apps.sort(key=lambda item: item.name.casefold())
        return apps

    def _component_to_entry(self, component: Any) -> AppEntry | None:
        name = self._safe_text(getattr(component, "get_name", lambda: None)())
        summary = self._safe_text(getattr(component, "get_summary", lambda: None)())
        description = self._normalize_description(getattr(component, "get_description", lambda: None)())
        pkg_names = [str(item) for item in self._as_list(getattr(component, "get_pkgnames", lambda: [])())]

        if self._flatpak_bundle(component) is not None:
            return None  # Flatpak apps are handled by _load_flatpak

        if not name or not pkg_names:
            return None


        if not self._looks_like_user_app(component, pkg_names):
            return None

        screenshots = self._extract_screenshots(component)
        icon_name, icon_path, icon_url = self._extract_icon(component, name, pkg_names)
        launchables = self._extract_launchables(component)
        categories = [str(item) for item in self._as_list(getattr(component, "get_categories", lambda: [])())]
        keywords = self._extract_keywords(component)
        homepage_url = self._extract_homepage(component)

        return AppEntry(
            appstream_id=self._safe_text(getattr(component, "get_id", lambda: None)()) or pkg_names[0],
            name=name,
            summary=summary or "No summary available.",
            description=description or summary or "No description available.",
            pkg_names=pkg_names,
            categories=categories,
            keywords=keywords,
            screenshots=screenshots,
            launchables=launchables,
            icon_name=icon_name,
            icon_path=icon_path,
            icon_url=icon_url,
            homepage_url=homepage_url,
            kind=self._extract_kind(component),
        )

    def _flatpak_bundle(self, component: Any) -> str | None:
        try:
            bundle = component.get_bundle(self.AppStream.BundleKind.FLATPAK)
        except Exception:
            return None
        return str(bundle.get_id()) if bundle is not None else None

    def _flatpak_entry(self, component: Any, remote: str, active: Path) -> AppEntry | None:
        """Desktop apps of one remote (no runtimes/addons)."""
        if not self._extract_kind(component).endswith("DESKTOP_APP"):
            return None
        name = self._safe_text(getattr(component, "get_name", lambda: None)())
        if not name:
            return None
        app_id = (self._safe_text(component.get_id()) or "").removesuffix(".desktop")
        if not app_id:
            return None
        if remote == "flathub-beta":
            name = f"{name} (Beta)"  # same app id as the stable build, so tell them apart in the lists
        summary = self._safe_text(getattr(component, "get_summary", lambda: None)())
        description = self._normalize_description(getattr(component, "get_description", lambda: None)())
        icon_name, icon_path, icon_url = None, _flatpak_icon_by_id(active, app_id), None
        if not icon_path:
            icon_name, icon_path, icon_url = self._extract_icon(component, name, [app_id])
        return AppEntry(
            appstream_id=app_id,
            name=name,
            summary=summary or "No summary available.",
            description=description or summary or "No description available.",
            pkg_names=[app_id],
            categories=[str(c) for c in self._as_list(getattr(component, "get_categories", lambda: [])())],
            keywords=self._extract_keywords(component),
            screenshots=self._extract_screenshots(component),
            launchables=self._extract_launchables(component) or [f"{app_id}.desktop"],
            icon_name=icon_name, icon_path=icon_path, icon_url=icon_url,
            homepage_url=self._extract_homepage(component),
            kind="DESKTOP_APP", repo_ids=[remote], source="flatpak",
        )

    def _extract_kind(self, component: Any) -> str:
        get_kind = getattr(component, "get_kind", None)
        if get_kind is None:
            return "UNKNOWN"
        try:
            kind = get_kind()
        except Exception:
            return "UNKNOWN"
        name = getattr(kind, "value_name", None) or getattr(kind, "name", None)
        if isinstance(name, str) and name:
            return name.rsplit(".", 1)[-1].upper()
        text = str(kind).rsplit(".", 1)[-1].strip()
        return (text or "UNKNOWN").upper()

    def _looks_like_user_app(self, component: Any, pkg_names: list[str]) -> bool:
        launchables = self._extract_launchables(component)
        categories = [str(item) for item in self._as_list(getattr(component, "get_categories", lambda: [])())]
        screenshots = self._extract_screenshots(component)
        component_id = self._safe_text(getattr(component, "get_id", lambda: None)()) or ""

        if launchables:
            return True
        if screenshots and categories:
            return True
        if component_id.endswith(".desktop"):
            return True

        blocked_prefixes = ("lib", "font-", "golang-", "perl-", "python3-")
        primary_pkg = pkg_names[0]
        if primary_pkg.startswith(blocked_prefixes):
            return False
        return bool(categories)

    def _extract_keywords(self, component: Any) -> list[str]:
        keywords = getattr(component, "get_keywords", lambda: [])()
        if isinstance(keywords, dict):
            flat: list[str] = []
            for values in keywords.values():
                flat.extend(str(item) for item in self._as_list(values))
            return flat
        return [str(item) for item in self._as_list(keywords)]

    def _extract_homepage(self, component: Any) -> str | None:
        get_url = getattr(component, "get_url", None)
        if get_url is None:
            return None
        url_kind = getattr(self.AppStream, "UrlKind", None)
        if url_kind is not None and hasattr(url_kind, "HOMEPAGE"):
            try:
                return self._safe_text(get_url(url_kind.HOMEPAGE))
            except Exception:
                return None
        return None

    def _extract_launchables(self, component: Any) -> list[str]:
        """desktop-ids declared by the component (AppStream Launchable.get_entries())."""
        values: list[str] = []
        for item in self._as_list(getattr(component, "get_launchables", lambda: [])()):
            kind = getattr(item, "get_kind", lambda: None)()
            kind_name = str(getattr(kind, "value_nick", None) or getattr(kind, "name", None) or kind).lower()
            if kind is not None and "desktop" not in kind_name:
                continue  # service / cockpit-manifest / url launchables can't be opened
            try:
                entries = item.get_entries()
            except Exception:
                entries = []
            for entry in self._as_list(entries):
                if entry:
                    values.append(str(entry))
        return values

    def _extract_screenshots(self, component: Any) -> list[str]:
        screenshots = self._as_list(getattr(component, "get_screenshots_all", lambda: [])())
        urls: list[str] = []
        for screenshot in screenshots:
            seen: set[str] = set()
            for image in self._iter_screenshot_images(screenshot):
                value = self._extract_media_ref(image)
                if value and value not in seen:
                    urls.append(value)
                    seen.add(value)
                    break
        return urls

    def _iter_screenshot_images(self, screenshot: Any) -> list[Any]:
        values: list[Any] = []
        for method_name in ("get_images",):
            method = getattr(screenshot, method_name, None)
            if callable(method):
                try:
                    values.extend(self._as_list(method()))
                except Exception:
                    pass
        for method_name, args in (
            ("get_source_image", ()),
            ("get_image", (1120, 630, 1.0)),
            ("get_image", (800, 600, 1.0)),
            ("get_image", (624, 351, 1.0)),
        ):
            method = getattr(screenshot, method_name, None)
            if callable(method):
                try:
                    image = method(*args)
                except Exception:
                    image = None
                if image is not None:
                    values.append(image)
        return values

    def _extract_icon(self, component: Any, entry_name: str | None, pkg_names: list[str]) -> tuple[str | None, str | None, str | None]:
        app_id = self._safe_text(getattr(component, "get_id", lambda: None)())
        icons = self._as_list(getattr(component, "get_icons", lambda: [])())
        if _debug_enabled_for(entry_name, app_id, pkg_names):
            self._debug_component_icon_info(component, entry_name, app_id, pkg_names, icons)

        get_icon_by_size = getattr(component, "get_icon_by_size", None)
        if get_icon_by_size is not None:
            for size in ((128, 128), (64, 64), (48, 48)):
                try:
                    icon = get_icon_by_size(*size)
                    resolved = self._resolve_icon(icon, entry_name, app_id, pkg_names)
                    if resolved != (None, None, None):
                        return resolved
                except Exception:
                    pass

        for icon in icons:
            resolved = self._resolve_icon(icon, entry_name, app_id, pkg_names)
            if resolved != (None, None, None):
                return resolved
        return None, None, None

    def _resolve_icon(
        self,
        icon: Any,
        entry_name: str | None,
        app_id: str | None,
        pkg_names: list[str],
    ) -> tuple[str | None, str | None, str | None]:
        if icon is None:
            return None, None, None

        value = self._extract_media_ref(icon)
        if value:
            _icon_debug(entry_name, app_id, pkg_names, f"AppStream icon ref={value!r}")
            if value.startswith(("http://", "https://")):
                _icon_debug(entry_name, app_id, pkg_names, "resolved icon as remote URL")
                return None, None, value
            if value.startswith("file://"):
                parsed = urlparse(value)
                local_path = unquote(parsed.path or "")
                _icon_debug(entry_name, app_id, pkg_names, f"parsed file:// icon URI to local path {local_path!r}")
                if local_path and Path(local_path).is_file():
                    _icon_debug(entry_name, app_id, pkg_names, f"resolved icon as local file {local_path}")
                    return None, local_path, None
                _icon_debug(entry_name, app_id, pkg_names, f"file:// icon URI did not resolve to a file: {local_path!r}")
            if Path(value).is_file():
                _icon_debug(entry_name, app_id, pkg_names, f"resolved icon as local file {value}")
                return None, value, None
            # non-file values are usually themed icon names or cached filenames
            if "/" not in value:
                cache_path = self._find_cached_icon_path(value, entry_name, app_id, pkg_names)
                if cache_path:
                    _icon_debug(entry_name, app_id, pkg_names, f"resolved icon from AppStream cache {cache_path}")
                    return None, cache_path, None
                _icon_debug(entry_name, app_id, pkg_names, f"treating icon ref as themed icon name {value!r}")
                return value, None, None
            _icon_debug(entry_name, app_id, pkg_names, f"treating non-file path-like icon ref as path {value!r}")
            return None, value, None

        for attr in ("get_name",):
            fn = getattr(icon, attr, None)
            if callable(fn):
                try:
                    icon_name = fn()
                except Exception:
                    icon_name = None
                if icon_name:
                    _icon_debug(entry_name, app_id, pkg_names, f"resolved icon from get_name() -> {icon_name!r}")
                    return str(icon_name), None, None
        return None, None, None

    def _normalize_icon_name(self, value: str | None) -> str | None:
        value = self._safe_text(value)
        if not value:
            return None
        path_name = Path(value).name
        for suffix in (".png", ".svg", ".svgz", ".xpm", ".jpg", ".jpeg", ".webp"):
            if path_name.lower().endswith(suffix):
                return path_name[: -len(suffix)] or None
        return path_name

    def _find_cached_icon_path(
        self,
        filename: str,
        entry_name: str | None,
        app_id: str | None,
        pkg_names: list[str],
    ) -> str | None:
        search_roots = [
            *([os.path.join(os.environ["ROUDIX_STORE_CATALOG"], "icons")] if os.environ.get("ROUDIX_STORE_CATALOG") else []),
            "/var/cache/swcatalog/icons",
            "/var/lib/swcatalog/icons",
            "/usr/share/swcatalog/icons",
            "/var/cache/app-info/icons",
            "/usr/share/app-info/icons",
        ]
        for root in search_roots:
            path = Path(root)
            if not path.exists():
                continue
            try:
                match = next(path.rglob(filename), None)
            except Exception as exc:
                _icon_debug(entry_name, app_id, pkg_names, f"cache lookup failed under {root}: {exc}")
                match = None
            if match and match.is_file():
                return str(match)
        _icon_debug(entry_name, app_id, pkg_names, f"no AppStream cached icon match for {filename!r}")
        return None

    def _debug_component_icon_info(
        self,
        component: Any,
        entry_name: str | None,
        app_id: str | None,
        pkg_names: list[str],
        icons: list[Any],
    ) -> None:
        launchables = []
        for item in self._as_list(getattr(component, "get_launchables", lambda: [])()):
            row: dict[str, Any] = {}
            for attr in ("get_kind", "get_value", "get_name"):
                fn = getattr(item, attr, None)
                if callable(fn):
                    try:
                        row[attr[4:]] = fn()
                    except Exception as exc:
                        row[attr[4:]] = f"<error: {exc}>"
            launchables.append(row or repr(item))

        icon_rows = []
        for icon in icons:
            row: dict[str, Any] = {}
            for attr in ("get_kind", "get_name", "get_filename", "get_url", "get_path"):
                fn = getattr(icon, attr, None)
                if callable(fn):
                    try:
                        row[attr[4:]] = fn()
                    except Exception as exc:
                        row[attr[4:]] = f"<error: {exc}>"
            icon_rows.append(row or repr(icon))

        _icon_debug(entry_name, app_id, pkg_names, f"appstream_id={app_id!r}")
        _icon_debug(entry_name, app_id, pkg_names, f"pkg_names={pkg_names!r}")
        _icon_debug(entry_name, app_id, pkg_names, f"launchables={launchables!r}")
        _icon_debug(entry_name, app_id, pkg_names, f"icons={icon_rows!r}")

    def _extract_media_ref(self, item: Any) -> str | None:
        for attr in (
            "get_filename",
            "get_path",
            "get_url",
            "get_name",
            "get_basename",
        ):
            fn = getattr(item, attr, None)
            if fn is None:
                continue
            try:
                value = fn()
            except Exception:
                value = None
            if value:
                return str(value)
        return None

    def _as_list(self, value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, (str, bytes)):
            return [value]
        try:
            return list(value)
        except TypeError:
            pass

        as_array = getattr(value, "as_array", None)
        if callable(as_array):
            try:
                return list(as_array())
            except Exception:
                pass

        get_size = getattr(value, "get_size", None)
        index_safe = getattr(value, "index_safe", None)
        if callable(get_size) and callable(index_safe):
            try:
                return [index_safe(i) for i in range(int(get_size())) if index_safe(i) is not None]
            except Exception:
                pass

        size = getattr(value, "size", None)
        get = getattr(value, "get", None)
        if callable(size) and callable(get):
            try:
                return [get(i) for i in range(int(size())) if get(i) is not None]
            except Exception:
                pass

        return []

    def _normalize_description(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        if "<" in text and ">" in text:
            parser = _HTMLToTextParser()
            parser.feed(text)
            parsed = parser.get_text()
            return parsed or self._safe_text(value)
        return self._safe_text(value)

    def _safe_text(self, value: Any) -> str | None:
        if value is None:
            return None
        text = unescape(str(value)).strip()
        return text or None
