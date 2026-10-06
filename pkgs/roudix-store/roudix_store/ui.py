from __future__ import annotations

import hashlib
import html
import os
from dataclasses import dataclass, field
from html.parser import HTMLParser
import subprocess
import sys
import threading
import traceback
import urllib.error
import urllib.request
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Adw, Gdk, GdkPixbuf, Gio, GLib, GObject, Gtk, Pango

from .appstream_catalog import AppStreamCatalog, AppStreamUnavailable
from .nix_backend import NixBackend, NixUnavailable
from . import localnix
from . import update_output
from . import launcher

import json
from pathlib import Path as _Path

_UPDATER_CONFIG_PATH = _Path.home() / ".config" / "roudix-store" / "updater.json"

def load_updater_settings() -> dict:
    defaults = {
        "enabled": True,
        "interval_unit": "hours",
        "interval_value": 6,
    }
    try:
        if _UPDATER_CONFIG_PATH.exists():
            data = json.loads(_UPDATER_CONFIG_PATH.read_text())
            if isinstance(data, dict):
                defaults.update({k: data[k] for k in defaults.keys() if k in data})
    except Exception:
        pass
    return defaults

def save_updater_settings(settings: dict) -> None:
    _UPDATER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "enabled": bool(settings.get("enabled", True)),
        "interval_unit": str(settings.get("interval_unit", "hours")),
        "interval_value": int(settings.get("interval_value", 6)),
    }
    _UPDATER_CONFIG_PATH.write_text(json.dumps(payload, indent=2))

from .i18n import L, action_word, status_word
from .updater_config import load_updater_settings, save_updater_settings, VALID_UNITS, save_view_mode, get_view_mode
from .models import AppEntry, should_hide_from_standard_catalog


class _NewsHTMLToMarkupParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self._parts: list[str] = []
        self._href_stack: list[str] = []
        self._list_depth = 0

    def _append(self, text: str) -> None:
        if text:
            self._parts.append(text)

    def _flush_block(self) -> None:
        text = ''.join(self._parts).strip()
        if text:
            self.blocks.append(text)
        self._parts = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs = dict(attrs)
        tag = tag.lower()
        if tag in {'b', 'strong'}:
            self._append('<b>')
        elif tag in {'i', 'em'}:
            self._append('<i>')
        elif tag == 'u':
            self._append('<u>')
        elif tag in {'s', 'strike', 'del'}:
            self._append('<s>')
        elif tag in {'tt', 'code'}:
            self._append('<tt>')
        elif tag == 'a':
            href = attrs.get('href', '')
            self._href_stack.append(href)
            if href:
                self._append(f'<a href="{GLib.markup_escape_text(href)}">')
        elif tag in {'p', 'div', 'section', 'article', 'header'}:
            self._flush_block()
        elif tag in {'br', 'hr'}:
            self._append('\n')
        elif tag in {'ul', 'ol'}:
            self._flush_block()
            self._list_depth += 1
        elif tag == 'li':
            if self._parts and not ''.join(self._parts).endswith('\n'):
                self._append('\n')
            indent = '  ' * max(self._list_depth - 1, 0)
            self._append(f'{indent}• ')

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {'b', 'strong'}:
            self._append('</b>')
        elif tag in {'i', 'em'}:
            self._append('</i>')
        elif tag == 'u':
            self._append('</u>')
        elif tag in {'s', 'strike', 'del'}:
            self._append('</s>')
        elif tag in {'tt', 'code'}:
            self._append('</tt>')
        elif tag == 'a':
            href = self._href_stack.pop() if self._href_stack else ''
            if href:
                self._append('</a>')
        elif tag == 'li':
            self._append('\n')
        elif tag in {'ul', 'ol'}:
            self._list_depth = max(0, self._list_depth - 1)
            self._flush_block()
        elif tag in {'p', 'div', 'section', 'article', 'header'}:
            self._flush_block()

    def handle_data(self, data: str) -> None:
        self._append(GLib.markup_escape_text(data))

    def handle_entityref(self, name: str) -> None:
        self._append(GLib.markup_escape_text(html.unescape(f'&{name};')))

    def handle_charref(self, name: str) -> None:
        self._append(GLib.markup_escape_text(html.unescape(f'&#{name};')))


def _markup_blocks_from_text(raw_text: str) -> list[str]:
    text = (raw_text or '').strip()
    if not text:
        return [L("Aucune actualité disponible.", "No news available.")]
    if '<' in text and '>' in text:
        parser = _NewsHTMLToMarkupParser()
        try:
            parser.feed(text)
            parser.close()
        except Exception:
            parser.blocks = []
        if parser.blocks:
            return parser.blocks
    sections = [GLib.markup_escape_text(part.strip()) for part in text.replace('\r\n', '\n').split('\n\n') if part.strip()]
    return sections or [L("Aucune actualité disponible.", "No news available.")]


@dataclass
class QueueItem:
    app: AppEntry
    action: str
    status: str = "queued"
    message: str = L("En attente", "Waiting")
    pkg_names: list[str] = field(default_factory=list)
    file_paths: list[str] = field(default_factory=list)
    label: str | None = None
    update_result: dict = field(default_factory=dict)
    scope: str = "home"

    def __post_init__(self) -> None:
        if not self.pkg_names:
            self.pkg_names = [self.app.primary_pkg] if self.app.primary_pkg else []

    @property
    def pkg_name(self) -> str:
        return self.pkg_names[0] if self.pkg_names else (self.app.primary_pkg or "")

    @property
    def display_name(self) -> str:
        if self.label:
            return self.label
        if len(self.file_paths) > 1:
            return L(f"{len(self.file_paths)} fichiers RPM", f"{len(self.file_paths)} RPM files")
        if len(self.pkg_names) > 1:
            return L(f"{len(self.pkg_names)} paquets", f"{len(self.pkg_names)} packages")
        return self.app.name

CATEGORY_GROUPS = {
    "system": {
        "installed": L("Installées", "Installed"),
        "queue": L("File d'attente", "Queue"),
    },
    "categories": {
        "office": L("Bureautique", "Productivity"),
        "graphics": L("Graphisme & photo", "Graphics & Photography"),
        "audiovideo": L("Audio & vidéo", "Audio & Video"),
        "education": L("Éducation", "Education"),
        "network": L("Réseau", "Networking"),
        "game": L("Jeux", "Games"),
        "development": L("Outils de développement", "Developer Tools"),
        "science": L("Sciences", "Science"),
        "system": L("Système", "System"),
        "utility": L("Utilitaires", "Utilities"),
    },
}

CATEGORY_ICONS = {
    "system": {
        "installed": "emblem-default-symbolic",
        "queue": "view-list-symbolic",
    },
    "categories": {
        "office": "x-office-document-symbolic",
        "graphics": "applications-graphics-symbolic",
        "audiovideo": "applications-multimedia-symbolic",
        "education": "accessories-dictionary-symbolic",
        "network": "network-workgroup-symbolic",
        "game": "applications-games-symbolic",
        "development": "applications-engineering-symbolic",
        "science": "applications-science-symbolic",
        "system": "applications-system-symbolic",
        "utility": "applications-utilities-symbolic",
    },
}

SUBCATEGORY_GROUPS = {
    "audiovideo": {
        "audiovideoediting": L("Montage audio & vidéo", "Audio & Video Editing"),
        "discburning": L("Gravure de disques", "Disc Burning"),
        "midi": L("Midi", "Midi"),
        "mixer": L("Mixage", "Mixer"),
        "player": L("Lecteurs", "Player"),
        "recorder": L("Enregistrement", "Recorder"),
        "sequencer": L("Séquenceurs", "Sequencer"),
        "tuner": L("Tuner", "Tuner"),
        "tv": L("TV", "TV"),
    },
    "development": {
        "building": L("Compilation", "Building"),
        "database": L("Bases de données", "Database"),
        "debugger": L("Débogage", "Debugger"),
        "guidesigner": L("Concepteurs d'interface", "GUI Designer"),
        "ide": L("IDE", "IDE"),
        "profiling": L("Profilage", "Profiling"),
        "revisioncontrol": L("Gestion de versions", "Revision Control"),
        "translation": L("Traduction", "Translation"),
        "webdevelopment": L("Développement web", "Web Development"),
    },
    "game": {
        "actiongame": L("Jeux d'action", "Action Games"),
        "adventuregame": L("Jeux d'aventure", "Adventure Games"),
        "arcadegame": L("Jeux d'arcade", "Arcade Games"),
        "blocksgame": L("Jeux de blocs", "Blocks Games"),
        "boardgame": L("Jeux de plateau", "Board Games"),
        "cardgame": L("Jeux de cartes", "Card Games"),
        "emulator": L("Émulateurs", "Emulators"),
        "kidsgame": L("Jeux pour enfants", "Kids' Games"),
        "logicgame": L("Jeux de logique", "Logic Games"),
        "roleplaying": L("Jeux de rôle", "Role Playing"),
        "shooter": L("Jeux de tir", "Shooter"),
        "simulation": L("Simulation", "Simulation"),
        "sportsgame": L("Jeux de sport", "Sports Games"),
        "strategygame": L("Jeux de stratégie", "Strategy Games"),
    },
    "graphics": {
        "2dgraphics": L("Graphisme 2D", "2D Graphics"),
        "3dgraphics": L("Graphisme 3D", "3D Graphics"),
        "ocr": L("OCR", "OCR"),
        "photography": L("Photographie", "Photography"),
        "publishing": L("Édition / PAO", "Publishing"),
        "rastergraphics": L("Images matricielles", "Raster Graphics"),
        "scanning": L("Numérisation", "Scanning"),
        "vectorgraphics": L("Graphisme vectoriel", "Vector Graphics"),
        "viewer": L("Visionneuses", "Viewer"),
    },
    "network": {
        "chat": L("Discussion", "Chat"),
        "email": L("Courriel", "Email"),
        "feed": L("Flux", "Feed"),
        "filetransfer": L("Transfert de fichiers", "File Transfer"),
        "hamradio": L("Radioamateur", "Ham Radio"),
        "instantmessaging": L("Messagerie instantanée", "Instant Messaging"),
        "ircclient": L("Clients IRC", "IRC Client"),
        "monitor": L("Surveillance", "Monitor"),
        "news": L("Actualités", "News"),
        "p2p": L("P2P", "P2P"),
        "remoteaccess": L("Accès à distance", "Remote Access"),
        "telephony": L("Téléphonie", "Telephony"),
        "videoconference": L("Visioconférence", "Video Conference"),
        "webbrowser": L("Navigateurs web", "Web Browser"),
        "webdevelopment": L("Développement web", "Web Development"),
    },
    "office": {
        "calendar": L("Agenda", "Calendar"),
        "chart": L("Diagrammes", "Chart"),
        "contactmanagement": L("Contacts", "Contact Management"),
        "database": L("Bases de données", "Database"),
        "dictionary": L("Dictionnaires", "Dictionary"),
        "email": L("Courriel", "Email"),
        "finance": L("Finance", "Finance"),
        "presentation": L("Présentation", "Presentation"),
        "projectmanagement": L("Gestion de projet", "Project Management"),
        "publishing": L("Édition / PAO", "Publishing"),
        "spreadsheet": L("Tableurs", "Spreadsheet"),
        "viewer": L("Visionneuses", "Viewer"),
        "wordprocessor": L("Traitement de texte", "Word Processor"),
    },
    "system": {
        "emulator": L("Émulateurs", "Emulators"),
        "filemanager": L("Gestionnaires de fichiers", "File Manager"),
        "filesystem": L("Systèmes de fichiers", "Filesystem"),
        "filetools": L("Outils de fichiers", "File Tools"),
        "monitor": L("Surveillance", "Monitor"),
        "security": L("Sécurité", "Security"),
        "terminalemulator": L("Émulateurs de terminal", "Terminal Emulator"),
    },
    "utility": {
        "accessibility": L("Accessibilité", "Accessibility"),
        "archiving": L("Archivage", "Archiving"),
        "calculator": L("Calculatrices", "Calculator"),
        "clock": L("Horloge", "Clock"),
        "compression": L("Compression", "Compression"),
        "filetools": L("Outils de fichiers", "File Tools"),
        "telephonytools": L("Outils de téléphonie", "Telephony Tools"),
        "texteditor": L("Éditeurs de texte", "Text Editor"),
        "texttools": L("Outils de texte", "Text Tools"),
    },
}

CSS = b"""
window {
  background: @window_bg_color;
}
windowhandle > box.top-bar {
  padding: 10px 12px;
  border-bottom: 1px solid alpha(currentColor, 0.12);
  background: mix(@window_bg_color, @headerbar_bg_color, 0.8);
}
.sidebar {
  margin: 0;
  padding: 12px 6px 8px 12px;
  background: transparent;
  border: 0;
}
.sidebar-section {
  margin: 0;
  font-weight: 400;
  font-size: 0.85rem;
  text-transform: uppercase;
  color: alpha(currentColor, 0.5);
}
.sidebar-section-box {
  margin: 0;
  padding: 10px 8px 2px 8px;
}
.sidebar-section-box image {
  color: @window_fg_color;
  -gtk-icon-style: symbolic;
}
.nav-button {
  border: 0;
  padding: 0;
  margin: 0;
  background: none;
  box-shadow: none;
  min-height: 0;
}
.nav-button > box {
  border-radius: 4px;
  padding: 12px 8px;
  transition: margin-left 0.2s cubic-bezier(0.040, 0.455, 0.215, 0.995), padding 0.2s cubic-bezier(0.040, 0.455, 0.215, 0.995);
}
.nav-button .nav-label {
  font-weight: 400;
}
.nav-button .nav-arrow {
  color: #3584e4;
  font-weight: 700;
}
.nav-button.active > box {
  background: transparent;
  margin-left: 0;
  padding: 12px 8px;
}
.nav-button.active .nav-label {
  font-weight: bold;
}
.content-box {
  margin: 12px 12px 12px 0;
}
.queue-bottom-bar {
  padding: 8px 12px;
  border-top: 1px solid alpha(currentColor, 0.12);
  background: mix(@window_bg_color, @headerbar_bg_color, 0.85);
}
.queue-bottom-status {
  min-width: 180px;
}
.content-header {
  margin: 8px 4px 10px 4px;
  min-width: 0;
}

.updates-action-bar {
  margin: 8px 0 4px 0;
}
.update-check {
  margin-right: 6px;
}
.subcat-strip {
  padding: 4px 0 10px 0;
  min-width: 0;
}
.subcat-strip > box {
  min-width: 0;
}
.subcat-strip-frame {
  margin: 2px;
  padding: 0;
  background: @sidebar_backdrop_color;
  border-radius: 4px;
  min-width: 0;
}
.subcat-page {
  padding: 2px 6px;
}
.pan-button {
  border: 0px;
  padding: 6px;
  margin: 0;
  background: none;
  box-shadow: none;
  color: alpha(currentColor, 0.45);
}
.pan-button.available {
  color: #3584e4;
}
.subcategory-chip {
  margin: 4px 0;
  padding: 8px 14px;
  border-radius: 4px;
  background: transparent;
}
.subcategory-chip.active {
  background-color: transparent;
  padding: 8px 0;
  border-radius: 0;
}
.subcategory-label {
  font-weight: 400;
}
.subcategory-chip.active .subcategory-label {
  font-weight: 700;
}
.app-list {
  background: transparent;
}
.app-list row,
.app-list row:selected,
.app-list row:hover {
  background: transparent;
  box-shadow: none;
}
.app-list-row {
  margin: 4px 0;
}
.app-card {
  padding: 10px 14px;
  border-radius: 14px;
  background: alpha(@card_bg_color, 0.72);
  border: 1px solid alpha(currentColor, 0.08);
  box-shadow: none;
}
.app-title {
  font-size: 1.02em;
  font-weight: 800;
}
.app-summary {
  margin-top: 0;
  color: alpha(currentColor, 0.78);
}
.app-meta {
  font-size: 0.92em;
  color: alpha(currentColor, 0.68);
  margin-top: 4px;
}
.detail-hero {
  padding: 24px 28px;
  border-radius: 18px;
  background: alpha(@card_bg_color, 0.75);
  border: 1px solid alpha(currentColor, 0.08);
}
.repo-card {
  padding: 14px 16px;
  border-radius: 14px;
  background: alpha(@card_bg_color, 0.7);
  border: 1px solid alpha(currentColor, 0.08);
  margin: 6px 0;
}
.news-card {
  padding: 22px 24px;
  border-radius: 18px;
  background: alpha(@card_bg_color, 0.72);
  border: 1px solid alpha(currentColor, 0.08);
}
.news-heading {
  font-size: 1.18em;
  font-weight: 800;
}
.news-body {
  font-size: 1.02em;
  line-height: 1.45;
}
.news-panel {
  background: alpha(@window_bg_color, 0.5);
  border-left: 1px solid alpha(currentColor, 0.1);
}
"""




CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "roudix-store" / "media"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DEBUG_ICONS = os.environ.get("APPSTORE_DEBUG_ICONS") == "1"
DEBUG_ICON_FILTER = os.environ.get("APPSTORE_DEBUG_ICON_FILTER", "").strip().casefold()


def _icon_debug_enabled(app: AppEntry | None) -> bool:
    if not DEBUG_ICONS:
        return False
    if app is None:
        return not DEBUG_ICON_FILTER
    haystack = " ".join([
        app.name or "",
        app.appstream_id or "",
        " ".join(app.pkg_names or []),
        " ".join(app.launchables or []),
    ]).casefold()
    return not DEBUG_ICON_FILTER or DEBUG_ICON_FILTER in haystack


def _icon_debug(app: AppEntry | None, message: str) -> None:
    if _icon_debug_enabled(app):
        target = getattr(app, "name", None) or getattr(app, "appstream_id", None) or "<unknown>"
        print(f"[ICON DEBUG] {target}: {message}", file=sys.stderr)


def _cached_media_path(url: str) -> Path:
    suffix = Path(url.split("?", 1)[0]).suffix or ".bin"
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{digest}{suffix}"


def _ensure_local_media(ref: str | None) -> str | None:
    if not ref:
        return None
    if ref.startswith(("http://", "https://")):
        target = _cached_media_path(ref)
        if target.exists():
            return str(target)
        try:
            with urllib.request.urlopen(ref, timeout=20) as response:
                data = response.read()
            target.write_bytes(data)
            return str(target)
        except (OSError, urllib.error.URLError, TimeoutError):
            return None
    path = Path(ref)
    if path.is_file():
        return str(path)
    return None


def _crop_transparent_borders(pixbuf: GdkPixbuf.Pixbuf) -> GdkPixbuf.Pixbuf:
    if not pixbuf.get_has_alpha():
        return pixbuf

    width = pixbuf.get_width()
    height = pixbuf.get_height()
    rowstride = pixbuf.get_rowstride()
    n_channels = pixbuf.get_n_channels()
    pixels = pixbuf.get_pixels()

    min_x = width
    min_y = height
    max_x = -1
    max_y = -1

    for y in range(height):
        base = y * rowstride
        for x in range(width):
            alpha = pixels[base + x * n_channels + (n_channels - 1)]
            if alpha > 0:
                if x < min_x:
                    min_x = x
                if y < min_y:
                    min_y = y
                if x > max_x:
                    max_x = x
                if y > max_y:
                    max_y = y

    if max_x < min_x or max_y < min_y:
        return pixbuf

    cropped_w = max_x - min_x + 1
    cropped_h = max_y - min_y + 1
    if cropped_w <= 0 or cropped_h <= 0 or (cropped_w == width and cropped_h == height):
        return pixbuf

    try:
        return pixbuf.new_subpixbuf(min_x, min_y, cropped_w, cropped_h)
    except Exception:
        return pixbuf




def _is_font_like_app(app: AppEntry) -> bool:
    haystacks = [
        app.name or "",
        app.summary or "",
        app.description or "",
        app.primary_pkg or "",
        " ".join(app.pkg_names or []),
        " ".join(app.categories or []),
    ]
    text = " ".join(haystacks).lower()
    if any(token in text for token in [" font", "fonts", "typeface", "typography"]):
        return True
    pkg = (app.primary_pkg or "").lower()
    return pkg.endswith("-fonts") or pkg.endswith("fonts")
def _image_from_ref(ref: str | None, size: int, *, crop_transparency: bool = True, fill_ratio: float = 1.0) -> Gtk.Widget | None:
    local_path = _ensure_local_media(ref)
    if not local_path:
        return None

    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(local_path)
        if crop_transparency:
            pixbuf = _crop_transparent_borders(pixbuf)
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        if width <= 0 or height <= 0:
            return None
        target_size = max(1, int(round(size * fill_ratio)))
        scale = min(target_size / width, target_size / height)
        scaled_w = max(1, int(round(width * scale)))
        scaled_h = max(1, int(round(height * scale)))
        scaled = pixbuf.scale_simple(scaled_w, scaled_h, GdkPixbuf.InterpType.BILINEAR)
        texture = Gdk.Texture.new_for_pixbuf(scaled)
        picture = Gtk.Picture.new_for_paintable(texture)
        picture.set_can_shrink(True)
        picture.set_keep_aspect_ratio(True)
        picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        picture.set_halign(Gtk.Align.CENTER)
        picture.set_valign(Gtk.Align.CENTER)
        picture.set_size_request(size, size)
        return picture
    except Exception:
        picture = Gtk.Picture.new_for_filename(local_path)
        picture.set_can_shrink(True)
        picture.set_keep_aspect_ratio(True)
        picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        picture.set_halign(Gtk.Align.CENTER)
        picture.set_valign(Gtk.Align.CENTER)
        picture.set_size_request(size, size)
        return picture






def _image_from_icon_name(icon_name: str | None, size: int, *, crop_transparency: bool = True, fill_ratio: float = 1.0) -> Gtk.Widget | None:
    if not icon_name:
        return None

    try:
        display = Gdk.Display.get_default()
        if display is not None:
            theme = Gtk.IconTheme.get_for_display(display)
            paintable = None
            try:
                paintable = theme.lookup_icon(
                    icon_name,
                    None,
                    size,
                    1,
                    Gtk.TextDirection.NONE,
                    Gtk.IconLookupFlags.FORCE_SIZE,
                )
            except TypeError:
                try:
                    paintable = theme.lookup_icon(
                        icon_name,
                        [],
                        size,
                        1,
                        Gtk.TextDirection.NONE,
                        Gtk.IconLookupFlags.FORCE_SIZE,
                    )
                except Exception:
                    paintable = None
            except Exception:
                paintable = None

            if paintable is not None:
                try:
                    file = paintable.get_file()
                    if file is not None:
                        local_path = file.get_path()
                        if local_path:
                            image = _image_from_ref(local_path, size, crop_transparency=crop_transparency, fill_ratio=fill_ratio)
                            if image is not None:
                                return image
                except Exception:
                    pass
    except Exception:
        pass

    image = Gtk.Image.new_from_icon_name(icon_name)
    image.set_pixel_size(size)
    image.set_size_request(size, size)
    image.set_halign(Gtk.Align.CENTER)
    image.set_valign(Gtk.Align.CENTER)
    return image

def _picture_from_ref(ref: str | None, width: int, height: int) -> Gtk.Widget | None:
    local_path = _ensure_local_media(ref)
    if not local_path:
        return None

    picture = Gtk.Picture.new_for_filename(local_path)
    picture.set_can_shrink(True)
    picture.set_keep_aspect_ratio(True)
    picture.set_content_fit(Gtk.ContentFit.CONTAIN)
    picture.set_halign(Gtk.Align.CENTER)
    picture.set_valign(Gtk.Align.CENTER)
    picture.set_size_request(width, height)
    return picture

def _icon_names_from_launchables(app: AppEntry) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for launchable in app.launchables:
        if not launchable:
            continue
        desktop_id = Path(str(launchable)).name
        if not desktop_id.endswith('.desktop'):
            _icon_debug(app, f"skip non-desktop launchable {launchable!r}")
            continue
        try:
            info = Gio.DesktopAppInfo.new(desktop_id)  # PyGObject raises TypeError when the app isn't installed
        except TypeError:
            info = None
        if info is None:
            _icon_debug(app, f"DesktopAppInfo not found for {desktop_id!r}")
            continue
        _icon_debug(app, f"DesktopAppInfo found for {desktop_id!r}")
        icon = info.get_icon()
        icon_key = None
        try:
            icon_key = info.get_string("Icon")
        except Exception:
            icon_key = None
        _icon_debug(app, f"desktop Icon= {icon_key!r}; gicon={icon!r}")
        if icon is None:
            continue
        icon_str = icon.to_string()
        if icon_str and icon_str not in seen:
            names.append(icon_str)
            seen.add(icon_str)
    return names


def _resolve_themed_icon_name(app: AppEntry) -> str | None:
    display = Gdk.Display.get_default()
    if display is None:
        candidates: list[str] = []
        _icon_debug(app, "no display available for icon theme lookup")
    else:
        theme = Gtk.IconTheme.get_for_display(display)
        candidates = []
        if app.icon_name:
            candidates.extend([app.icon_name, Path(app.icon_name).stem])
        candidates.extend(_icon_names_from_launchables(app))
        if app.appstream_id:
            candidates.extend([app.appstream_id, Path(app.appstream_id).stem])
        if app.primary_pkg:
            candidates.extend([app.primary_pkg, Path(app.primary_pkg).stem])
        seen: set[str] = set()
        normalized: list[str] = []
        for candidate in candidates:
            if not candidate:
                continue
            for variant in (candidate, Path(candidate).stem):
                variant = str(variant).strip()
                if not variant or variant in seen:
                    continue
                seen.add(variant)
                normalized.append(variant)
        _icon_debug(app, f"themed icon candidates={normalized!r}")
        for candidate in normalized:
            try:
                if theme.has_icon(candidate):
                    _icon_debug(app, f"theme matched icon name {candidate!r}")
                    return candidate
            except Exception as exc:
                _icon_debug(app, f"theme lookup failed for {candidate!r}: {exc}")
                continue
        candidates = normalized

    if candidates:
        _icon_debug(app, f"no theme match, falling back to first candidate {candidates[0]!r}")
    else:
        _icon_debug(app, "no themed icon candidates available")
    return candidates[0] if candidates else None


class IconWidget(Gtk.Box):
    def __init__(self, app: AppEntry, size: int = 64):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.set_size_request(size, size)
        self.set_halign(Gtk.Align.START)
        self.set_valign(Gtk.Align.CENTER)
        self.set_hexpand(False)
        self.set_vexpand(False)

        holder = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        holder.set_size_request(size, size)
        holder.set_halign(Gtk.Align.CENTER)
        holder.set_valign(Gtk.Align.CENTER)
        holder.set_hexpand(False)
        holder.set_vexpand(False)
        self.append(holder)

        _icon_debug(app, f"icon_path={app.icon_path!r} icon_url={app.icon_url!r} icon_name={app.icon_name!r}")
        font_like = _is_font_like_app(app)
        crop_transparency = not font_like
        fill_ratio = 0.72 if font_like else 1.0

        image_widget = _image_from_ref(app.icon_path or app.icon_url, size, crop_transparency=crop_transparency, fill_ratio=fill_ratio)
        if image_widget is not None:
            _icon_debug(app, f"using picture from {app.icon_path or app.icon_url!r}")
            holder.append(image_widget)
            return

        themed_name = _resolve_themed_icon_name(app)
        if themed_name:
            _icon_debug(app, f"using themed icon {themed_name!r}")
        else:
            _icon_debug(app, "falling back to generic application-x-executable")

        image = _image_from_icon_name(themed_name or "application-x-executable", size, crop_transparency=crop_transparency, fill_ratio=fill_ratio)
        holder.append(image)


class NavSidebarButton(Gtk.Button):
    def __init__(self, title: str, callback, icon_name: str | None = None, indent: bool = False):
        super().__init__()
        self.set_halign(Gtk.Align.START)
        self.set_has_frame(False)
        self.add_css_class("flat")
        self.add_css_class("nav-button")
        if indent:
            self.set_margin_start(10)

        inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        inner.set_halign(Gtk.Align.START)
        self.set_child(inner)

        if icon_name:
            icon_widget = Gtk.Image.new_from_gicon(Gio.ThemedIcon.new(icon_name))
            icon_widget.set_pixel_size(16)
            icon_widget.add_css_class("nav-icon")
            inner.append(icon_widget)

        self.label_widget = Gtk.Label(label=title, xalign=0)
        self.label_widget.add_css_class("nav-label")
        inner.append(self.label_widget)

        self.arrow_widget = Gtk.Label(label="❯", xalign=0)
        self.arrow_widget.add_css_class("nav-arrow")
        self.arrow_widget.set_visible(False)
        inner.append(self.arrow_widget)

        self.connect("clicked", lambda *_: callback())

    def set_active(self, active: bool) -> None:
        if active:
            self.add_css_class("active")
        else:
            self.remove_css_class("active")
        self.arrow_widget.set_visible(active)


class SubcategoryButton(Gtk.Box):
    def __init__(self, title: str, callback):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.set_halign(Gtk.Align.START)
        self.set_valign(Gtk.Align.CENTER)
        self.set_hexpand(False)
        self.set_vexpand(False)

        self.chip = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.chip.set_halign(Gtk.Align.START)
        self.chip.set_valign(Gtk.Align.CENTER)
        self.chip.add_css_class("subcategory-chip")
        self.append(self.chip)

        self.label = Gtk.Label(label=title, xalign=0)
        self.label.set_halign(Gtk.Align.START)
        self.label.set_valign(Gtk.Align.CENTER)
        self.label.set_wrap(False)
        self.label.set_single_line_mode(True)
        self.label.add_css_class("subcategory-label")
        self.chip.append(self.label)

        gesture = Gtk.GestureClick()
        gesture.connect("released", lambda *_: callback())
        self.add_controller(gesture)

    def set_active(self, active: bool) -> None:
        if active:
            self.chip.add_css_class("active")
        else:
            self.chip.remove_css_class("active")


class AppCardRow(Gtk.ListBoxRow):
    __gtype_name__ = "DnfAppCenterAppCardRow"

    def __init__(self, app: AppEntry, action_cb, open_cb, queue_state_cb, page_mode: str = "default", update_selected: bool = False, update_toggle_cb=None):
        super().__init__()
        self.app = app
        self._action_cb = action_cb
        self._open_cb = open_cb
        self._queue_state_cb = queue_state_cb
        self._page_mode = page_mode
        self._update_toggle_cb = update_toggle_cb
        self.add_css_class("app-list-row")

        # Container for content + separator
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(container)

        outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        outer.set_valign(Gtk.Align.CENTER)
        outer.add_css_class("app-card-compact")
        outer.set_hexpand(True)
        outer.set_margin_start(10)
        container.append(outer)

        if self._page_mode == "updates":
            self.update_check = Gtk.CheckButton()
            self.update_check.add_css_class("update-check")
            self.update_check.set_active(update_selected)
            if self._update_toggle_cb is not None:
                self.update_check.connect("toggled", lambda btn: self._update_toggle_cb(self.app, btn.get_active()))
            outer.append(self.update_check)
        else:
            self.update_check = None

        self.title_label = Gtk.Label(xalign=0)
        self.title_label.add_css_class("app-title")
        self.title_label.set_wrap(False)
        self.title_label.set_single_line_mode(True)
        self.title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.title_label.set_text(app.name)
        self.title_label.set_hexpand(True)
        outer.append(self.title_label)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        button_box.set_valign(Gtk.Align.CENTER)
        button_box.set_halign(Gtk.Align.END)
        outer.append(button_box)

        self.action_button = Gtk.Button()
        self.action_button.set_size_request(24, 24)
        self.action_button.add_css_class("flat")
        self.action_button.connect("clicked", lambda *_: self._action_cb(self.app))
        button_box.append(self.action_button)

        # Add separator line at bottom
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.add_css_class("list-row-separator")
        container.append(separator)

        self.refresh()

    def refresh(self) -> None:
        queue_state = self._queue_state_cb(self.app)
        if queue_state is not None:
            self.action_button.set_icon_name("emblem-synchronizing-symbolic")
            self.action_button.set_sensitive(False)
            self.action_button.set_tooltip_text(queue_state)
        else:
            self.action_button.set_sensitive(True)
            if self._page_mode == "updates":
                self.action_button.set_icon_name("software-update-available-symbolic")
                self.action_button.set_tooltip_text(L("Mettre à jour", "Update"))
            else:
                if self.app.installed:
                    self.action_button.set_icon_name("list-remove-symbolic")
                    self.action_button.set_tooltip_text(L("Supprimer", "Remove"))
                else:
                    self.action_button.set_icon_name("list-add-symbolic")
                    self.action_button.set_tooltip_text(L("Installer", "Install"))
        self.action_button.remove_css_class("destructive-action")
        self.action_button.remove_css_class("suggested-action")
        if self._page_mode == "updates":
            self.action_button.add_css_class("suggested-action")
        else:
            self.action_button.add_css_class("destructive-action" if self.app.installed else "suggested-action")




