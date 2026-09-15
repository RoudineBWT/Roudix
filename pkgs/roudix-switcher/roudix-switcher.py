#!/usr/bin/env python3
import gi
import os
import re
import subprocess
import sys
import logging

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Pango

CONFIG_FILE = os.path.expanduser("~/.config/roudix/hosts/roudix/local.nix")
NH_FLAKE    = os.path.expanduser("~/.config/roudix")

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR   = os.path.join(SCRIPT_DIR, "../share/roudix-switcher/icons")

LOG_DIR     = os.path.expanduser("~/.local/share/roudix-switcher")
LOG_FILE    = os.path.join(LOG_DIR, "switcher.log")
TMP_LOG     = "/tmp/roudix-switcher.log"

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

ENVIRONMENTS = [
    {
        "id":       "niri",
        "name":     "Niri",
        "subtitle": "Scrollable tiling Wayland compositor",
        "icon":     "niri.svg",
    },
    {
        "id":       "hyprland",
        "name":     "Hyprland",
        "subtitle": "Dynamic tiling Wayland compositor",
        "icon":     "hyprland.svg",
    },
    {
        "id":       "gnome",
        "name":     "GNOME",
        "subtitle": "GNOME — modern and user-friendly desktop",
        "icon":     "gnome.svg",
    },
    {
        "id":       "kde",
        "name":     "KDE Plasma",
        "subtitle": "KDE Plasma — Highly customizable and feature-rich desktop environment",
        "icon":     "kde.svg",
    },
    {
        "id":       "mangowc",
        "name":     "MangoWC",
        "subtitle": "Lightweight dynamic tiling Wayland compositor",
        "icon":     "mangowc.svg",
    },

     {
         "id":       "umbriel",
         "name":     "Umbriel",
         "subtitle": "a Wayland compositor designed for daily use, with scrolling, dwindle, and master layouts, per-output workspaces, window rules, blur, shadows, and fluid animations.",
         "icon":     "umbriel.svg",
     },
]

# Shells graphiques — disponibles uniquement pour niri et hyprland
SHELLS = [
    {
        "id":       "noctalia",
        "name":     "Noctalia",
        "subtitle": "Roudix default shell — sleek and feature-complete",
        "icon":     "noctalia.svg",
    },
    {
        "id":       "dms",
        "name":     "DMS",
        "subtitle": "Minimal and lightweight Roudix shell",
        "icon":     "dms.svg",
    },
]

CAELESTIA = [
    {
        "id":       "caelestia",
        "name":     "Caelestia",
        "subtitle": "Elegant Roudix shell with a focus on aesthetics",
        "icon":     "caelestia.svg",
    },
]

UMBRIEL = [
    {
        "id":       "noctalia",
        "name":     "Noctalia",
        "subtitle": "Roudix default shell — sleek and feature-complete",
        "icon":     "noctalia.svg",
    },

]

# Compositeurs qui supportent le choix de shell graphique
SHELL_SUPPORTED_DE    = {"niri", "hyprland", "mangowc", "umbriel"}
CAELESTIA_SUPPORTED_DE = {"hyprland"}
UMBRIEL_SUPPORTED_DE = {"umbriel"}

# ── Tweaks: éditeur, keyring/portal, apps gaming ───────────────────────────
# Ces trois catégories suivent le même principe que DE/shell : une valeur
# choisie parmi plusieurs (enum, écrit comme string dans local.nix) ou un
# ensemble de booléens indépendants. Voir roudix.editor,
# roudix.desktopIntegration et roudix.gaming.apps.* côté Nix.

EDITORS = [
    {"id": "zed",    "name": "Zed",     "subtitle": "Fast GPU-accelerated editor (Roudix default)", "icon": "zed.svg"},
    {"id": "vscode", "name": "VS Code", "subtitle": "Microsoft's editor, huge extension ecosystem",  "icon": "vscode.svg"},
    {"id": "neovim", "name": "Neovim",  "subtitle": "Terminal-based, keyboard-driven",                "icon": "neovim.svg"},
    {"id": "none",   "name": "None",    "subtitle": "Don't install a default editor",                 "icon": "none.svg"},
]