class AppCardTile(Gtk.Box):
    __gtype_name__ = "DnfAppCenterAppCardTile"

    def __init__(self, app: AppEntry, action_cb, open_cb, queue_state_cb, page_mode: str = "default", update_selected: bool = False, update_toggle_cb=None):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.app = app
        self._action_cb = action_cb
        self._open_cb = open_cb
        self._queue_state_cb = queue_state_cb
        self._page_mode = page_mode
        self._update_toggle_cb = update_toggle_cb
        self.add_css_class("app-card")
        self.set_margin_top(4)
        self.set_margin_bottom(4)
        self.set_margin_start(4)
        self.set_margin_end(4)
        self.set_hexpand(True)
        self.set_size_request(300, 92)
        self.set_valign(Gtk.Align.FILL)

        if self._page_mode == "updates":
            self.update_check = Gtk.CheckButton()
            self.update_check.add_css_class("update-check")
            self.update_check.set_active(update_selected)
            if self._update_toggle_cb is not None:
                self.update_check.connect("toggled", lambda btn: self._update_toggle_cb(self.app, btn.get_active()))
            self.append(self.update_check)
        else:
            self.update_check = None

        self.append(IconWidget(app, 64))

        text_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        text_col.set_hexpand(True)
        text_col.set_valign(Gtk.Align.CENTER)
        self.append(text_col)

        self.title_label = Gtk.Label(xalign=0)
        self.title_label.add_css_class("app-title")
        self.title_label.set_wrap(False)
        self.title_label.set_single_line_mode(True)
        self.title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.title_label.set_text(app.name)
        text_col.append(self.title_label)

        self.summary_label = Gtk.Label(xalign=0)
        self.summary_label.add_css_class("app-summary")
        self.summary_label.set_wrap(True)
        self.summary_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.summary_label.set_lines(2)
        self.summary_label.set_max_width_chars(22)
        self.summary_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.summary_label.set_text(app.summary)
        text_col.append(self.summary_label)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        button_box.set_valign(Gtk.Align.CENTER)
        button_box.set_halign(Gtk.Align.END)
        self.append(button_box)

        self.action_button = Gtk.Button()
        self.action_button.set_size_request(24, 24)
        self.action_button.add_css_class("flat")
        self.action_button.connect("clicked", lambda *_: self._action_cb(self.app))
        button_box.append(self.action_button)

        gesture = Gtk.GestureClick()
        gesture.connect("released", lambda *_: self._open_cb(self.app))
        self.add_controller(gesture)
        self.refresh()

    def refresh(self) -> None:
        queue_state = self._queue_state_cb(self.app)
        if queue_state is not None:
            self.action_button.set_icon_name("emblem-synchronizing-symbolic")
            self.action_button.set_sensitive(False)
            self.action_button.set_tooltip_text(queue_state)
        else:
            self.action_button.set_sensitive(True)
            if self._page_mode == "updates":
                self.action_button.set_icon_name("software-update-available-symbolic")
                self.action_button.set_tooltip_text(L("Mettre à jour", "Update"))
            else:
                if self.app.installed:
                    self.action_button.set_icon_name("list-remove-symbolic")
                    self.action_button.set_tooltip_text(L("Supprimer", "Remove"))
                else:
                    self.action_button.set_icon_name("list-add-symbolic")
                    self.action_button.set_tooltip_text(L("Installer", "Install"))
        self.action_button.remove_css_class("destructive-action")
        self.action_button.remove_css_class("suggested-action")
        if self._page_mode == "updates":
            self.action_button.add_css_class("suggested-action")
        else:
            self.action_button.add_css_class("destructive-action" if self.app.installed else "suggested-action")


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, launch_updates: bool = False):
        super().__init__(application=app)
        self.set_title("Roudix Store")
        self.set_default_size(1280, 800)

        self.catalog: AppStreamCatalog | None = None
        self.backend: NixBackend | None = None
        self.apps: list[AppEntry] = []
        self.current_items: list[AppEntry] = []
        self.current_page = "audiovideo"
        self.source = "nix"  # "nix" or "flatpak": the active catalog (sidebar switch)
        self.current_group = "categories"
        self.news_panel_visible = True
        self.news_text = L("Chargement des actualités…", "Loading news…")
        self.current_subcategory: str | None = None
        self.current_search_text = ""
        self.current_category_filter_text = ""
        self.current_repo_filter = "__all__"
        self.updater_settings = load_updater_settings()
        self.current_app: AppEntry | None = None
        self.update_selection: set[str] = set()
        self.queue_items: list[QueueItem] = []
        self.queue_logs: list[str] = []
        self.queue_log_full: list[str] = []
        self.queue_worker_running = False
        self.current_queue_item: QueueItem | None = None
        self._appstream_pkg_names: set[str] = set()
        self.nav_buttons: dict[str, Gtk.Button] = {}
        self.subcategory_buttons: dict[str, Gtk.Widget] = {}
        self.subcategory_button_pages: dict[str, int] = {}
        self.subcategory_pages: list[list[tuple[str, str]]] = []
        self.current_subcategory_page = 0
        self._page_items_cache: dict[tuple, list[AppEntry]] = {}
        self._data_revision = 0
        self.view_mode = "grid"  # Can be "grid" or "list"
        self._updating_view_buttons = False  # Flag to prevent toggle recursion
        self._listbox_gen = 0
        self._is_loading = False

        provider = Gtk.CssProvider()
        provider.load_from_bytes(GLib.Bytes.new(CSS))
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.toast_overlay.set_child(root)
        self.connect("close-request", self._on_close_request)

        root.append(self._build_top_bar())
        self.update_banner = Adw.Banner(title="")
        self.update_banner.set_revealed(False)
        root.append(self.update_banner)

        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        body.set_vexpand(True)
        root.append(body)

        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_scroll.set_min_content_width(308)
        sidebar_scroll.set_size_request(308, -1)
        sidebar_scroll.set_vexpand(True)
        body.append(sidebar_scroll)

        self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.sidebar_box.add_css_class("sidebar")
        sidebar_scroll.set_child(self.sidebar_box)
        self._build_sidebar()

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content_box.add_css_class("content-box")
        self.content_box.set_hexpand(True)
        self.content_box.set_vexpand(True)
        body.append(self.content_box)

        self.content_header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content_header_box.add_css_class("content-header")
        self.content_box.append(self.content_header_box)

        self.title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.title_row.set_hexpand(True)
        self.title_row.set_halign(Gtk.Align.FILL)
        self.content_header_box.append(self.title_row)

        self.title_label = Gtk.Label(xalign=0)
        self.title_label.add_css_class("title-1")
        self.title_label.set_hexpand(False)
        self.title_label.set_halign(Gtk.Align.START)
        self.title_row.append(self.title_label)

        self.title_row_spacer = Gtk.Box()
        self.title_row_spacer.set_hexpand(True)
        self.title_row.append(self.title_row_spacer)

        self.category_filter_entry = Gtk.SearchEntry()
        self.category_filter_entry.set_placeholder_text(L("Filtrer…", "Search filter…"))
        self.category_filter_entry.set_hexpand(False)
        self.category_filter_entry.set_halign(Gtk.Align.END)
        self.category_filter_entry.set_valign(Gtk.Align.CENTER)
        self.category_filter_entry.set_size_request(280, -1)
        self.category_filter_entry.set_visible(False)
        self.category_filter_entry.connect("activate", self._on_category_filter_changed)
        self.title_row.append(self.category_filter_entry)

        # View mode toggle buttons
        self.view_toggle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.view_toggle_box.add_css_class("linked")
        self.view_toggle_box.set_hexpand(False)
        self.view_toggle_box.set_halign(Gtk.Align.END)
        self.view_toggle_box.set_valign(Gtk.Align.CENTER)
        self.view_toggle_box.set_visible(False)
        self.title_row.append(self.view_toggle_box)

        self.grid_view_button = Gtk.ToggleButton()
        self.grid_view_button.set_icon_name("view-grid-symbolic")
        self.grid_view_button.set_tooltip_text(L("Vue en grille", "Grid View"))
        self.grid_view_button.set_active(True)
        self.grid_view_button.connect("toggled", self._on_grid_view_toggled)
        self.view_toggle_box.append(self.grid_view_button)

        self.list_view_button = Gtk.ToggleButton()
        self.list_view_button.set_icon_name("view-list-symbolic")
        self.list_view_button.set_tooltip_text(L("Vue en liste", "List View"))
        self.list_view_button.connect("toggled", self._on_list_view_toggled)
        self.view_toggle_box.append(self.list_view_button)

        self.status_label = Gtk.Label(xalign=0)
        self.status_label.add_css_class("dim-label")
        self.content_header_box.append(self.status_label)

        self.updates_action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.updates_action_bar.add_css_class("updates-action-bar")
        self.updates_action_bar.set_visible(False)
        self.content_header_box.append(self.updates_action_bar)

        self.updates_selected_label = Gtk.Label(xalign=0)
        self.updates_selected_label.add_css_class("dim-label")
        self.updates_action_bar.append(self.updates_selected_label)

        self.updates_clear_button = Gtk.Button(label=L("Effacer la sélection", "Clear Selection"))
        self.updates_clear_button.connect("clicked", lambda *_: self._clear_update_selection())
        self.updates_action_bar.append(self.updates_clear_button)

        self.update_selected_button = Gtk.Button(label=L("Mettre à jour la sélection", "Update Selected"))
        self.update_selected_button.add_css_class("suggested-action")
        self.update_selected_button.connect("clicked", lambda *_: self._queue_selected_updates())
        self.updates_action_bar.append(self.update_selected_button)

        self.update_all_button = Gtk.Button()
        update_all_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        update_all_icon = Gtk.Image.new_from_icon_name("software-update-available-symbolic")
        update_all_label = Gtk.Label(label=L("Tout sélectionner et mettre à jour", "Select All and Update"))
        update_all_box.append(update_all_icon)
        update_all_box.append(update_all_label)
        self.update_all_button.set_child(update_all_box)
        self.update_all_button.connect("clicked", lambda *_: self._queue_system_update())
        self.updates_action_bar.append(self.update_all_button)

        self.update_flatpaks_check = Gtk.CheckButton(label=L("Mettre aussi à jour les flatpaks", "Also update flatpaks"))
        self.update_flatpaks_check.set_valign(Gtk.Align.CENTER)
        self.update_flatpaks_check.set_tooltip_text(L("Ajoute --all à nobara-sync pour cette mise à jour système.", "Append --all to nobara-sync for this system update."))
        self.update_flatpaks_check.set_active(bool(self.updater_settings.get("update_flatpaks", False)))
        self.update_flatpaks_check.connect("toggled", self._on_update_flatpaks_toggled)
        self.updates_action_bar.append(self.update_flatpaks_check)

        # News panel toggle button
        self.news_toggle_button = Gtk.ToggleButton()
        self.news_toggle_button.set_icon_name("starred-symbolic")
        self.news_toggle_button.set_tooltip_text(L("Afficher/masquer le panneau d'actualités", "Toggle News Panel"))
        self.news_toggle_button.set_active(True)
        self.news_toggle_button.connect("toggled", self._on_news_toggle)
        self.title_row.append(self.news_toggle_button)

        self.subcategory_strip = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.subcategory_strip.add_css_class("subcat-strip")
        self.subcategory_strip.set_hexpand(True)
        self.subcategory_strip.set_halign(Gtk.Align.FILL)
        self.content_header_box.append(self.subcategory_strip)

        self.subcat_left_button = Gtk.Button.new_from_icon_name("pan-start-symbolic")
        self.subcat_left_button.add_css_class("pan-button")
        self.subcat_left_button.connect("clicked", self._on_subcat_pan_start)
        self.subcategory_strip.append(self.subcat_left_button)

        self.subcategory_frame = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.subcategory_frame.add_css_class("subcat-strip-frame")
        self.subcategory_frame.set_hexpand(True)
        self.subcategory_frame.set_halign(Gtk.Align.FILL)
        self.subcategory_frame.set_valign(Gtk.Align.CENTER)
        self.subcategory_strip.append(self.subcategory_frame)

        self.subcategory_stack = Gtk.Stack()
        self.subcategory_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.subcategory_stack.set_transition_duration(180)
        self.subcategory_stack.set_hexpand(True)
        self.subcategory_stack.set_halign(Gtk.Align.FILL)
        self.subcategory_stack.set_valign(Gtk.Align.CENTER)
        self.subcategory_frame.append(self.subcategory_stack)

        self.subcat_right_button = Gtk.Button.new_from_icon_name("pan-end-symbolic")
        self.subcat_right_button.add_css_class("pan-button")
        self.subcat_right_button.connect("clicked", self._on_subcat_pan_end)
        self.subcategory_strip.append(self.subcat_right_button)

        self.stack = Gtk.Stack()
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        self.content_box.append(self.stack)

        self.bottom_queue_revealer = Gtk.Revealer()
        self.bottom_queue_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        self.bottom_queue_revealer.set_reveal_child(False)
        root.append(self.bottom_queue_revealer)

        bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bottom_bar.add_css_class("queue-bottom-bar")
        self.bottom_queue_revealer.set_child(bottom_bar)

        self.bottom_queue_progress = Gtk.ProgressBar()
        self.bottom_queue_progress.set_hexpand(True)
        bottom_bar.append(self.bottom_queue_progress)

        self.bottom_queue_status = Gtk.Label(xalign=0)
        self.bottom_queue_status.add_css_class("dim-label")
        self.bottom_queue_status.add_css_class("queue-bottom-status")
        bottom_bar.append(self.bottom_queue_status)

        queue_button = Gtk.Button(label=L("Voir la file d'attente", "View Queue"))
        queue_button.connect("clicked", lambda *_: self._switch_page("system", "queue"))
        bottom_bar.append(queue_button)

        self.bottom_clear_button = Gtk.Button(label=L("Vider", "Clear"))
        self.bottom_clear_button.connect("clicked", lambda *_: self._clear_pending_queue())
        bottom_bar.append(self.bottom_clear_button)

        self.bottom_apply_button = Gtk.Button(label=L("Appliquer", "Apply"))
        self.bottom_apply_button.add_css_class("suggested-action")
        self.bottom_apply_button.connect("clicked", lambda *_: self._apply_queue())
        bottom_bar.append(self.bottom_apply_button)

        self._build_list_page()
        self._build_queue_page()
        self._build_repo_page()
        self._build_detail_page()

        self._refresh_news_page()
        self._show_loading_page(L("Chargement des métadonnées AppStream et de l'index nixpkgs…", "Loading AppStream metadata and the nixpkgs index…"))
        self._load_async(force=True)

    def _setup_rpm_drop_target(self) -> None:
        try:
            drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        except Exception:
            return
        drop_target.connect("drop", self._on_rpm_drop)
        self.add_controller(drop_target)

    def _extract_dropped_rpm_paths(self, value) -> list[str]:
        paths: list[str] = []
        files_obj = None
        try:
            files_obj = value.get_files()
        except Exception:
            files_obj = value

        try:
            n_items = files_obj.get_n_items()
            for i in range(n_items):
                item = files_obj.get_item(i)
                try:
                    path = item.get_path()
                except Exception:
                    path = None
                if path and path.endswith('.rpm'):
                    paths.append(path)
        except Exception:
            try:
                for item in files_obj:  # type: ignore
                    path = item.get_path()
                    if path and path.endswith('.rpm'):
                        paths.append(path)
            except Exception:
                pass
        return paths

    def _on_rpm_drop(self, _target, value, _x, _y) -> bool:
        rpm_paths = self._extract_dropped_rpm_paths(value)
        if not rpm_paths:
            self._show_toast(L("Dépose un ou plusieurs fichiers .rpm pour les installer.", "Drop one or more .rpm files to install them."))
            return False
        self._queue_rpm_file_install(rpm_paths)
        return True

    def queue_rpm_file_install(self, rpm_paths: list[str]) -> None:
        self._queue_rpm_file_install(rpm_paths)

    def _queue_rpm_file_install(self, rpm_paths: list[str]) -> None:
        rpm_paths = [str(Path(path)) for path in rpm_paths if str(path).lower().endswith('.rpm')]
        if not rpm_paths:
            self._show_toast(L("Aucun fichier RPM dans ce que tu as déposé.", "No RPM files were found in the drop."))
            return
        queued_files = {path for item in self.queue_items for path in getattr(item, 'file_paths', []) if item.status in {'queued', 'running'}}
        unique_paths = [path for path in rpm_paths if path not in queued_files]
        if not unique_paths:
            self._show_toast(L("Ces fichiers RPM sont déjà dans la file.", "Those RPM files are already queued."))
            return
        label = Path(unique_paths[0]).name if len(unique_paths) == 1 else L(f"{len(unique_paths)} fichiers RPM", f"{len(unique_paths)} RPM files")
        pseudo_app = AppEntry(
            appstream_id='local-rpm-install',
            name=L("Installation RPM locale", "Local RPM Install"),
            summary=L("Installer des fichiers RPM locaux", "Install local RPM files"),
            description=L("Installer des fichiers RPM locaux", "Install local RPM files"),
            pkg_names=[],
        )
        item = QueueItem(app=pseudo_app, action='install-rpms', message=L(f"Installation de {len(unique_paths)} fichier(s) RPM mise en file", f"Queued to install {len(unique_paths)} RPM file(s)"), file_paths=unique_paths, label=label)
        self.queue_items.append(item)
        names = ', '.join(Path(path).name for path in unique_paths[:5]) + ('…' if len(unique_paths) > 5 else '')
        self._append_queue_log(L(f"Installation RPM mise en file : {names}", f"Queued RPM install for {names}"))
        self.status_label.set_text(self._queue_status_text())
        self._refresh_queue_page()
        self._refresh_main_page()
        self._refresh_detail_action_button()
        self._switch_page('system', 'queue')
        if self.backend and not self.queue_worker_running:
            self._prompt_install()

    def _build_top_bar(self) -> Gtk.Widget:
        handle = Gtk.WindowHandle()
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bar.add_css_class("top-bar")
        handle.set_child(bar)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text(L("Rechercher des applications…", "Search applications…"))
        self.search_entry.set_hexpand(False)
        self.search_entry.set_size_request(280, -1)
        self.search_entry.connect("activate", self._on_search_changed)
        bar.append(self.search_entry)

        self.repo_filter_combo = Gtk.ComboBoxText()
        self.repo_filter_combo.append("__all__", L("Tous les dépôts", "All repositories"))
        self.repo_filter_combo.set_active_id("__all__")
        self.repo_filter_combo.connect("changed", self._on_repo_filter_changed)
        self.repo_filter_combo.set_size_request(220, -1)
        self.repo_filter_combo.set_visible(False)
        bar.append(self.repo_filter_combo)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        bar.append(spacer)

        refresh_button = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        refresh_button.connect("clicked", lambda *_: self._load_async(force=True))
        bar.append(refresh_button)

        menu_button = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu_button.set_tooltip_text(L("Réglages des mises à jour", "Updater settings"))
        menu_button.set_popover(self._build_app_menu_popover())

        controls = Gtk.WindowControls()
        controls.set_side(Gtk.PackType.END)
        controls.set_decoration_layout(":minimize,maximize,close")
        bar.append(controls)
        return handle

    def _build_app_menu_popover(self) -> Gtk.Popover:
        popover = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        heading = Gtk.Label(label=L("Vérification des mises à jour", "Update checker"), xalign=0)
        heading.add_css_class("heading")
        box.append(heading)

        self.updater_enabled_check = Gtk.CheckButton(label=L("Activer la vérification des mises à jour", "Enable update checker"))
        self.updater_enabled_check.set_active(bool(self.updater_settings.get("enabled", True)))
        self.updater_enabled_check.connect("toggled", self._on_updater_setting_changed)
        box.append(self.updater_enabled_check)

        self.updater_notifications_check = Gtk.CheckButton(label=L("Activer les notifications", "Enable notifications"))
        self.updater_notifications_check.set_active(bool(self.updater_settings.get("notifications", True)))
        self.updater_notifications_check.connect("toggled", self._on_updater_setting_changed)
        box.append(self.updater_notifications_check)

        interval_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        interval_label = Gtk.Label(label=L("Vérifier toutes les", "Check every"), xalign=0)
        interval_label.set_valign(Gtk.Align.CENTER)
        interval_row.append(interval_label)

        adjustment = Gtk.Adjustment(value=float(self.updater_settings.get("interval_value", 12)), lower=1, upper=999, step_increment=1, page_increment=10)
        self.updater_interval_spin = Gtk.SpinButton(adjustment=adjustment, climb_rate=1, digits=0)
        self.updater_interval_spin.connect("value-changed", self._on_updater_setting_changed)
        interval_row.append(self.updater_interval_spin)

        self.updater_interval_unit = Gtk.ComboBoxText()
        for unit in ("hours", "days", "weeks"):
            self.updater_interval_unit.append(unit, unit.capitalize())
        self.updater_interval_unit.set_active_id(str(self.updater_settings.get("interval_unit", "hours")))
        self.updater_interval_unit.connect("changed", self._on_updater_setting_changed)
        interval_row.append(self.updater_interval_unit)
        box.append(interval_row)

        note = Gtk.Label(label=L("Ces réglages concernent le service de mise à jour de la zone de notification.", "These settings affect the tray updater service."), xalign=0)
        note.add_css_class("dim-label")
        note.set_wrap(True)
        box.append(note)

        popover.set_child(box)
        return popover

    def _on_updater_setting_changed(self, *_args) -> None:
        settings = {
            "enabled": self.updater_enabled_check.get_active(),
            "notifications": self.updater_notifications_check.get_active(),
            "interval_value": int(self.updater_interval_spin.get_value()),
            "interval_unit": self.updater_interval_unit.get_active_id() or "hours",
        }
        save_updater_settings(settings)
        self.updater_settings = load_updater_settings()

    def _on_update_flatpaks_toggled(self, button: Gtk.CheckButton) -> None:
        save_updater_settings({"update_flatpaks": button.get_active()})
        self.updater_settings = load_updater_settings()

    def _build_sidebar(self) -> None:
        self.sidebar_box.append(self._build_source_switch())
        self.sidebar_box.append(self._section_label(L("Système", "System")))
        for key, title in CATEGORY_GROUPS["system"].items():
            icon = CATEGORY_ICONS["system"].get(key)
            self.sidebar_box.append(self._nav_button(key, title, "system", icon, indent=True))

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_start(10)
        separator.set_margin_end(10)
        self.sidebar_box.append(separator)
        self.sidebar_box.append(self._section_label(L("Catégories", "Categories")))
        for key, title in CATEGORY_GROUPS["categories"].items():
            icon = CATEGORY_ICONS["categories"].get(key)
            self.sidebar_box.append(self._nav_button(key, title, "categories", icon, indent=True))

    def _build_source_switch(self) -> Gtk.Widget:
        """Nix | Flatpak — each one is its own catalog (categories, search, Installed)."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box.add_css_class("linked")
        box.set_margin_top(8)
        box.set_margin_bottom(6)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_homogeneous(True)
        self.source_buttons: dict[str, Gtk.ToggleButton] = {}
        group = None
        for key, label in (("nix", "Nix"), ("flatpak", "Flatpak")):
            button = Gtk.ToggleButton(label=label)
            if group is None:
                group = button
            else:
                button.set_group(group)
            button.set_active(key == self.source)
            button.connect("toggled", self._on_source_toggled, key)
            self.source_buttons[key] = button
            box.append(button)
        return box

    def _on_source_toggled(self, button: Gtk.ToggleButton, key: str) -> None:
        if not button.get_active() or key == self.source:
            return
        self.source = key
        self._invalidate_page_caches()
        if self.current_group == "system" and self.current_page in {"repositories", "updates"}:
            self.current_group, self.current_page = "categories", "audiovideo"
        self._switch_page(self.current_group, self.current_page)
        if key == "flatpak" and not any(app.source == "flatpak" for app in self.apps):
            self._show_toast(L("Pas encore de données Flathub. roudix.flatpak.enable est-il activé ? Essaie : flatpak update --appstream", "No Flathub data yet. Is roudix.flatpak.enable on? Try: flatpak update --appstream"))

    def _section_label(self, text: str) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
        box.add_css_class("sidebar-section-box")
        label = Gtk.Label(label=text, xalign=0)
        label.add_css_class("sidebar-section")
        box.append(label)
        return box

    def _nav_button(self, key: str, title: str, group: str, icon_name: str | None = None, indent: bool = False) -> Gtk.Widget:
        button = NavSidebarButton(title, lambda: self._switch_page(group, key), icon_name, indent)
        self.nav_buttons[f"{group}:{key}"] = button
        return button

    def _build_list_page(self) -> None:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.set_vexpand(True)
        self.stack.add_titled(outer, "list", L("Liste", "List"))

        # Horizontal box to hold list and news panel side-by-side
        horiz_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        horiz_container.set_vexpand(True)
        outer.append(horiz_container)

        # Left side: list content
        list_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        list_container.set_vexpand(True)
        list_container.set_hexpand(True)
        horiz_container.append(list_container)

        self.listbox = Gtk.ListBox()
        self.listbox.add_css_class("app-list")
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.set_activate_on_single_click(True)
        self.listbox.connect("row-activated", self._on_row_activated)

        self.list_scroller = Gtk.ScrolledWindow()
        self.list_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.list_scroller.set_child(self.listbox)
        self.list_scroller.set_vexpand(True)
        list_container.append(self.list_scroller)

        self.empty_status = Adw.StatusPage()
        self.empty_status.set_title(L("Aucune application trouvée", "No applications found"))
        self.empty_status.set_description(L("Essaie une autre catégorie ou un autre terme de recherche.", "Try a different category or search term."))
        list_container.append(self.empty_status)
        self.empty_status.set_visible(False)

        # Right side: news panel with revealer
        self.news_panel_revealer = Gtk.Revealer()
        self.news_panel_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_LEFT)
        self.news_panel_revealer.set_transition_duration(250)
        self.news_panel_revealer.set_reveal_child(True)
        horiz_container.append(self.news_panel_revealer)

        news_panel_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        news_panel_box.add_css_class("news-panel")
        news_panel_box.set_size_request(350, -1)
        self.news_panel_revealer.set_child(news_panel_box)

        self.news_panel_scroll = Gtk.ScrolledWindow()
        self.news_panel_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.news_panel_scroll.set_vexpand(True)
        news_panel_box.append(self.news_panel_scroll)

        news_inner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        news_inner_box.set_margin_top(8)
        news_inner_box.set_margin_bottom(20)
        news_inner_box.set_margin_start(12)
        news_inner_box.set_margin_end(12)
        self.news_panel_scroll.set_child(news_inner_box)

        # News panel title
        news_title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        news_title_box.set_margin_top(4)
        news_title_box.set_margin_bottom(8)
        news_title_label = Gtk.Label(label=L("Annonces importantes", "Important Notices"), xalign=0)
        news_title_label.add_css_class("sidebar-section")
        news_title_box.append(news_title_label)
        news_inner_box.append(news_title_box)

        self.news_panel_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.news_panel_card.add_css_class("news-card")
        news_inner_box.append(self.news_panel_card)

        self.news_panel_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.news_panel_card.append(self.news_panel_content_box)

    def _build_queue_page(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(8)
        box.set_margin_bottom(60)
        box.set_margin_start(4)
        box.set_margin_end(4)
        box.set_vexpand(True)
        self.stack.add_titled(box, "queue", L("File d'attente", "Queue"))

        self.queue_progress = Gtk.ProgressBar()
        self.queue_progress.add_css_class("queue-progress")
        box.append(self.queue_progress)

        queue_title = Gtk.Label(label=L("Actions en attente", "Queued actions"), xalign=0)
        queue_title.add_css_class("title-4")
        box.append(queue_title)

        self.queue_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.append(self.queue_list_box)

        log_title = Gtk.Label(label=L("Journal des transactions", "Transaction log"), xalign=0)
        log_title.add_css_class("title-4")
        box.append(log_title)

        self.queue_log_view = Gtk.TextView()
        self.queue_log_view.set_editable(False)
        self.queue_log_view.set_cursor_visible(False)
        self.queue_log_view.set_monospace(True)
        self.queue_log_view.add_css_class("queue-log-view")
        self.queue_log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)

        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        log_scroll.set_vexpand(True)
        log_scroll.set_child(self.queue_log_view)
        box.append(log_scroll)

        queue_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        queue_actions.set_halign(Gtk.Align.START)
        self.queue_apply_button = Gtk.Button(label=L("Appliquer", "Apply"))
        self.queue_apply_button.add_css_class("suggested-action")
        self.queue_apply_button.connect("clicked", lambda *_: self._apply_queue())
        queue_actions.append(self.queue_apply_button)
        self.queue_clear_button = Gtk.Button(label=L("Vider", "Clear"))
        self.queue_clear_button.connect("clicked", lambda *_: self._clear_pending_queue())
        queue_actions.append(self.queue_clear_button)
        self.view_log_button = Gtk.Button(label=L("Voir le journal des transactions", "View transaction log"))
        self.view_log_button.connect("clicked", self._on_view_transaction_log)
        queue_actions.append(self.view_log_button)
        self.send_paste_button = Gtk.Button(label=L("Envoyer sur un pastebin", "Send to pastebin"))
        self.send_paste_button.connect("clicked", self._on_send_to_pastebin)
        queue_actions.append(self.send_paste_button)
        box.append(queue_actions)

        self._refresh_queue_page()

    def _build_repo_page(self) -> None:
        self.repo_scroll = Gtk.ScrolledWindow()
        self.repo_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.repo_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.repo_box.set_margin_top(6)
        self.repo_box.set_margin_bottom(12)
        self.repo_box.set_margin_start(4)
        self.repo_box.set_margin_end(4)
        self.repo_scroll.set_child(self.repo_box)
        self.stack.add_titled(self.repo_scroll, "repos", L("Dépôts", "Repositories"))

    def _build_detail_page(self) -> None:
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.stack.add_titled(scroller, "details", L("Détails", "Details"))

        self.detail_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.detail_box.set_margin_top(8)
        self.detail_box.set_margin_bottom(20)
        self.detail_box.set_margin_start(4)
        self.detail_box.set_margin_end(4)
        scroller.set_child(self.detail_box)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.detail_box.append(top)
        back = Gtk.Button(label=L("← Retour", "← Back"))
        back.connect("clicked", lambda *_: self.stack.set_visible_child_name("list"))
        top.append(back)

        top_spacer = Gtk.Box()
        top_spacer.set_hexpand(True)
        top.append(top_spacer)

        hero = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        hero.add_css_class("detail-hero")
        self.detail_box.append(hero)

        self.detail_icon_box = Gtk.Box()
        hero.append(self.detail_icon_box)

        hero_text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        hero_text.set_hexpand(True)
        hero.append(hero_text)

        self.detail_title = Gtk.Label(xalign=0)
        self.detail_title.add_css_class("title-1")
        self.detail_title.set_wrap(True)
        hero_text.append(self.detail_title)

        self.detail_summary = Gtk.Label(xalign=0)
        self.detail_summary.add_css_class("title-4")
        self.detail_summary.add_css_class("dim-label")
        self.detail_summary.set_wrap(True)
        hero_text.append(self.detail_summary)

        self.detail_meta = Gtk.Label(xalign=0)
        self.detail_meta.set_wrap(True)
        self.detail_meta.set_selectable(True)
        hero_text.append(self.detail_meta)

        # Flatpak only: where to install from (Flathub / Flathub Beta, system / user)
        self.detail_source_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.detail_source_box.set_visible(False)
        source_label = Gtk.Label(label=L("Source", "Source"), xalign=0)
        source_label.add_css_class("dim-label")
        self.detail_source_box.append(source_label)
        self.detail_source = Gtk.DropDown.new_from_strings([""])
        self.detail_source.connect("notify::selected", self._on_detail_source_changed)
        self.detail_source_box.append(self.detail_source)
        hero_text.append(self.detail_source_box)
        self.detail_source_options: list[tuple[str, str]] = []
        self._detail_source_populating = False

        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hero_text.append(action_box)

        self.detail_action_button = Gtk.Button(label=L("Installer", "Install"))
        self.detail_action_button.connect("clicked", lambda *_: self.current_app and self._run_action_for_app(self.current_app, "update" if (self.current_group == "system" and self.current_page == "updates" and self.current_app and self.current_app.installed and self.current_app.candidate_version and self.current_app.candidate_version != self.current_app.installed_version) else None))
        action_box.append(self.detail_action_button)

        self.detail_open_button = Gtk.Button(label=L("Ouvrir", "Open"))
        self.detail_open_button.connect("clicked", self._on_open_clicked)
        action_box.append(self.detail_open_button)

        self.detail_description_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.detail_box.append(self.detail_description_box)

        self.detail_links = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.detail_box.append(self.detail_links)

        self.detail_screenshots = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.detail_box.append(self.detail_screenshots)

    def _refresh_detail_description(self, raw_text: str) -> None:
        if not hasattr(self, "detail_description_box"):
            return
        child = self.detail_description_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.detail_description_box.remove(child)
            child = next_child

        blocks = _markup_blocks_from_text(raw_text or "")
        for block in blocks:
            label = Gtk.Label(xalign=0, yalign=0)
            label.add_css_class("body")
            label.set_wrap(True)
            label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
            label.set_selectable(True)
            label.set_use_markup(True)
            label.set_markup(block)
            label.connect("activate-link", lambda _label, uri: (Gtk.show_uri(None, uri, Gdk.CURRENT_TIME), True)[1])
            self.detail_description_box.append(label)

    def _invalidate_page_caches(self) -> None:
        self._data_revision += 1
        self._page_items_cache.clear()

    def _page_cache_key(self) -> tuple:
        return (
            self._data_revision,
            self.current_group,
            self.current_page,
            self.current_subcategory,
            self.current_search_text,
            self.current_category_filter_text,
            self.current_repo_filter,
            self.source,
        )

    def _show_loading_page(self, message: str) -> None:
        spinner = Gtk.Spinner()
        spinner.start()
        self.status_label.set_text(message)
        self.title_label.set_text(L("Chargement…", "Loading…"))
        self.news_toggle_button.set_visible(False)
        self.news_panel_revealer.set_reveal_child(False)
        self._clear_listbox()
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(64)
        box.set_margin_bottom(64)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_halign(Gtk.Align.CENTER)
        box.append(spinner)
        label = Gtk.Label(label=message)
        box.append(label)
        row.set_child(box)
        self.listbox.append(row)
        self.stack.set_visible_child_name("list")

    def _load_async(self, force: bool = False) -> None:
        if force:
            self._invalidate_page_caches()
        self._is_loading = True
        self._show_loading_page(L("Chargement des métadonnées AppStream et de l'index nixpkgs…", "Loading AppStream metadata and the nixpkgs index…"))

        def worker() -> None:
            try:
                backend = NixBackend()
                if force:
                    backend.reload_state(force_refresh=True)
                catalog = AppStreamCatalog()
                apps = catalog.load()
                backend.enrich_apps(apps)
                repos = backend.get_repositories()
                news_text = self._fetch_news_text()
            except (AppStreamUnavailable, NixUnavailable, Exception) as exc:
                GLib.idle_add(self._load_failed, exc, traceback.format_exc())
                return
            GLib.idle_add(self._load_succeeded, catalog, backend, apps, repos, news_text)

        threading.Thread(target=worker, daemon=True).start()

    def _load_succeeded(self, catalog: AppStreamCatalog, backend: NixBackend, apps: list[AppEntry], repos: list[dict[str, str]], news_text: str) -> bool:
        if self.queue_worker_running:
            # An apply is in flight: this load read local.nix / `flatpak list` before it finished,
            # so adopting it now would bring back a stale state. Try again shortly.
            GLib.timeout_add(500, self._load_succeeded, catalog, backend, apps, repos, news_text)
            return False
        if self.backend is not None:
            # Actions may have completed since the background thread read its state: re-read it.
            backend.reload_state()
            backend.enrich_apps(apps)
        self._is_loading = False
        self.catalog = catalog
        self.backend = backend
        self.apps = apps
        self._appstream_pkg_names = {pkg for app in apps for pkg in app.pkg_names}
        self.repos = repos
        self.news_text = news_text
        self._invalidate_page_caches()
        self._refresh_news_page()
        n_nix = sum(a.source == 'nix' for a in apps)
        n_flatpak = sum(a.source == 'flatpak' for a in apps)
        self.status_label.set_text(L(f"{len(apps)} applications chargées ({n_nix} nixpkgs, {n_flatpak} Flatpak).", f"Loaded {len(apps)} applications ({n_nix} nixpkgs, {n_flatpak} Flatpak)."))
        self._rebuild_repo_page()
        self._populate_repo_filter_dropdown()
        self._switch_page(self.current_group, self.current_page)
        self._refresh_queue_page()
        return False

    def _fetch_news_text(self) -> str:
        return ""
        url = ""
        if not url:
            return L("Aucune URL de flux de mises à jour n'est configurée.", "No update feed URL is configured.")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DNF App Center/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = response.read()
            text = data.decode("utf-8", errors="replace").strip()
            return text or L("Aucune actualité disponible.", "No news available.")
        except Exception as exc:
            return L(f"Impossible de charger les actualités depuis {url}.\n\n{exc}", f"Failed to load news from {url}.\n\n{exc}")

    def _refresh_news_page(self) -> None:
        if not hasattr(self, "news_panel_content_box"):
            return
        child = self.news_panel_content_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.news_panel_content_box.remove(child)
            child = next_child

        raw_text = (getattr(self, "news_text", L("Chargement des actualités…", "Loading news…")) or L("Aucune actualité disponible.", "No news available.")).strip()
        sections = [part.strip() for part in raw_text.replace("\r\n", "\n").split("\n\n") if part.strip()]
        if not sections:
            sections = [L("Aucune actualité disponible.", "No news available.")]

        for section in sections:
            label = Gtk.Label(xalign=0, yalign=0)
            label.add_css_class("news-body")
            label.set_wrap(True)
            label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
            label.set_selectable(True)
            label.set_use_markup(True)
            label.set_markup(section)
            label.connect("activate-link", lambda _label, uri: (Gtk.show_uri(None, uri, Gdk.CURRENT_TIME), True)[1])
            self.news_panel_content_box.append(label)

    def _load_failed(self, exc: Exception, tb: str) -> bool:
        self._is_loading = False
        self.status_label.set_text(L("Échec du chargement des métadonnées.", "Failed to load metadata."))
        self._show_toast(str(exc))
        self.title_label.set_text(L("Échec du démarrage", "Startup failed"))
        self._clear_listbox()
        row = Gtk.ListBoxRow()
        label = Gtk.Label(label=f"{exc}\n\n{tb}", xalign=0)
        label.set_wrap(True)
        label.set_selectable(True)
        label.set_margin_top(18)
        label.set_margin_bottom(18)
        label.set_margin_start(18)
        label.set_margin_end(18)
        row.set_child(label)
        self.listbox.append(row)
        return False

    def _switch_page(self, group: str, key: str) -> None:
        if self.current_search_text or self.search_entry.get_text():
            self.search_entry.set_text("")
        self.current_search_text = ""
        if self.current_category_filter_text or self.category_filter_entry.get_text():
            self.category_filter_entry.set_text("")
        self.current_category_filter_text = ""
        self.current_repo_filter = "__all__"
        self.current_group = group
        self.current_page = key
        self.current_subcategory = None
        self._update_nav_buttons()
        self._rebuild_subcategories()
        if self._is_loading:
            self._show_loading_page(L("Chargement des métadonnées AppStream et de l'index nixpkgs…", "Loading AppStream metadata and the nixpkgs index…"))
            return
        self._refresh_main_page(preserve_scroll=False)

    def _update_nav_buttons(self) -> None:
        for button in self.nav_buttons.values():
            if hasattr(button, "set_active"):
                button.set_active(False)
            else:
                button.remove_css_class("active")
        active = self.nav_buttons.get(f"{self.current_group}:{self.current_page}")
        if active is not None:
            if hasattr(active, "set_active"):
                active.set_active(True)
            else:
                active.add_css_class("active")

    def _rebuild_subcategories(self) -> None:
        self.subcategory_buttons.clear()
        self.subcategory_button_pages.clear()
        self.subcategory_pages = []
        self.current_subcategory_page = 0

        child = self.subcategory_stack.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.subcategory_stack.remove(child)
            child = next_child

        subcats = SUBCATEGORY_GROUPS.get(self.current_page, {}) if self.current_group == "categories" else {}
        has_subcats = bool(subcats)
        self.subcategory_strip.set_visible(has_subcats)
        if not subcats:
            return

        entries: list[tuple[str, str]] = [("__all__", L("Tout", "All"))]
        entries.extend((key, title) for key, title in subcats.items())
        self.subcategory_pages = self._paginate_subcategories(entries)

        for page_index, page_entries in enumerate(self.subcategory_pages):
            page = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            page.add_css_class("subcat-page")
            page.set_hexpand(False)
            page.set_halign(Gtk.Align.CENTER)
            page.set_valign(Gtk.Align.CENTER)

            for key, title in page_entries:
                callback_key = None if key == "__all__" else key
                button = SubcategoryButton(title, lambda s=callback_key: self._select_subcategory(s))
                page.append(button)
                self.subcategory_buttons[key] = button
                self.subcategory_button_pages[key] = page_index

            self.subcategory_stack.add_named(page, f"page-{page_index}")

        self._highlight_subcategory_button()
        self._set_subcategory_page(self.subcategory_button_pages.get("__all__", 0), animate=False)

    def _paginate_subcategories(self, entries: list[tuple[str, str]]) -> list[list[tuple[str, str]]]:
        available_width = self._subcategory_page_width()
        pages: list[list[tuple[str, str]]] = []
        current_page: list[tuple[str, str]] = []
        current_width = 0

        for key, title in entries:
            item_width = self._estimate_subcategory_width(title)
            if current_page and current_width + item_width > available_width:
                pages.append(current_page)
                current_page = [(key, title)]
                current_width = item_width
            else:
                current_page.append((key, title))
                current_width += item_width

        if current_page:
            pages.append(current_page)

        return pages or [entries]

    def _subcategory_page_width(self) -> int:
        window_width = 0
        try:
            window_width = int(self.get_width())
        except Exception:
            window_width = 0

        if window_width <= 0:
            window_width = 1280

        available = window_width - 420
        return max(320, available)

    def _estimate_subcategory_width(self, title: str) -> int:
        return max(74, 32 + (len(title) * 9))

    def _select_subcategory(self, key: str | None) -> None:
        self.current_subcategory = key
        self._highlight_subcategory_button()
        self._refresh_main_page()

    def _highlight_subcategory_button(self) -> None:
        for key, button in self.subcategory_buttons.items():
            if hasattr(button, "set_active"):
                button.set_active(False)
            else:
                button.remove_css_class("active")

        active = "__all__" if self.current_subcategory is None else self.current_subcategory
        button = self.subcategory_buttons.get(active)
        if button is not None:
            if hasattr(button, "set_active"):
                button.set_active(True)
            else:
                button.add_css_class("active")
            page_index = self.subcategory_button_pages.get(active, 0)
            self._set_subcategory_page(page_index)
        else:
            self._set_subcategory_page(0, animate=False)

    def _set_subcategory_page(self, page_index: int, animate: bool = True) -> None:
        if not self.subcategory_pages:
            self.subcat_left_button.set_sensitive(False)
            self.subcat_right_button.set_sensitive(False)
            return

        page_index = max(0, min(len(self.subcategory_pages) - 1, page_index))
        current_index = self.current_subcategory_page
        self.current_subcategory_page = page_index

        try:
            transition_type = Gtk.StackTransitionType.SLIDE_LEFT_RIGHT
            if page_index < current_index:
                transition_type = Gtk.StackTransitionType.SLIDE_RIGHT
            elif page_index > current_index:
                transition_type = Gtk.StackTransitionType.SLIDE_LEFT
            if not animate:
                transition_type = Gtk.StackTransitionType.NONE
            self.subcategory_stack.set_transition_type(transition_type)
        except Exception:
            pass

        self.subcategory_stack.set_visible_child_name(f"page-{page_index}")
        left_available = page_index > 0
        right_available = page_index < len(self.subcategory_pages) - 1
        self.subcat_left_button.set_sensitive(left_available)
        self.subcat_right_button.set_sensitive(right_available)
        self._set_pan_button_available(self.subcat_left_button, left_available)
        self._set_pan_button_available(self.subcat_right_button, right_available)

    def _set_pan_button_available(self, button: Gtk.Button, available: bool) -> None:
        if available:
            button.add_css_class("available")
        else:
            button.remove_css_class("available")

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        self.current_search_text = entry.get_text().strip()
        self._refresh_main_page()

    def _on_category_filter_changed(self, entry: Gtk.SearchEntry) -> None:
        self.current_category_filter_text = entry.get_text().strip()
        self._refresh_main_page(preserve_scroll=False)

    def _current_page_key(self) -> str:
        """Get a unique key for the current page to store view mode preference."""
        if self.current_search_text:
            return "search"
        return f"{self.current_group}:{self.current_page}"

    def _on_grid_view_toggled(self, button: Gtk.ToggleButton) -> None:
        if self._updating_view_buttons:
            return
        if button.get_active() and self.view_mode != "grid":
            self._updating_view_buttons = True
            self.view_mode = "grid"
            self.list_view_button.set_active(False)
            save_view_mode(self._current_page_key(), "grid")
            self._updating_view_buttons = False
            self._refresh_main_page(preserve_scroll=False)

    def _on_list_view_toggled(self, button: Gtk.ToggleButton) -> None:
        if self._updating_view_buttons:
            return
        if button.get_active() and self.view_mode != "list":
            self._updating_view_buttons = True
            self.view_mode = "list"
            self.grid_view_button.set_active(False)
            save_view_mode(self._current_page_key(), "list")
            self._updating_view_buttons = False
            self._refresh_main_page(preserve_scroll=False)

    def _on_news_toggle(self, button: Gtk.ToggleButton) -> None:
        self.news_panel_visible = button.get_active()
        self.news_panel_revealer.set_reveal_child(self.news_panel_visible)

    def _on_repo_filter_changed(self, combo: Gtk.ComboBoxText) -> None:
        self.current_repo_filter = combo.get_active_id() or "__all__"
        self._refresh_main_page()

    def _populate_repo_filter_dropdown(self) -> None:
        current = getattr(self, "current_repo_filter", "__all__") or "__all__"
        combo = self.repo_filter_combo
        combo.remove_all()
        combo.append("__all__", L("Tous les dépôts", "All repositories"))
        for repo in getattr(self, "repos", []):
            repo_id = repo.get("id", "")
            if not repo_id:
                continue
            label = repo.get("name") or repo_id
            combo.append(repo_id, label)
        combo.set_active_id(current if any((repo.get("id") == current) for repo in getattr(self, "repos", [])) else "__all__")
        self.current_repo_filter = combo.get_active_id() or "__all__"

    def _on_subcat_pan_start(self, _button: Gtk.Button) -> None:
        self._set_subcategory_page(self.current_subcategory_page - 1)

    def _on_subcat_pan_end(self, _button: Gtk.Button) -> None:
        self._set_subcategory_page(self.current_subcategory_page + 1)



    def _get_scroll_position_for_visible_page(self) -> tuple[str | None, float]:
        if not hasattr(self, "stack"):
            return None, 0.0
        visible = self.stack.get_visible_child_name()
        scroller = None
        if visible == "list" and hasattr(self, "list_scroller"):
            scroller = self.list_scroller
        elif visible == "repos" and hasattr(self, "repo_scroll"):
            scroller = self.repo_scroll
        elif visible == "details":
            scroller = self.stack.get_child_by_name("details")
        if scroller is None:
            return visible, 0.0
        adj = scroller.get_vadjustment()
        return visible, float(adj.get_value())

    def _restore_scroll_position(self, visible: str | None, value: float) -> bool:
        if not hasattr(self, "stack"):
            return False
        current_visible = self.stack.get_visible_child_name()
        if current_visible != visible:
            return False
        scroller = None
        if visible == "list" and hasattr(self, "list_scroller"):
            scroller = self.list_scroller
        elif visible == "repos" and hasattr(self, "repo_scroll"):
            scroller = self.repo_scroll
        elif visible == "details":
            scroller = self.stack.get_child_by_name("details")
        if scroller is None:
            return False
        adj = scroller.get_vadjustment()
        upper = max(adj.get_lower(), adj.get_upper() - adj.get_page_size())
        adj.set_value(max(adj.get_lower(), min(value, upper)))
        return False

    def _scroll_visible_page_to_top(self) -> bool:
        visible = self.stack.get_visible_child_name()
        scroller = None
        if visible == "list" and hasattr(self, "list_scroller"):
            scroller = self.list_scroller
        elif visible == "repos" and hasattr(self, "repo_scroll"):
            scroller = self.repo_scroll
        elif visible == "details":
            scroller = self.stack.get_child_by_name("details")
        if scroller is None:
            return False
        adj = scroller.get_vadjustment()
        adj.set_value(adj.get_lower())
        return False

    def _refresh_main_page(self, preserve_scroll: bool = True) -> None:
        if preserve_scroll:
            visible_before, scroll_before = self._get_scroll_position_for_visible_page()
        else:
            visible_before, scroll_before = None, 0.0
        in_search_mode = bool(self.current_search_text)
        if not in_search_mode and self.current_group == "system" and self.current_page == "repositories":
            self.title_label.set_text(CATEGORY_GROUPS["system"]["repositories"])
            n_repos = len(getattr(self, 'repos', []))
            self.status_label.set_text(L(f"{n_repos} dépôts affichés.", f"Showing {n_repos} repositories."))
            self.stack.set_visible_child_name("repos")
            if preserve_scroll:
                GLib.idle_add(self._restore_scroll_position, visible_before, scroll_before)
            else:
                GLib.idle_add(self._scroll_visible_page_to_top)
            return
        if not in_search_mode and self.current_group == "system" and self.current_page == "queue":
            self.title_label.set_text(CATEGORY_GROUPS["system"]["queue"])
            self.status_label.set_text("")
            self.updates_action_bar.set_visible(False)
            self._refresh_queue_page()
            self.stack.set_visible_child_name("queue")
            if preserve_scroll:
                GLib.idle_add(self._restore_scroll_position, visible_before, scroll_before)
            else:
                GLib.idle_add(self._scroll_visible_page_to_top)
            return

        show_local_filter = (not in_search_mode and ((self.current_group == "categories") or (self.current_group == "system" and self.current_page in {"installed", "updates"})))
        self.category_filter_entry.set_visible(show_local_filter)
        self.view_toggle_box.set_visible(show_local_filter)

        # Show news toggle only on updates page
        show_news_toggle = (not in_search_mode and self.current_group == "system" and self.current_page == "updates")
        self.news_toggle_button.set_visible(show_news_toggle)
        self.news_panel_revealer.set_reveal_child(show_news_toggle and self.news_panel_visible)

        # Restore saved view mode for this page
        if show_local_filter:
            saved_mode = get_view_mode(self._current_page_key(), "grid")
            if saved_mode != self.view_mode:
                self._updating_view_buttons = True
                self.view_mode = saved_mode
                if saved_mode == "grid":
                    self.grid_view_button.set_active(True)
                    self.list_view_button.set_active(False)
                else:
                    self.list_view_button.set_active(True)
                    self.grid_view_button.set_active(False)
                self._updating_view_buttons = False

        items = self._filtered_apps_for_current_page()
        self.current_items = items
        self.title_label.set_text(self._page_title())
        repo_note = ''
        if self.current_repo_filter != '__all__':
            repo_name = next((repo.get('name') or repo.get('id') for repo in getattr(self, 'repos', []) if repo.get('id') == self.current_repo_filter), self.current_repo_filter)
            repo_note = L(f' dans {repo_name}', f' in {repo_name}')
        if in_search_mode:
            self.status_label.set_text(L(f'Résultats pour « {self.current_search_text} » ({len(items)} applications{repo_note}).', f'Search results for “{self.current_search_text}” ({len(items)} applications{repo_note}).'))
        else:
            extra = ""
            if show_local_filter and self.current_category_filter_text:
                extra = L(f' correspondant à « {self.current_category_filter_text} »', f' matching “{self.current_category_filter_text}”')
            self.status_label.set_text(L(f"{len(items)} applications affichées{repo_note}{extra}.", f"Showing {len(items)} applications{repo_note}{extra}."))
        self._refresh_updates_action_bar(items)
        self._rebuild_listbox(items)
        self.stack.set_visible_child_name("list")
        if preserve_scroll:
            GLib.idle_add(self._restore_scroll_position, visible_before, scroll_before)
        else:
            GLib.idle_add(self._scroll_visible_page_to_top)

    def _filtered_apps_for_current_page(self) -> list[AppEntry]:
        cache_key = self._page_cache_key()
        cached = self._page_items_cache.get(cache_key)
        if cached is not None:
            return list(cached)

        items = [app for app in self.apps if app.source == self.source]
        needle = self.current_search_text.casefold()
        show_local_filter = ((self.current_group == "categories") or (self.current_group == "system" and self.current_page in {"installed", "updates"})) and not bool(needle)

        if needle:
            items = [
                app for app in items
                if needle in app.name.casefold()
                or needle in app.summary.casefold()
                or needle in app.description.casefold()
                or any(needle in item.casefold() for item in app.categories)
                or any(needle in item.casefold() for item in app.keywords)
                or any(needle in item.casefold() for item in app.pkg_names)
            ]
            if self.current_repo_filter != "__all__":
                items = [app for app in items if self.current_repo_filter in app.repo_ids]

            merged: list[AppEntry] = list(items)
            seen_pkgs = {pkg for app in merged for pkg in app.pkg_names}
            if self.backend is not None and self.source == "nix":
                try:
                    fallback = self.backend.search_packages(needle, repo_id=self.current_repo_filter)
                except Exception:
                    fallback = []
                for app in fallback:
                    if any(pkg in seen_pkgs for pkg in app.pkg_names):
                        continue
                    merged.append(app)
                    seen_pkgs.update(app.pkg_names)

            merged.sort(key=lambda item: self._search_rank_key(item, needle))
            self._page_items_cache[cache_key] = list(merged)
            return list(merged)
        else:
            if self.current_group == "system":
                if self.current_page == "installed":
                    items = [app for app in items if app.installed]
                    seen_pkgs = {pkg for app in items for pkg in app.pkg_names}
                    if self.backend is not None and self.source == "nix":
                        try:
                            fallback_installed = self.backend.get_installed_packages(repo_id=self.current_repo_filter)
                        except Exception:
                            fallback_installed = []
                        for app in fallback_installed:
                            if any(pkg in seen_pkgs for pkg in app.pkg_names):
                                continue
                            items.append(app)
                            seen_pkgs.update(app.pkg_names)
                elif self.current_page == "updates":
                    if self.backend is not None:
                        try:
                            items = self.backend.get_upgradable_packages(repo_id=self.current_repo_filter)
                        except Exception:
                            items = []
                    else:
                        items = []
            elif self.current_group == "categories":
                page_key = self.current_page.casefold()
                items = [app for app in items if self._has_category(app, page_key)]
                items = [app for app in items if (app.launchables or app.kind != "PACKAGE") or not should_hide_from_standard_catalog(app)]
                if self.current_subcategory:
                    sub = self.current_subcategory.casefold()
                    items = [app for app in items if self._has_category(app, sub)]

        if show_local_filter and self.current_category_filter_text:
            local_needle = self.current_category_filter_text.casefold()
            items = [
                app for app in items
                if local_needle in app.name.casefold()
                or local_needle in app.summary.casefold()
                or local_needle in app.description.casefold()
                or any(local_needle in item.casefold() for item in app.categories)
                or any(local_needle in item.casefold() for item in app.keywords)
                or any(local_needle in item.casefold() for item in app.pkg_names)
            ]

        if self.current_repo_filter != "__all__":
            items = [app for app in items if self.current_repo_filter in app.repo_ids]

        items.sort(key=lambda item: item.name.casefold())
        self._page_items_cache[cache_key] = list(items)
        return list(items)

    def _search_rank_key(self, app: AppEntry, needle: str) -> tuple[int, int, int, str]:
        pkg_names = [pkg.casefold() for pkg in app.pkg_names if pkg]
        app_name = app.name.casefold()
        summary = app.summary.casefold()

        def _best_pos(values: list[str]) -> int:
            positions = [value.find(needle) for value in values if needle in value]
            return min(positions) if positions else 9999

        exact_pkg = any(pkg == needle for pkg in pkg_names)
        prefix_pkg = any(pkg.startswith(needle) for pkg in pkg_names)
        exact_name = app_name == needle
        prefix_name = app_name.startswith(needle)
        pkg_pos = _best_pos(pkg_names)
        name_pos = app_name.find(needle) if needle in app_name else 9999
        summary_pos = summary.find(needle) if needle in summary else 9999
        best_pos = min(pkg_pos, name_pos, summary_pos)

        # Lower rank wins.
        if exact_pkg:
            rank = 0
        elif prefix_pkg:
            rank = 1
        elif exact_name:
            rank = 2
        elif prefix_name:
            rank = 3
        elif pkg_pos != 9999:
            rank = 4
        elif name_pos != 9999:
            rank = 5
        elif summary_pos != 9999:
            rank = 6
        else:
            rank = 7

        shortest_prefix_len = min((len(pkg) for pkg in pkg_names if pkg.startswith(needle)), default=9999)
        return (rank, best_pos, shortest_prefix_len, app.name.casefold())

    def _has_category(self, app: AppEntry, category: str) -> bool:
        categories = {item.casefold() for item in app.categories}
        aliases = {
            "office": {"office", "productivity"},
            "graphics": {"graphics", "photography"},
            "audiovideo": {"audio", "video", "audiovideo"},
            "network": {"network", "networking", "internet"},
            "development": {"development", "developer tools", "devel", "programming"},
            "game": {"game", "games"},
            "utility": {"utility", "utilities"},
            "system": {"system"},
            "science": {"science"},
            "education": {"education"},
        }
        wanted = aliases.get(category, {category})
        return bool(categories & wanted) or category in categories

    def _page_title(self) -> str:
        if self.current_search_text:
            return L("Recherche", "Search")
        if self.current_group == "system":
            return CATEGORY_GROUPS["system"][self.current_page]
        title = CATEGORY_GROUPS["categories"].get(self.current_page, self.current_page.title())
        if self.current_subcategory:
            sub = SUBCATEGORY_GROUPS.get(self.current_page, {}).get(self.current_subcategory, self.current_subcategory)
            return f"{title} » {sub}"
        return title

    def _rebuild_listbox(self, items: list[AppEntry] | None = None) -> None:
        self._clear_listbox()
        self._listbox_gen += 1
        gen = self._listbox_gen
        items = list(items or [])
        self.empty_status.set_visible(not items)
        if not items:
            return

        update_mode = self.current_group == "system" and self.current_page == "updates" and not self.current_search_text
        compact_grid = (self.view_mode == "grid")
        cols = 3
        # Chunk size must be a multiple of cols so grid rows are never split across batches
        chunk_size = 30

        def make_row(app: AppEntry) -> AppCardRow:
            return AppCardRow(
                app,
                (lambda entry, mode=("update" if update_mode else None): self._run_action_for_app(entry, mode)),
                self._open_details,
                self._queued_state_label,
                page_mode=("updates" if update_mode else "default"),
                update_selected=(app.primary_pkg in self.update_selection if app.primary_pkg else False),
                update_toggle_cb=self._toggle_update_selection if update_mode else None,
            )

        def make_tile_row(chunk: list[AppEntry]) -> Gtk.ListBoxRow:
            row = Gtk.ListBoxRow()
            row.set_activatable(False)
            row.set_selectable(False)
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row_box.set_homogeneous(True)
            for app in chunk:
                tile = AppCardTile(
                    app,
                    (lambda entry, mode=("update" if update_mode else None): self._run_action_for_app(entry, mode)),
                    self._open_details,
                    self._queued_state_label,
                    page_mode=("updates" if update_mode else "default"),
                    update_selected=(app.primary_pkg in self.update_selection if app.primary_pkg else False),
                    update_toggle_cb=self._toggle_update_selection if update_mode else None,
                )
                row_box.append(tile)
            for _ in range(cols - len(chunk)):
                spacer = Gtk.Box()
                spacer.set_hexpand(True)
                row_box.append(spacer)
            row.set_child(row_box)
            return row

        def add_chunk(start: int) -> bool:
            if self._listbox_gen != gen:
                return GLib.SOURCE_REMOVE
            end = min(start + chunk_size, len(items))
            if not compact_grid:
                for i in range(start, end):
                    self.listbox.append(make_row(items[i]))
            else:
                for i in range(start, end, cols):
                    self.listbox.append(make_tile_row(items[i:i + cols]))
            if end < len(items):
                GLib.idle_add(add_chunk, end, priority=GLib.PRIORITY_LOW)
            return GLib.SOURCE_REMOVE

        add_chunk(0)

    def _clear_listbox(self) -> None:
        child = self.listbox.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.listbox.remove(child)
            child = next_child

    def _rebuild_repo_page(self) -> None:
        child = self.repo_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.repo_box.remove(child)
            child = next_child
        for repo in getattr(self, "repos", []):
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            card.add_css_class("repo-card")

            top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            card.append(top)

            labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            labels.set_hexpand(True)
            top.append(labels)

            name = Gtk.Label(xalign=0)
            name.set_markup(f"<b>{GLib.markup_escape_text(repo['name'] or repo['id'])}</b>")
            labels.append(name)

            rid = Gtk.Label(label=repo["id"], xalign=0)
            rid.add_css_class("dim-label")
            labels.append(rid)

            toggle = Gtk.Switch()
            toggle.set_valign(Gtk.Align.CENTER)
            toggle.set_active(bool(repo.get("enabled", True)))
            toggle.connect("state-set", self._on_repo_toggle_state_set, repo["id"])
            top.append(toggle)

            if repo.get("baseurl"):
                url = Gtk.Label(label=repo["baseurl"], xalign=0)
                url.set_wrap(True)
                url.set_selectable(True)
                card.append(url)
            self.repo_box.append(card)

    def _on_repo_toggle_state_set(self, switch: Gtk.Switch, state: bool, repo_id: str) -> bool:
        switch.set_sensitive(False)

        def worker() -> None:
            ok, message = self.backend.set_repository_enabled(repo_id, state)
            GLib.idle_add(self._repo_toggle_done, switch, repo_id, state, ok, message)

        threading.Thread(target=worker, daemon=True).start()
        return True

    def _repo_toggle_done(self, switch: Gtk.Switch, repo_id: str, state: bool, ok: bool, message: str) -> bool:
        switch.set_sensitive(True)
        if ok:
            self.repos = self.backend.get_repositories()
            self._rebuild_repo_page()
            self._show_toast(message)
            return False
        switch.set_state(not state)
        switch.set_active(not state)
        self._show_toast(message)
        return False

    def _on_row_activated(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        if hasattr(row, "app"):
            self._open_details(row.app)

    def _open_details(self, app: AppEntry, keep_source: bool = False) -> None:
        self.current_app = app
        child = self.detail_icon_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.detail_icon_box.remove(child)
            child = next_child
        self.detail_icon_box.append(IconWidget(app, 128))
        self.detail_title.set_text(app.name)
        self.detail_summary.set_text(app.summary)
        self._refresh_detail_description(app.description)

        lines = []
        if app.pkg_names:
            lines.append(L("Paquets : ", "Packages: ") + ', '.join(app.pkg_names))
        if app.installed_version:
            lines.append(L("Installé : ", "Installed: ") + str(app.installed_version))
        if app.candidate_version:
            lines.append(L("Disponible : ", "Available: ") + str(app.candidate_version))
        if app.repo_ids:
            lines.append(L("Dépôts : ", "Repositories: ") + ', '.join(app.repo_ids))
        if app.categories:
            lines.append(L("Catégories : ", "Categories: ") + ', '.join(app.categories))
        self.detail_meta.set_text("\n".join(lines))

        self.stack.set_visible_child_name("details")
        self._populate_detail_sources(app, reset=not keep_source)
        self._refresh_detail_action_button(repopulate=False)

        self._rebuild_detail_links(app)
        self._rebuild_detail_screenshots(app)
        self.stack.set_visible_child_name("details")

    def _refresh_detail_action_button(self, repopulate: bool = True) -> None:
        if not getattr(self, "current_app", None):
            return
        app = self.current_app
        if repopulate and self._has_sources(app):
            self._populate_detail_sources(app)  # refresh the "installed" marks
        queued_label = self._queued_state_label(app)
        installed_here = self._target_installed(app)
        self.detail_action_button.set_label(self._detail_button_label(app, queued_label))
        self.detail_action_button.set_sensitive(bool(app.primary_pkg and self.backend) and queued_label != "Running")
        self.detail_action_button.remove_css_class("destructive-action")
        self.detail_action_button.remove_css_class("suggested-action")
        self.detail_action_button.add_css_class("destructive-action" if installed_here else "suggested-action")
        self.detail_open_button.set_sensitive(bool(app.launchables) and app.installed)
        if self.backend and app.source == "nix" and self._has_sources(app) and not queued_label \
                and self._source_state(app, *self._source_target(app)) == "external":
            self.detail_action_button.set_label(L("Installée (config Roudix)", "Installed (Roudix config)"))
            self.detail_action_button.set_sensitive(False)
            self.detail_action_button.remove_css_class("destructive-action")

    def _detail_button_label(self, app: AppEntry, queued_label: str | None) -> str:
        if queued_label == "Queued":
            return L("Retirer de la file", "Remove from queue")
        if queued_label:
            return {"Running": L("En cours", "Running")}.get(queued_label, queued_label)
        return self._default_action_label(app)

    def _default_action_label(self, app: AppEntry) -> str:
        if self.current_group == "system" and self.current_page == "updates" and app.installed and app.candidate_version and app.candidate_version != app.installed_version:
            return L("Mettre à jour", "Update")
        return L("Supprimer", "Remove") if self._target_installed(app) else L("Installer", "Install")

    # ── source chooser (GNOME Software style): Nix user/system, Flatpak remote x user/system ──
    @staticmethod
    def _has_sources(app: AppEntry) -> bool:
        return app.source in ("nix", "flatpak") and bool(app.primary_pkg)

    def _source_options(self, app: AppEntry) -> list[tuple[str, str]]:
        """[(remote, "system"|"user")]. Nix: nixpkgs, then one more remote per flake that provides the
        app; user = Home Manager."""
        if app.source == "flatpak":
            return [(remote, scope) for remote in app.repo_ids for scope in ("system", "user")]
        return [(remote, scope) for remote in self.backend.nix_remotes(app) for scope in ("user", "system")]

    def _source_state(self, app: AppEntry, remote: str, scope: str) -> str | None:
        if app.source == "flatpak":
            return self.backend.flatpak_state(app, remote, scope)
        return self.backend.nix_state(app, scope, remote)

    def _installed_sources(self, app: AppEntry) -> list[tuple[str, str]]:
        if app.source == "flatpak":
            return self.backend.flatpak_installed_sources(app)
        return self.backend.nix_installed_sources(app)

    def _source_label(self, app: AppEntry, remote: str, scope: str) -> str:
        if app.source == "flatpak":
            where = L("Système", "System") if scope == "system" else L("Utilisateur", "User")
            return f"{localnix.FLATPAK_REMOTE_LABELS.get(remote, remote)} · {where}"
        where = L("Système", "System") if scope == "system" else L("Utilisateur (Home Manager)", "User (Home Manager)")
        return f"{'Nix' if remote == 'nixpkgs' else self.backend.flake_label(remote)} · {where}"

    def _source_scope_key(self, app: AppEntry, remote: str, scope: str) -> str:
        """local.nix scope an action on this source is recorded in."""
        if app.source == "flatpak":
            return self.backend.flatpak_scope_key(remote, scope == "system")
        return self.backend.nix_scope_key(scope, remote)

    def _target_installed(self, app: AppEntry) -> bool:
        """Is the thing the button acts on installed? With sources, that is the chosen source."""
        if not self.backend or not self._has_sources(app):
            return app.installed
        remote, scope = self._source_target(app)
        return self._source_state(app, remote, scope) is not None

    def _source_target(self, app: AppEntry) -> tuple[str, str]:
        """(remote, "system"|"user") an action on `app` applies to: the chosen source on its
        page; elsewhere (cards, lists) the place it is installed, else the default
        (Flathub system for Flatpak, user/Home Manager for Nix)."""
        on_page = getattr(self, "current_app", None) is app and self.stack.get_visible_child_name() == "details"
        options = getattr(self, "detail_source_options", [])
        if on_page and options:
            index = self.detail_source.get_selected()
            if 0 <= index < len(options):
                return options[index]
        if self.backend:
            installed = self._installed_sources(app)
            if installed:
                return installed[0]
        if app.source == "flatpak":
            return (app.repo_ids[0] if app.repo_ids else "flathub", "system")
        return (self.backend.nix_remotes(app)[0] if self.backend else "nixpkgs", "user")

    def _populate_detail_sources(self, app: AppEntry, reset: bool = False) -> None:
        has = bool(self.backend) and self._has_sources(app)
        self.detail_source_box.set_visible(has)
        if not has:
            self.detail_source_options = []
            return
        options = self._source_options(app)
        previous = None
        if not reset and self.detail_source_options:
            index = self.detail_source.get_selected()
            if 0 <= index < len(self.detail_source_options):
                previous = self.detail_source_options[index]
        if previous in options:
            choice = previous
        else:
            installed = [src for src in self._installed_sources(app) if src in options]
            choice = installed[0] if installed else self._default_source(app, options)
        labels = []
        for remote, scope in options:
            label = self._source_label(app, remote, scope)
            state = self._source_state(app, remote, scope)
            if state == "external" and app.source == "nix":
                label += f"  ({L('installé via la config', 'installed via config')})"
            elif state:
                label += f"  ({L('installé', 'installed')})"
            labels.append(label)
        self._detail_source_populating = True
        try:
            self.detail_source_options = options
            self.detail_source.set_model(Gtk.StringList.new(labels))
            self.detail_source.set_selected(options.index(choice))
        finally:
            self._detail_source_populating = False

    @staticmethod
    def _default_source(app: AppEntry, options: list[tuple[str, str]]) -> tuple[str, str]:
        return options[0]  # Flatpak: Flathub system; Nix: user (Home Manager)

    def _on_detail_source_changed(self, *_args) -> None:
        if self._detail_source_populating or not getattr(self, "current_app", None):
            return
        self._refresh_detail_action_button(repopulate=False)

    def _rebuild_detail_links(self, app: AppEntry) -> None:
        child = self.detail_links.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.detail_links.remove(child)
            child = next_child
        if app.homepage_url:
            button = Gtk.LinkButton.new_with_label(app.homepage_url, L("Site web", "Homepage"))
            self.detail_links.append(button)

    def _rebuild_detail_screenshots(self, app: AppEntry) -> None:
        child = self.detail_screenshots.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.detail_screenshots.remove(child)
            child = next_child
        if not app.screenshots:
            return

        title = Gtk.Label(label=L("Captures d'écran", "Screenshots"), xalign=0)
        title.add_css_class("title-4")
        self.detail_screenshots.append(title)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_row_spacing(12)
        flow.set_column_spacing(12)
        flow.set_max_children_per_line(2)
        flow.set_min_children_per_line(1)
        self.detail_screenshots.append(flow)

        added_any = False
        for ref in app.screenshots[:6]:
            picture = _picture_from_ref(ref, 560, 315)
            child_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            child_box.set_margin_bottom(6)
            if picture is not None:
                frame = Gtk.Frame()
                frame.set_child(picture)
                child_box.append(frame)
                added_any = True
            else:
                child_box.append(Gtk.LinkButton.new_with_label(ref, ref))
            flow.insert(child_box, -1)

        if not added_any:
            note = Gtk.Label(label=L("Impossible de charger les captures d'écran en local.", "Screenshots could not be loaded locally."), xalign=0)
            note.add_css_class("dim-label")
            self.detail_screenshots.append(note)

    def _source_queue_key(self, app: AppEntry) -> str:
        remote, scope = self._source_target(app)
        return self._source_scope_key(app, remote, scope)

    def _queue_match(self, item: "QueueItem", app: AppEntry) -> bool:
        """Does a queued item target `app`? With sources: only for the very same source."""
        target_pkgs = ({app.primary_pkg} | set(app.flake_refs)) - {None}
        if not target_pkgs & set(item.pkg_names):
            return False
        if self.backend and self._has_sources(app):
            return item.scope == self._source_queue_key(app)
        return True

    def _queued_state_label(self, app: AppEntry) -> str | None:
        for item in self.queue_items:
            if item.status in {"queued", "running"} and self._queue_match(item, app):
                return "Queued" if item.status == "queued" else "Running"
        return None

    def _run_action_for_app(self, app: AppEntry, preferred_action: str | None = None) -> None:
        if not self.backend or not app.primary_pkg:
            return
        state = self._queued_state_label(app)
        if state == "Running":
            self._show_toast(L(f"{app.primary_pkg} est en cours d'application.", f"{app.primary_pkg} is being applied right now."))
            return
        if state == "Queued":
            self.queue_items = [i for i in self.queue_items if not (i.status == "queued" and self._queue_match(i, app))]
            self._append_queue_log(L(f"{app.primary_pkg} retiré de la file", f"Removed {app.primary_pkg} from the queue"))
            self._invalidate_page_caches()
            self.status_label.set_text(self._queue_status_text())
            self._refresh_queue_page()
            self._refresh_main_page()
            if self.current_app is app:
                self._open_details(app, keep_source=True)
            return
        target = None
        if self._has_sources(app):
            remote, where = target = self._source_target(app)
            state = self._source_state(app, remote, where)
            if state == "external" and app.source == "nix":  # comes from the Roudix config / a profile: not ours to remove
                self._show_toast(L(
                    f"{app.primary_pkg} vient de la configuration Roudix, pas du store — retire-le de ta config pour le désinstaller.",
                    f"{app.primary_pkg} comes from the Roudix configuration, not from the store — remove it from your config to uninstall it.",
                ))
                return
            # a Flatpak installed by hand ("external") is removed directly with flatpak, no rebuild
            if preferred_action != "update":
                preferred_action = "remove" if state else "install"
        if preferred_action == "update":
            self._enqueue_update_batch([app])
            return
        action = preferred_action or ("remove" if app.installed else "install")
        scope = self._source_scope_key(app, *target) if target else "home"
        recorded = self.backend.source_pkg(app, target[0]) if target and app.source == "nix" else ""
        item = QueueItem(app=app, action=action, pkg_names=[recorded] if recorded and recorded != app.primary_pkg else [], message=L(f"{action_word(action, True)} de {app.primary_pkg} mise en file", f"Queued to {action} {app.primary_pkg}"), scope=scope)
        self.queue_items.append(item)
        self._append_queue_log(L(f"{action_word(action, True)} de {app.primary_pkg} mise en file — appuie sur Appliquer pour la lancer", f"Queued {action} for {app.primary_pkg} — press Apply to run it"))
        self._invalidate_page_caches()
        self.status_label.set_text(self._queue_status_text())
        self._refresh_queue_page()
        self._refresh_main_page()
        if self.current_app is app:
            self._open_details(app, keep_source=True)

    def _toggle_update_selection(self, app: AppEntry, selected: bool) -> None:
        pkg = app.primary_pkg
        if not pkg:
            return
        if selected:
            self.update_selection.add(pkg)
        else:
            self.update_selection.discard(pkg)
        self._refresh_updates_action_bar(self.current_items)

    def _clear_update_selection(self) -> None:
        self.update_selection.clear()
        self._refresh_updates_action_bar(self.current_items)
        self._refresh_main_page()

    def _refresh_updates_action_bar(self, items: list[AppEntry]) -> None:
        is_updates_page = self.current_group == "system" and self.current_page == "updates" and not self.current_search_text
        self.updates_action_bar.set_visible(is_updates_page)
        if not is_updates_page:
            return
        selectable = [app for app in items if app.primary_pkg]
        selected_count = sum(1 for app in selectable if app.primary_pkg in self.update_selection)
        self.updates_selected_label.set_text(L(f"{selected_count} sélectionné(s)", f"{selected_count} selected"))
        self.updates_clear_button.set_sensitive(selected_count > 0)
        self.update_selected_button.set_sensitive(selected_count > 0)
        self.update_all_button.set_sensitive(bool(selectable))

    def _queue_selected_updates(self) -> None:
        items = [app for app in self.current_items if app.primary_pkg and app.primary_pkg in self.update_selection]
        self._enqueue_update_batch(items)

    def _should_use_nobara_sync(self) -> bool:
        try:
            for raw in Path("/etc/os-release").read_text(encoding="utf-8", errors="replace").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key == "ID":
                    return value.strip().strip('"').strip("'").lower() == "nobara"
        except Exception:
            return False
        return False

    def _queue_system_update(self) -> None:
        update_flatpaks_check = getattr(self, "update_flatpaks_check", None)
        include_flatpaks = bool(update_flatpaks_check and update_flatpaks_check.get_active())

        # First, select all update items for visual feedback
        items = [app for app in self.current_items if app.primary_pkg]
        for app in items:
            if app.primary_pkg:
                self.update_selection.add(app.primary_pkg)
        self._refresh_updates_action_bar(self.current_items)
        self._refresh_main_page()

        if self._should_use_nobara_sync():
            if any(item.action == "system-update" and item.status in {"queued", "running"} for item in self.queue_items):
                self._show_toast(L("La mise à jour système est déjà dans la file.", "System update is already in the queue."))
                return
            base_app = self.current_items[0] if self.current_items else AppEntry(
                appstream_id="system-update",
                name=L("Mise à jour système", "System Update"),
                summary="",
                description="",
                pkg_names=[],
            )
            sync_args = ["--all"] if include_flatpaks else []
            label = L("Mise à jour système + Flatpaks", "System Update + Flatpaks") if include_flatpaks else L("Mise à jour système", "System Update")
            message = (L("Mise à jour système avec Flatpaks mise en file", "Queued system update with Flatpaks") if include_flatpaks else L("Mise à jour système mise en file", "Queued system update"))
            item = QueueItem(base_app, action="system-update", message=message, pkg_names=sync_args, label=label)
            self.queue_items.append(item)
            command_label = "nobara-sync cli --all" if include_flatpaks else "nobara-sync cli"
            self._append_queue_log(L(f"Mise à jour système mise en file via {command_label}", f"Queued system update via {command_label}"))
            self.status_label.set_text(self._queue_status_text())
            self._refresh_queue_page()
            self._refresh_main_page()
            self._refresh_detail_action_button()
            self._switch_page("system", "queue")
            if not self.queue_worker_running:
                self._start_queue_worker()
            return

        if not items:
            self._show_toast(L("Aucune mise à jour disponible.", "No updates are available."))
            return
        self._enqueue_update_batch(items)

    def _enqueue_update_batch(self, apps: list[AppEntry]) -> None:
        unique: list[AppEntry] = []
        seen: set[str] = set()
        for app in apps:
            pkg = app.primary_pkg
            if not pkg or pkg in seen:
                continue
            if self._queued_state_label(app) is not None:
                continue
            seen.add(pkg)
            unique.append(app)
        if not unique:
            return
        pkg_names = [app.primary_pkg for app in unique if app.primary_pkg]
        label = unique[0].name if len(unique) == 1 else L(f"{len(unique)} mises à jour", f"{len(unique)} updates")
        item = QueueItem(app=unique[0], action="update", message=L(f"Mise à jour de {len(pkg_names)} paquet(s) mise en file", f"Queued to update {len(pkg_names)} package(s)"), pkg_names=pkg_names, label=label)
        self.queue_items.append(item)
        names = ', '.join(pkg_names[:5]) + ('…' if len(pkg_names) > 5 else '')
        self._append_queue_log(L(f"Mise à jour mise en file pour {names}", f"Queued update for {names}"))
        for pkg in pkg_names:
            self.update_selection.discard(pkg)
        self.status_label.set_text(self._queue_status_text())
        self._invalidate_page_caches()
        self._refresh_queue_page()
        self._refresh_main_page()
        self._refresh_detail_action_button()
        if not self.queue_worker_running:
            self._start_queue_worker()

    def _apply_queue(self) -> None:
        """Run every queued change with a single local.nix write and a single rebuild."""
        if self.queue_worker_running or not self.backend:
            return
        if not any(i.status == "queued" for i in self.queue_items):
            return
        self._start_queue_worker()

    def _clear_pending_queue(self) -> None:
        if self.queue_worker_running:
            return
        self.queue_items = [i for i in self.queue_items if i.status != "queued"]
        self._append_queue_log(L("File d'attente vidée", "Cleared the pending queue"))
        self._invalidate_page_caches()
        self.status_label.set_text(self._queue_status_text())
        self._refresh_queue_page()
        self._refresh_main_page()
        self._refresh_detail_action_button()

    def _start_queue_worker(self) -> None:
        if self.queue_worker_running or not self.backend:
            return
        batch = [i for i in self.queue_items if i.status == "queued"]
        if not batch:
            return
        self.queue_worker_running = True

        def worker() -> None:
            for item in batch:
                GLib.idle_add(self._queue_item_started, item)
            changes = [(item.action, pkg, item.scope) for item in batch for pkg in (item.pkg_names or [item.pkg_name])]

            def on_event(payload: dict) -> None:
                GLib.idle_add(self._handle_batch_event, payload)

            ok, message = self.backend.apply_changes(changes, on_event)
            for item in batch:
                GLib.idle_add(self._queue_item_finished, item, ok, message)
            GLib.idle_add(self._queue_worker_done)

        threading.Thread(target=worker, daemon=True).start()

    def _handle_batch_event(self, payload: dict) -> bool:
        message = update_output.visible_text(str(payload.get("message") or ""))
        if message:
            self._append_queue_log(message)
            self.bottom_queue_status.set_text(message[:120])
        return False

    def _queue_item_started(self, item: QueueItem) -> bool:
        item.status = "running"
        subject = item.display_name if item.action in {"update", "system-update", 'install-rpms'} and (item.action in {'system-update', 'install-rpms'} or len(item.pkg_names) > 1) else item.pkg_name
        item.message = L(f"{action_word(item.action, True)} de {subject} en cours", f"Running {item.action} for {subject}")
        self.current_queue_item = item
        self._append_queue_log(L(f"Début : {action_word(item.action)} de {subject}", f"Starting {item.action} for {subject}"))
        self._invalidate_page_caches()
        self._refresh_queue_page()
        self._refresh_main_page()
        if self.current_app is item.app:
            self._open_details(item.app)
        return False

    def _handle_queue_event(self, item: QueueItem, payload: dict) -> bool:
        message = update_output.visible_text(str(payload.get("message") or ""))
        if payload.get("event") == "update-status" and item.action == "system-update":
            item.update_result = dict(payload)
            item.message = message
            self.update_banner.set_title(message)
            self.update_banner.set_revealed(payload.get("reboot_required") is True)
        elif message:
            item.message = message
            self._append_queue_log(f"{item.display_name}: {message}")
        self._refresh_queue_page()
        return False

    def _queue_item_finished(self, item: QueueItem, ok: bool, message: str) -> bool:
        message = update_output.visible_text(message) or (L("Opération terminée.", "Operation completed.") if ok else L("Échec de l'opération.", "Operation failed."))
        item.status = "done" if ok else "failed"
        item.message = message
        self._append_queue_log(f"{item.display_name}: {message}")
        if item.action == "system-update":
            # Refresh actual installed versions when the queue finishes:
            # this result may describe either live installation or staging.
            self._show_toast(message if ok else L(f"{item.display_name} : échec", f"{item.display_name} failed"))
            self._invalidate_page_caches()
            self._refresh_queue_page()
            self._refresh_visible_list()
            self._refresh_detail_action_button()
            return False
        if self.backend:
            if ok:
                # Update every in-memory representation of the acted-on package.
                related_apps: list[AppEntry] = []
                seen_ids: set[int] = set()

                acted_pkgs = set(item.pkg_names or [item.pkg_name])
                acted_pkgs |= {p.partition("#")[2] for p in list(acted_pkgs) if "#" in p}  # flake ref -> its attribute

                def _collect(candidate: AppEntry | None) -> None:
                    if candidate is None:
                        return
                    ident = id(candidate)
                    if ident in seen_ids:
                        return
                    candidate_pkgs = set(candidate.pkg_names or ([candidate.primary_pkg] if candidate.primary_pkg else []))
                    if candidate_pkgs & acted_pkgs:
                        related_apps.append(candidate)
                        seen_ids.add(ident)

                related_apps.append(item.app)  # the acted-on app, whatever name the flake gave its package
                seen_ids.add(id(item.app))
                _collect(self.current_app)
                for candidate in self.apps:
                    _collect(candidate)
                for candidate in getattr(self, 'current_items', []):
                    _collect(candidate)

                forced_installed = item.action in {"install", "update"}
                forced_installed_version = item.app.candidate_version if forced_installed else None
                for pkg in acted_pkgs:
                    self.update_selection.discard(pkg)

                # First flip the UI optimistically.
                for target in related_apps:
                    target.installed = forced_installed
                    target.installed_version = forced_installed_version if forced_installed else None
                if forced_installed and item.app not in self.apps:
                    self.apps.append(item.app)

                # Then refresh from backend state.
                try:
                    self.backend.refresh_apps(self.apps)
                except Exception:
                    self.backend.reload_state()
                    self.backend.enrich_apps(self.apps)

                for target in related_apps:
                    try:
                        self.backend.refresh_app(target)
                    except Exception:
                        pass

                # Finally, force the acted-on state once more so a slightly stale local
                # libdnf view cannot flip the button back to the old state immediately
                # after a successful transaction.
                for target in related_apps:
                    target.installed = forced_installed
                    if forced_installed:
                        if not target.installed_version:
                            target.installed_version = forced_installed_version or target.candidate_version
                    else:
                        target.installed_version = None
                if not forced_installed:  # still installed elsewhere (Roudix config, other scope)? keep it that way
                    still = getattr(self.backend, "still_installed", None)
                    for target in related_apps:
                        if still and still(target):
                            self.backend.refresh_app(target)
            else:
                self.backend.refresh_app(item.app)
        if ok:
            self._show_toast(message)
        else:
            self._show_toast(L(f"{item.display_name} : échec", f"{item.display_name} failed"))
        self._invalidate_page_caches()
        self._refresh_queue_page()
        self._refresh_visible_list()
        self._refresh_detail_action_button()
        if self.current_app is item.app:
            self._open_details(item.app)
        return False

    def _queue_worker_done(self) -> bool:
        self.queue_worker_running = False
        self.current_queue_item = None

        had_items = bool(self.queue_items)
        failed_items = [item for item in self.queue_items if item.status == "failed"]
        done_count = sum(1 for item in self.queue_items if item.status == "done")

        if had_items and done_count:
            self.queue_items = failed_items
            if failed_items:
                self._append_queue_log(L(
                    f"File terminée. {done_count} élément(s) terminé(s) retiré(s) ; {len(failed_items)} en échec restent.",
                    f"Queue finished. Cleared {done_count} completed item(s); {len(failed_items)} failed item(s) remain.",
                ))
            else:
                self._append_queue_log(L(f"File terminée. {done_count} élément(s) terminé(s) retiré(s).", f"Queue finished. Cleared {done_count} completed item(s)."))

        self.status_label.set_text(self._queue_status_text())
        self._refresh_queue_page()
        self._refresh_visible_list()
        self._refresh_detail_action_button()

        # Refresh updates after queue completes
        if had_items and done_count:
            self._load_async(force=True)

        return False

    def _on_close_request(self, *_args):
        try:
            if self.backend is not None:
                self.backend.shutdown()
        except Exception:
            pass
        return False

    def _queue_status_text(self) -> str:
        if not self.queue_items:
            return L("La file d'attente est vide.", "Queue is empty.")
        done = sum(1 for item in self.queue_items if item.status == "done")
        failed = sum(1 for item in self.queue_items if item.status == "failed")
        running = next((item for item in self.queue_items if item.status == "running"), None)
        queued = sum(1 for item in self.queue_items if item.status == "queued")
        if running is not None:
            target = running.display_name if running.action in {"update", "system-update"} and (running.action == "system-update" or len(running.pkg_names) > 1) else running.pkg_name
            return L(f"{action_word(running.action, True)} de {target} en cours. {done} terminé(s), {failed} en échec, {queued} en attente.", f"Running {running.action} for {target}. {done} done, {failed} failed, {queued} queued.")
        return L(f"{done} terminé(s), {failed} en échec, {queued} en attente.", f"{done} completed, {failed} failed, {queued} queued.")

    def _append_queue_log(self, line: str) -> None:
        line = update_output.visible_text(line)
        if not line:
            return
        if self.queue_log_full and self.queue_log_full[-1] == line:
            return
        self.queue_log_full.append(line)
        self.queue_logs.append(line)
        if len(self.queue_logs) > 400:
            self.queue_logs = self.queue_logs[-400:]
        if hasattr(self, "queue_log_view"):
            buffer = self.queue_log_view.get_buffer()
            end_iter = buffer.get_end_iter()
            prefix = "" if buffer.get_char_count() == 0 else "\n"
            buffer.insert(end_iter, prefix + line)
            if buffer.get_line_count() > 400:
                start = buffer.get_start_iter()
                end = buffer.get_iter_at_line(1)
                if isinstance(end, tuple):
                    _ok, end = end
                buffer.delete(start, end)
            GLib.idle_add(self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        if hasattr(self, "queue_log_view"):
            buffer = self.queue_log_view.get_buffer()
            end_iter = buffer.get_end_iter()
            self.queue_log_view.scroll_to_iter(end_iter, 0.0, False, 0.0, 1.0)
        return False

    def _refresh_visible_list(self) -> None:
        visible, scroll_before = self._get_scroll_position_for_visible_page()
        visible = visible or (self.stack.get_visible_child_name() if hasattr(self, "stack") else "list")
        items = self._filtered_apps_for_current_page()
        self.current_items = items
        self._rebuild_listbox(items)
        if visible != "details":
            self._refresh_main_page()
        else:
            if getattr(self, "current_app", None) is not None and self.current_app not in items and self.current_search_text:
                # keep details open for current search result even if not represented in AppStream list
                pass
            self._refresh_detail_action_button()
        GLib.idle_add(self._restore_scroll_position, visible, scroll_before)

    def _refresh_queue_page(self) -> None:
        if not hasattr(self, "queue_list_box"):
            return
        child = self.queue_list_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.queue_list_box.remove(child)
            child = next_child

        total = len(self.queue_items)
        done_count = sum(1 for item in self.queue_items if item.status == "done")
        failed_count = sum(1 for item in self.queue_items if item.status == "failed")
        resolved_count = done_count + failed_count
        fraction = (resolved_count / total) if total else 0.0
        if total:
            if failed_count and done_count == 0:
                progress_text = L(f"0/{total} terminé, {failed_count} en échec", f"0/{total} complete, {failed_count} failed")
            elif failed_count:
                progress_text = L(f"{done_count}/{total} terminé(s), {failed_count} en échec", f"{done_count}/{total} complete, {failed_count} failed")
            else:
                progress_text = L(f"{done_count}/{total} terminé(s)", f"{done_count}/{total} complete")
        else:
            progress_text = L("File vide", "Queue empty")
        self.queue_progress.set_fraction(fraction)
        self.queue_progress.set_show_text(True)
        self.queue_progress.set_text(progress_text)

        if self.queue_worker_running and total > resolved_count:
            self.queue_progress.pulse()

        if hasattr(self, "bottom_queue_revealer"):
            self.bottom_queue_revealer.set_reveal_child(total > 0)
            self.bottom_queue_progress.set_fraction(fraction)
            self.bottom_queue_progress.set_show_text(True)
            self.bottom_queue_progress.set_text(progress_text)
            if self.queue_worker_running and total > resolved_count:
                self.bottom_queue_progress.pulse()
            self.bottom_queue_status.set_text(self._queue_status_text())

        pending = sum(1 for i in self.queue_items if i.status == "queued")
        can_apply = pending > 0 and not self.queue_worker_running
        apply_label = L("Appliquer", "Apply") + (f" ({pending})" if pending else "")
        for name in ("bottom_apply_button", "queue_apply_button"):
            btn = getattr(self, name, None)
            if btn is not None:
                btn.set_label(apply_label)
                btn.set_sensitive(can_apply)
        for name in ("bottom_clear_button", "queue_clear_button"):
            btn = getattr(self, name, None)
            if btn is not None:
                btn.set_sensitive(can_apply)

        if not self.queue_items:
            empty = Gtk.Label(label=L("Aucune action de paquet en attente.", "No queued package actions yet."), xalign=0)
            empty.add_css_class("dim-label")
            self.queue_list_box.append(empty)

        for item in self.queue_items:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.add_css_class("queue-item-card")
            title = Gtk.Label(xalign=0)
            where = {"home": L("utilisateur", "user"), "system": L("système", "system"),
                     "flatpak": "Flatpak " + L("système", "system"), "flatpak-beta": "Flatpak Beta " + L("système", "system"),
                     "flatpak-user": "Flatpak " + L("utilisateur", "user"), "flatpak-user-beta": "Flatpak Beta " + L("utilisateur", "user"),
                     "home-flake": "Flake " + L("utilisateur", "user"), "system-flake": "Flake " + L("système", "system")}.get(item.scope, item.scope)
            title.set_markup(f"<b>{GLib.markup_escape_text(item.display_name)}</b> — {GLib.markup_escape_text(action_word(item.action))} ({GLib.markup_escape_text(where)}) · {GLib.markup_escape_text(status_word(item.status))}")
            card.append(title)
            self.queue_list_box.append(card)

    def _get_queue_log_text(self) -> str:
        if getattr(self, "queue_log_full", None):
            return "\n".join(self.queue_log_full)
        buffer = self.queue_log_view.get_buffer()
        start = buffer.get_start_iter()
        end = buffer.get_end_iter()
        return buffer.get_text(start, end, False)

    def _show_text_popup(self, title: str, text: str) -> None:
        window = Gtk.Window(title=title, transient_for=self, modal=True)
        window.set_default_size(900, 600)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        outer.set_margin_top(12)
        outer.set_margin_bottom(12)
        outer.set_margin_start(12)
        outer.set_margin_end(12)

        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_cursor_visible(False)
        text_view.set_monospace(True)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        text_view.get_buffer().set_text(text)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        scroll.set_child(text_view)
        outer.append(scroll)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        buttons.set_halign(Gtk.Align.END)
        close_btn = Gtk.Button(label=L("Fermer", "Close"))
        close_btn.connect("clicked", lambda *_: window.close())
        buttons.append(close_btn)
        outer.append(buttons)

        window.set_child(outer)
        window.present()

    def _show_info_popup(self, title: str, text: str) -> None:
        window = Gtk.Window(title=title, transient_for=self, modal=True)
        window.set_default_size(560, 160)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_margin_top(12)
        outer.set_margin_bottom(12)
        outer.set_margin_start(12)
        outer.set_margin_end(12)

        label = Gtk.Label(xalign=0)
        label.set_wrap(True)
        label.set_selectable(True)
        label.set_text(text)
        outer.append(label)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        buttons.set_halign(Gtk.Align.END)
        copy_btn = Gtk.Button(label=L("Copier", "Copy"))
        def _copy(*_args):
            display = Gdk.Display.get_default()
            if display is not None:
                clipboard = display.get_clipboard()
                clipboard.set(text)
                self._show_toast(L("Copié dans le presse-papiers", "Copied to clipboard"))
        copy_btn.connect("clicked", _copy)
        buttons.append(copy_btn)
        close_btn = Gtk.Button(label=L("Fermer", "Close"))
        close_btn.connect("clicked", lambda *_: window.close())
        buttons.append(close_btn)
        outer.append(buttons)

        window.set_child(outer)
        window.present()

    def _on_view_transaction_log(self, _button: Gtk.Button) -> None:
        text = self._get_queue_log_text().strip()
        if not text:
            self._show_toast(L("Pas encore de journal de transactions.", "No transaction log available yet."))
            return
        self._show_text_popup(L("Journal des transactions", "Transaction log"), text)

    def _on_send_to_pastebin(self, _button: Gtk.Button) -> None:
        text = self._get_queue_log_text().strip()
        if not text:
            self._show_toast(L("Pas encore de journal de transactions.", "No transaction log available yet."))
            return

        self.send_paste_button.set_sensitive(False)

        def worker() -> None:
            try:
                result = subprocess.run(["pbcli"], input=text, text=True, capture_output=True, check=False)
                stdout = (result.stdout or "").strip()
                stderr = (result.stderr or "").strip()
                if result.returncode != 0 or not stdout:
                    message = stderr or stdout or L("pbcli n'a pas renvoyé d'URL.", "pbcli did not return a URL.")
                    GLib.idle_add(self._pastebin_done, False, message)
                    return
                url = stdout.splitlines()[-1].strip()
                GLib.idle_add(self._pastebin_done, True, url)
            except FileNotFoundError:
                GLib.idle_add(self._pastebin_done, False, L("pbcli est introuvable sur ce système.", "pbcli was not found on this system."))
            except Exception as exc:
                GLib.idle_add(self._pastebin_done, False, str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _pastebin_done(self, ok: bool, message: str) -> bool:
        self.send_paste_button.set_sensitive(True)
        if ok:
            self._show_info_popup(L("URL du pastebin", "Pastebin URL"), message)
        else:
            self._show_info_popup(L("Échec de l'envoi sur le pastebin", "Pastebin upload failed"), message)
        return False

    def _on_open_clicked(self, _button: Gtk.Button) -> None:
        if not self.current_app:
            return
        ok, message = launcher.launch(self.current_app.launchables, self.get_display().get_app_launch_context())
        if not ok:
            self._show_toast(message)

    def _show_toast(self, message: str) -> None:
        self.toast_overlay.add_toast(Adw.Toast(title=message[:300]))

    def _prompt_install(self) -> bool:
        if not self.queue_items or self.queue_worker_running:
            return False

        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=L("Confirmer l'installation", "Confirm Installation"),
            body=L(f"{len(self.queue_items)} paquet(s) prêt(s). Veux-tu les installer ?", f"You have {len(self.queue_items)} package(s) ready. Do you want to install them?"),
        )

        dialog.add_response("cancel", L("Annuler", "Cancel"))
        dialog.add_response("install", L("Installer", "Install"))

        try:
            dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        except AttributeError:
            pass

        def on_response(dlg, response):
            if response == "install":
                self._start_queue_worker()
            else:
                self.queue_items.clear()
                self._refresh_queue_page()

        dialog.connect("response", on_response)
        dialog.present()

        return False