DESKTOP_INTEGRATIONS = [
    {
        "id": "gnome",
        "name": "GNOME",
        "subtitle": "gnome-keyring + xdg-desktop-portal-gtk/-gnome (default)",
        "icon": "gnome.svg",
    },
    {
        "id": "kde",
        "name": "KDE",
        "subtitle": "KWallet + xdg-desktop-portal-kde",
        "icon": "kde.svg",
    },
]
# Seuls les compositeurs "bruts" respectent ce choix — gnome/kde gardent
# toujours leur propre stack native.
DESKTOP_INTEGRATION_SUPPORTED_DE = {"niri", "hyprland", "mangowc", "umbriel"}

# name -> option Nix (roudix.gaming.apps.<id>.enable), toutes true par défaut
GAMING_APPS = [
    {"id": "lutris",        "name": "Lutris",         "key": "roudix.gaming.apps.lutris.enable"},
    {"id": "heroic",        "name": "Heroic",         "key": "roudix.gaming.apps.heroic.enable"},
    {"id": "faugus",        "name": "Faugus Launcher","key": "roudix.gaming.apps.faugus.enable"},
    {"id": "prismlauncher", "name": "Prism Launcher", "key": "roudix.gaming.apps.prismlauncher.enable"},
    {"id": "vintagestory",  "name": "Vintage Story",  "key": "roudix.gaming.apps.vintagestory.enable"},
    {"id": "mangohud",      "name": "MangoHud",       "key": "roudix.gaming.apps.mangohud.enable"},
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


def get_bool_option(key: str, default: bool) -> bool:
    """Read a `key = true;`/`key = false;` line (roudix.gaming.apps.*.enable...)."""
    try:
        with open(CONFIG_FILE) as f:
            for line in f:
                if key in line:
                    m = re.search(re.escape(key) + r"\s*=\s*(true|false)", line)
                    if m:
                        return m.group(1) == "true"
    except Exception:
        pass
    return default


def set_bool_option(key: str, value: bool):
    try:
        with open(CONFIG_FILE) as f:
            content = f.read()
        val = "true" if value else "false"
        pattern = re.escape(key) + r"\s*=\s*(true|false)"
        if re.search(pattern, content):
            new = re.sub(pattern, f"{key} = {val}", content)
        else:
            new = _insert_before_closing_brace(content, f"{key} = {val};")
        with open(CONFIG_FILE, "w") as f:
            f.write(new)
        log.info("Configuration updated: %s set to %s.", key, val)
        return True
    except Exception as e:
        log.error("Failed to write configuration: %s", e)
        return str(e)


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


def load_icon(icon_filename, dark):
    """Load icon from dark/ or light/ subfolder, fallback to theme icon."""
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

        icon = load_icon(item["icon"], self._dark)
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

        # Retirer les lignes qui ne doivent plus apparaître
        for existing_id in list(self._row_widgets.keys()):
            if existing_id not in wanted_ids:
                self.remove_item(existing_id)

        # Ajouter les lignes manquantes
        for item in items:
            if item["id"] not in self._row_widgets:
                self.add_item(item)

        # Sécurité : si la sélection actuelle n'est plus valide
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


# ── Main window ───────────────────────────────────────────────────────────────

class RoudixSwitcherWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Roudix — Customizer")
        self.set_default_size(760, 640)
        self.set_resizable(True)

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
        header.set_show_end_title_buttons(False)
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
            "<b>Customize your Roudix</b>\n"
            "<span size='small'>Pick your desktop, shell and tweaks below.\n"
            "The system will rebuild after your selection — this may take a few minutes.</span>"
        )
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_wrap(True)
        main_box.append(desc)

        # ── Sidebar (categories) + content pages ────────────────────────────
        # Layout inspiré d'un panneau de préférences façon "GLF Customizer" :
        # une liste de catégories à gauche, le détail de la catégorie choisie
        # à droite. Chaque page reste fidèle à la forme réelle de l'option
        # Nix sous-jacente (liste à choix unique pour un enum, switches
        # indépendants pour un ensemble de booléens) plutôt que de forcer
        # tout en cases à cocher.
        split_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        split_row.set_vexpand(True)

        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar_box.set_size_request(190, -1)

        self.category_list = Gtk.ListBox()
        self.category_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.category_list.add_css_class("navigation-sidebar")
        self.category_list.set_vexpand(True)

        CATEGORIES = [
            ("desktop",     "Desktop"),
            ("gaming",      "Gaming"),
            ("editor",      "Editor"),
            ("integration", "Integration"),
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

        # Seule "Gaming" a une vraie notion de "N/M activés" (des paquets
        # qu'on installe ou pas) — les autres catégories sont des choix
        # exclusifs sans équivalent honnête à ce compteur.
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
        self.content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        content_scroll = Gtk.ScrolledWindow()
        content_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content_scroll.set_hexpand(True)
        content_scroll.set_vexpand(True)
        content_scroll.set_child(self.content_stack)
        split_row.append(content_scroll)

        main_box.append(split_row)

        # ── "Desktop" page: DE + shell ───────────────────────────────────
        desktop_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        desktop_page.set_margin_top(4)
        desktop_page.set_margin_start(16)
        desktop_page.set_margin_end(16)
        desktop_page.set_margin_bottom(16)

        self.de_selector = SelectorGroup(
            "Desktop environment",
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
            "Graphical shell",
            initial_shells,
            current_shell,
            dark,
        )
        self.shell_selector.set_visible(current_de in SHELL_SUPPORTED_DE)
        desktop_page.append(self.shell_selector)

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
            label="Launchers and tools installed for gaming.",
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

        gaming_current = {app["id"]: get_bool_option(app["key"], True) for app in GAMING_APPS}
        self.gaming_apps_group = ToggleListGroup("", GAMING_APPS, gaming_current)
        self.gaming_apps_group.set_sensitive(cur_gaming_master)
        gaming_page.append(self.gaming_apps_group)

        self.gaming_master_switch.connect("notify::active", self._on_gaming_master_toggled)
        for sw in self.gaming_apps_group.switches.values():
            sw.connect("notify::active", lambda *_: self._update_gaming_counter())

        self.content_stack.add_named(gaming_page, "gaming")

        # ── "Editor" page ──────────────────────────────────────────────────
        editor_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        editor_page.set_margin_top(4)
        editor_page.set_margin_start(16)
        editor_page.set_margin_end(16)
        editor_page.set_margin_bottom(16)

        current_editor = get_string_option("roudix.editor", "zed")
        self.editor_selector = SelectorGroup("Default editor", EDITORS, current_editor, dark)
        editor_page.append(self.editor_selector)

        self.content_stack.add_named(editor_page, "editor")

        # ── "Integration" page: keyring/portal backend ─────────────────────
        integration_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        integration_page.set_margin_top(4)
        integration_page.set_margin_start(16)
        integration_page.set_margin_end(16)
        integration_page.set_margin_bottom(16)

        current_integration = get_string_option("roudix.desktopIntegration", "gnome")
        self.integration_selector = SelectorGroup(
            "Keyring & portal backend",
            DESKTOP_INTEGRATIONS,
            current_integration,
            dark,
        )
        integration_page.append(self.integration_selector)

        integration_note = Gtk.Label(
            label="Only applies to niri, Hyprland, MangoWC and Umbriel — "
                  "GNOME and KDE always keep their own native stack.",
        )
        integration_note.add_css_class("dim-label")
        integration_note.set_wrap(True)
        integration_note.set_halign(Gtk.Align.START)
        integration_page.append(integration_note)

        self.content_stack.add_named(integration_page, "integration")

        self.content_stack.set_visible_child_name("desktop")
        self.category_list.select_row(self._category_rows["desktop"])
        self.category_list.connect("row-selected", self._on_category_selected)

        self._update_gaming_counter()
        self._update_integration_visibility(current_de)

        # ── Integrated terminal ───────────────────────────────────────────
        term_frame = Gtk.Frame()
        term_frame.add_css_class("card")

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

        self.exit_btn = Gtk.Button(label="Exit")
        self.exit_btn.connect("clicked", lambda _: self.close())
        btn_box.append(self.exit_btn)

        self.apply_btn = Gtk.Button(label="Apply & Rebuild")
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

    def _on_gaming_master_toggled(self, sw, _param):
        active = sw.get_active()
        self.gaming_apps_group.set_sensitive(active)
        self._update_gaming_counter()

    def _update_gaming_counter(self):
        if not self.gaming_master_switch.get_active():
            self.gaming_counter_label.set_label("Gaming disabled")
            return
        states = self.gaming_apps_group.get_states()
        enabled = sum(1 for v in states.values() if v)
        self.gaming_counter_label.set_label(f"{enabled}/{len(states)} gaming apps enabled")

    def _update_integration_visibility(self, de_id: str):
        """Cache la page Integration pour gnome/kde (sans effet dessus) et
        retombe sur Desktop si elle était sélectionnée."""
        supported = de_id in DESKTOP_INTEGRATION_SUPPORTED_DE
        row = self._category_rows["integration"]
        row.set_visible(supported)
        if not supported and self.category_list.get_selected_row() is row:
            self.category_list.select_row(self._category_rows["desktop"])

    def _on_de_toggled(self, check, *_):
        """Affiche/cache le shell selector et met à jour la liste selon le DE choisi."""
        new_de  = self.de_selector.selected_id
        visible = new_de in SHELL_SUPPORTED_DE
        self.shell_selector.set_visible(visible)
        self._update_integration_visibility(new_de)

        if not visible:
            return

        # Réconcilie la liste des shells affichés avec celle attendue pour ce DE
        # (ex: bascule vers Umbriel → uniquement Noctalia; retour vers Hyprland
        # → Noctalia/DMS + Caelestia, etc.)
        self.shell_selector.sync_items(shells_for_de(new_de))

        log.debug(
            "DE changed to '%s' — shell selector mis à jour (shells: %s)",
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

    # ── Apply logic ───────────────────────────────────────────────────────

    def on_apply(self, btn):
        new_de    = self.de_selector.selected_id
        cur_de    = get_current_de()
        cur_shell = get_current_shell()

        de_changed = new_de != cur_de

        # Le shell n'est pertinent que pour niri/hyprland/mangowc/umbriel
        shell_relevant = new_de in SHELL_SUPPORTED_DE
        new_shell      = self.shell_selector.selected_id if shell_relevant else cur_shell
        shell_changed  = shell_relevant and (new_shell != cur_shell)

        # Keyring/portal — pertinent uniquement pour les compositeurs bruts
        integration_relevant = new_de in DESKTOP_INTEGRATION_SUPPORTED_DE
        cur_integration = get_string_option("roudix.desktopIntegration", "gnome")
        new_integration = self.integration_selector.selected_id if integration_relevant else cur_integration
        integration_changed = integration_relevant and (new_integration != cur_integration)

        # Éditeur par défaut
        cur_editor = get_string_option("roudix.editor", "zed")
        new_editor = self.editor_selector.selected_id
        editor_changed = new_editor != cur_editor

        # Apps gaming : booléens indépendants, on ne touche que celles qui ont changé
        gaming_states = self.gaming_apps_group.get_states()
        gaming_changes = {}
        for app in GAMING_APPS:
            cur_val = get_bool_option(app["key"], True)
            new_val = gaming_states[app["id"]]
            if new_val != cur_val:
                gaming_changes[app["id"]] = (app["key"], new_val, app["name"])

        # Interrupteur maître du groupe gaming
        cur_gaming_master = get_bool_option("roudix.gaming.enable", True)
        new_gaming_master = self.gaming_master_switch.get_active()
        gaming_master_changed = new_gaming_master != cur_gaming_master

        if not any([de_changed, shell_changed, integration_changed, editor_changed,
                    gaming_changes, gaming_master_changed]):
            log.info("No changes detected — nothing to do.")
            self.status.set_markup(
                "<span color='gray'>No changes detected — nothing to do.</span>"
            )
            return

        # Build a human-readable summary of what will change
        changes = []
        if de_changed:
            changes.append(f"Desktop: <b>{cur_de}</b> → <b>{new_de}</b>")
        if shell_changed:
            changes.append(f"Shell: <b>{cur_shell}</b> → <b>{new_shell}</b>")
        if integration_changed:
            changes.append(f"Keyring/portal: <b>{cur_integration}</b> → <b>{new_integration}</b>")
        if editor_changed:
            changes.append(f"Editor: <b>{cur_editor}</b> → <b>{new_editor}</b>")
        if gaming_master_changed:
            changes.append(f"Gaming: <b>{'enabled' if new_gaming_master else 'disabled'}</b>")
        for _key, new_val, name in gaming_changes.values():
            changes.append(f"{name}: <b>{'enabled' if new_val else 'disabled'}</b>")
        body_changes = "\n".join(changes)

        pending = {
            "de_changed": de_changed, "new_de": new_de,
            "shell_changed": shell_changed, "new_shell": new_shell,
            "integration_changed": integration_changed, "new_integration": new_integration,
            "editor_changed": editor_changed, "new_editor": new_editor,
            "gaming_master_changed": gaming_master_changed, "new_gaming_master": new_gaming_master,
            "gaming_changes": gaming_changes,
        }

        dialog = Adw.AlertDialog()
        dialog.set_heading("Apply changes?")
        dialog.set_body(
            f"{body_changes}\n\n"
            "Your NixOS configuration will be rebuilt. This may take a few minutes."
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("confirm", "Apply & Rebuild")
        dialog.set_response_appearance("confirm", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("confirm")
        dialog.connect("response", self.on_confirm_response, pending)
        dialog.present(self)

    def on_confirm_response(self, dialog, response, pending):
        if response != "confirm":
            log.info("User cancelled the rebuild dialog.")
            return

        if pending["de_changed"]:
            result = set_de(pending["new_de"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing DE config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if pending["shell_changed"]:
            result = set_shell(pending["new_shell"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing shell config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if pending["integration_changed"]:
            result = set_string_option("roudix.desktopIntegration", pending["new_integration"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing keyring/portal config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if pending["editor_changed"]:
            result = set_string_option("roudix.editor", pending["new_editor"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing editor config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if pending["gaming_master_changed"]:
            result = set_bool_option("roudix.gaming.enable", pending["new_gaming_master"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing gaming config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        for key, new_val, name in pending["gaming_changes"].values():
            result = set_bool_option(key, new_val)
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing {name} config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        self.status.set_markup("")
        GLib.idle_add(self._term_clear)
        GLib.idle_add(self._term_append, "=" * 50, "section")
        GLib.idle_add(self._term_append, "Important Notices:", "section")
        GLib.idle_add(self._term_append, "=" * 50, "section")
        GLib.idle_add(self._term_append, "No issues currently reported.", "info")
        GLib.idle_add(self._term_append, "", "dim")
        GLib.idle_add(self._term_append, "=" * 50, "section")
        GLib.idle_add(self._start_progress)
        self.apply_btn.set_sensitive(False)
        self.exit_btn.set_sensitive(False)

        log.info(
            "Starting NixOS rebuild — DE: %s, shell: %s",
            new_de if de_changed else "(unchanged)",
            new_shell if shell_changed else "(unchanged)",
        )

        import threading
        threading.Thread(target=self.run_rebuild, daemon=True).start()

    def run_rebuild(self):
        try:
            cmd_str = f"Running: nh os boot --elevation-strategy pkexec --accept-flake-config {NH_FLAKE}"
            log.info(cmd_str)
            GLib.idle_add(self._term_append, cmd_str, "dim")
            GLib.idle_add(self._term_append, "Checking repositories...", "dim")

            proc = subprocess.Popen(
                [
                    "nh", "os", "boot",
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
            GLib.idle_add(self._term_append, "✓ Rebuild completed successfully. Reboot to apply changes.", "ok")
            GLib.idle_add(self._stop_progress)
            GLib.idle_add(
                self.status.set_markup,
                "<span color='green'>✓ Done! Reboot to apply changes.</span>",
            )

        except subprocess.CalledProcessError as e:
            log.error("Rebuild failed (exit code %d).", e.returncode)
            GLib.idle_add(self._term_append, "", "dim")
            GLib.idle_add(self._term_append, f"✗ Rebuild failed (exit code {e.returncode}).", "error")
            GLib.idle_add(self._stop_progress)
            GLib.idle_add(
                self.status.set_markup,
                "<span color='red'>✗ Rebuild failed. Check <tt>~/.local/share/roudix-switcher/switcher.log</tt> for details.</span>",
            )
        except Exception as e:
            log.exception("Unexpected error during rebuild.")
            GLib.idle_add(self._term_append, "", "dim")
            GLib.idle_add(self._term_append, f"✗ Unexpected error: {e}", "error")
            GLib.idle_add(self._stop_progress)
            GLib.idle_add(
                self.status.set_markup,
                f"<span color='red'>✗ Unexpected error: {GLib.markup_escape_text(str(e))}</span>",
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
