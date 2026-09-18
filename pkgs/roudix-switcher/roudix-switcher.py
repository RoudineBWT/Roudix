#!/usr/bin/env python3
import gi
import os
import re
import subprocess
import sys
import logging

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Pango, Gdk

CONFIG_FILE = os.path.expanduser("~/.config/roudix/hosts/roudix/local.nix")
# roudix.fastfetch.useNix (et toute future option Home Manager) ne vit pas
# dans le config système — elle doit être écrite ici, sous peine de
# "The option `roudix.fastfetch' does not exist" au rebuild.
HOME_CONFIG_FILE = os.path.expanduser("~/.config/roudix/modules/home/local.nix")
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
    {"id": "lutris",        "name": "Lutris",         "key": "roudix.gaming.apps.lutris.enable",        "default": True},
    {"id": "heroic",        "name": "Heroic",         "key": "roudix.gaming.apps.heroic.enable",        "default": True},
    {"id": "faugus",        "name": "Faugus Launcher","key": "roudix.gaming.apps.faugus.enable",        "default": True},
    {"id": "prismlauncher", "name": "Prism Launcher", "key": "roudix.gaming.apps.prismlauncher.enable", "default": True},
    {"id": "vintagestory",  "name": "Vintage Story",  "key": "roudix.gaming.apps.vintagestory.enable",  "default": True},
    {"id": "mangohud",      "name": "MangoHud",       "key": "roudix.gaming.apps.mangohud.enable",      "default": True},
]

TERMINALS = [
    {"id": "ghostty",   "name": "Ghostty",   "subtitle": "GPU-accelerated, Roudix default", "icon": "ghostty.svg"},
    {"id": "kitty",     "name": "Kitty",     "subtitle": "GPU-accelerated, feature-rich",     "icon": "kitty.svg"},
    {"id": "alacritty", "name": "Alacritty", "subtitle": "Minimal, GPU-accelerated",          "icon": "alacritty.svg"},
    {"id": "foot",      "name": "Foot",      "subtitle": "Lightweight, Wayland-native",       "icon": "foot.svg"},
    {"id": "wezterm",   "name": "WezTerm",   "subtitle": "Cross-platform, Lua-configurable",  "icon": "wezterm.svg"},
    {"id": "ptyxis",    "name": "Ptyxis",    "subtitle": "GNOME's container-aware terminal",  "icon": "ptyxis.svg"},
    {"id": "konsole",   "name": "Konsole",   "subtitle": "KDE's terminal emulator",           "icon": "konsole.svg"},
]

# roudix.browsers est une LISTE (pas un enum) : plusieurs navigateurs peuvent
# être installés en même temps. On l'expose donc en checklist, pas en
# sélecteur exclusif. Le premier coché de cette liste devient le défaut
# (raccourci niri MOD+B) — c'est exactement la logique déjà utilisée côté
# Nix (roudix.browser.default = lib.head cfg.browsers).
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

# roudix.shell : le shell de LOGIN (fish/bash) — à ne pas confondre avec le
# "shell" graphique (noctalia/dms/caelestia) de la page Desktop.
LOGIN_SHELLS = [
    {"id": "fish", "name": "fish", "subtitle": "Shell interactif convivial (défaut Roudix)", "icon": "fish.svg"},
    {"id": "bash", "name": "bash", "subtitle": "Le shell POSIX classique",                    "icon": "bash.svg"},
]

FILE_MANAGERS = [
    {"id": "nautilus",   "name": "Nautilus (Files)", "subtitle": "Gestionnaire de fichiers de GNOME",   "icon": "nautilus.svg"},
    {"id": "dolphin",    "name": "Dolphin",           "subtitle": "Gestionnaire de fichiers de KDE",     "icon": "dolphin.svg"},
    {"id": "nemo",       "name": "Nemo",              "subtitle": "Gestionnaire de fichiers de Cinnamon","icon": "nemo.svg"},
    {"id": "thunar",     "name": "Thunar",            "subtitle": "Léger, celui de XFCE",                "icon": "thunar.svg"},
    {"id": "pcmanfm-qt", "name": "PCManFM-Qt",        "subtitle": "Léger, en Qt",                        "icon": "pcmanfm-qt.svg"},
]
# Comme Integration : sans effet sur gnome/kde, qui gardent leur gestionnaire natif.
FILE_MANAGER_SUPPORTED_DE = {"niri", "hyprland", "mangowc", "umbriel"}

MATRIX_CLIENTS = [
    {"id": "element", "name": "Element", "subtitle": "Client Matrix complet (défaut)",      "icon": "element.svg"},
    {"id": "cinny",   "name": "Cinny",   "subtitle": "Client Matrix léger",                 "icon": "cinny.svg"},
    {"id": "none",    "name": "None",    "subtitle": "N'installer aucun client Matrix",     "icon": "none.svg"},
]

DISCORD_OPTIONS = [
    {"id": "vencord", "name": "Vencord", "subtitle": "Discord avec Vencord déjà patché (défaut)", "icon": "vencord.svg"},
    {"id": "vanilla", "name": "Vanilla", "subtitle": "Discord sans aucun patch client",            "icon": "discord.svg"},
    {"id": "none",    "name": "None",    "subtitle": "N'installer aucun client Discord",           "icon": "none.svg"},
]

RGB_BACKENDS = [
    {"id": "openlinkhub", "name": "OpenLinkHub", "subtitle": "Pour périphériques compatibles Corsair iCUE", "icon": "openlinkhub.svg"},
    {"id": "openrgb",     "name": "OpenRGB",      "subtitle": "Support RGB multi-marques",                   "icon": "openrgb.svg"},
    {"id": "none",        "name": "None",         "subtitle": "Aucun backend RGB",                           "icon": "none.svg"},
]

# TODO: remplir avec les IDs des mods Zen que tu utilises réellement (store
# natif https://zen-browser.app/mods ou Sine — même liste d'IDs dans les
# deux cas, seule la cible Nix change selon roudix.zen.sine.enable). Une
# fois remplie, chaque mod devient toggleable comme les navigateurs.
# Exemple : {"id": "zen-internet", "name": "Zen Internet"},
ZEN_MODS = [
    # Confirmé (chrome/sine-mods/) : dossier UUID = celui du theme-store officiel
    {"id": "ad97bb70-0066-4e42-9b5f-173a5e42c6fc", "name": "SuperPins"},
    # Confirmés directement via le listing de chrome/sine-mods/ — ce sont
    # littéralement les noms de dossiers, pas des UUID.
    {"id": "Arc-2.0", "name": "Arc 2.0"},
    {"id": "context-menu-icons", "name": "Context Menu Icons"},
    {"id": "floating-statusbar", "name": "Floating Statusbar"},
    {"id": "unloaded-tabs", "name": "Unloaded Tabs"},
    {"id": "new-icons", "name": "New Icons"},
    {"id": "Nebula", "name": "Nebula"},
    # Confirmés (tu as identifié lequel est lequel depuis chrome/sine-mods/)
    {"id": "3c8ebf69-1042-49b1-8f08-9178f9490659", "name": "Better Music Bar"},
    {"id": "jvynuz3kn-hjd9pvfmg-vonasfop9", "name": "zen-container-halo"},
]

# Tweaks gaming annexes (à côté des launchers) — mêmes clés booléennes que
# GAMING_APPS mais affichés dans un groupe séparé sur la page Gaming.
GAMING_EXTRAS = [
    {"id": "ananicy", "name": "Ananicy (ordonnanceur process)", "key": "roudix.gaming.ananicy.enable", "default": False},
    {"id": "gtaFix",  "name": "Correctif hosts GTA Online",     "key": "roudix.hosts.gtaFix.enable",   "default": False},
]

# Interrupteurs système indépendants, sans rapport les uns avec les autres —
# regroupés dans une page "System" plutôt que de créer une catégorie par
# option.
SYSTEM_TOGGLES = [
    {"id": "flatpak",        "name": "Flatpak",                          "key": "roudix.flatpak.enable",        "default": False},
    {"id": "virtualization", "name": "Virtualisation (QEMU/KVM)",        "key": "roudix.virtualization.enable",  "default": False},
    {"id": "waydroid",       "name": "Waydroid (apps Android)",          "key": "roudix.waydroid.enable",        "default": False},
    {"id": "mesaGit",        "name": "Mesa-git (pilotes GPU bleeding-edge)", "key": "roudix.mesa.useGit",        "default": False},
    {"id": "autoupdate",     "name": "Auto-update (git pull + rebuild programmé)", "key": "roudix.autoupdate.enable", "default": False},
    {"id": "undervoltAmd",   "name": "Undervolt GPU AMD (LACT)",         "key": "roudix.undervolt.only-amd.enable", "default": False},
    # "file": roudix.fastfetch.useNix est une option Home Manager (définie
    # dans modules/home/fastfetch.nix), pas une option système — elle doit
    # donc être écrite dans HOME_CONFIG_FILE, pas dans CONFIG_FILE.
    {"id": "fastfetchNix",   "name": "Config fastfetch Roudix",          "key": "roudix.fastfetch.useNix",       "default": True, "file": HOME_CONFIG_FILE},
    {"id": "fstrim",         "name": "Fstrim (TRIM auto pour SSD/NVMe)", "key": "roudix.fstrim.enable",          "default": True},
    {"id": "vmGuest",        "name": "Invité VM (QEMU/Spice agent)",     "key": "roudix.vmGuest.enable",         "default": False},
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
        self.set_title("Roudix — Customizer")
        self.set_default_size(760, 640)
        self.set_resizable(True)

        # Forcer un fond opaque sur la zone de contenu : sur certains
        # compositeurs (blur-behind Hyprland/niri, etc.), une classe CSS
        # sémantique comme "view" ne suffit pas toujours à empêcher le flou
        # du bureau de transparaître derrière une page courte (peu
        # d'options = grande zone "vide" sous le contenu). On force donc un
        # background-color explicite via un provider dédié, avec la couleur
        # de fond réelle de la fenêtre (@window_bg_color) pour rester
        # cohérent en clair comme en sombre.
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
            ("terminal",    "Terminal"),
            ("browser",     "Browser"),
            ("login_shell", "Login Shell"),
            ("filemanager", "File Manager"),
            ("chat",        "Chat Client"),
            ("system",      "System"),
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
        self.content_stack.set_valign(Gtk.Align.START)
        # Sans ça (vhomogeneous par défaut = True), le Stack demande
        # toujours la hauteur de sa page la PLUS haute (System, la plus
        # longue), même en affichant Login Shell — ce qui annulerait le
        # rétrécissement voulu ci-dessous.
        self.content_stack.set_vhomogeneous(False)
        # CROSSFADE force le Stack à garder, le temps de la transition, une
        # taille égale au MAX des deux pages (ancienne + nouvelle) — et sur
        # certaines versions de GTK4 cette taille "gonflée" reste collée
        # après la transition au lieu de redescendre à la hauteur réelle de
        # la page affichée. C'est ce qui crée la grande zone vide sous une
        # page courte (Browser, Gaming...) une fois qu'on est passé par une
        # page plus longue (System). NONE évite complètement le problème :
        # chaque page est mesurée pour elle-même, sans jamais retenir la
        # taille d'une page précédente.
        self.content_stack.set_transition_type(Gtk.StackTransitionType.NONE)

        content_scroll = Gtk.ScrolledWindow()
        content_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content_scroll.set_hexpand(True)
        # Se dimensionner sur la hauteur naturelle de la page affichée (donc
        # pas de scrollbar ni de grand vide pour 2 options), et ne se
        # transformer en zone défilante qu'au-delà de ce plafond (pages
        # longues comme Browser ou System).
        content_scroll.set_propagate_natural_height(True)
        content_scroll.set_max_content_height(480)
        content_scroll.set_vexpand(False)
        content_scroll.set_valign(Gtk.Align.START)
        # Fond opaque du thème, pour que la zone sous une page courte ne
        # laisse pas transparaître le fond flouté de la fenêtre.
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

        # ── "Terminal" page ─────────────────────────────────────────────────
        terminal_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        terminal_page.set_margin_top(4)
        terminal_page.set_margin_start(16)
        terminal_page.set_margin_end(16)
        terminal_page.set_margin_bottom(16)

        current_terminal = get_string_option("roudix.terminal", "ghostty")
        self.terminal_selector = SelectorGroup("Default terminal", TERMINALS, current_terminal, dark)
        terminal_page.append(self.terminal_selector)

        self.content_stack.add_named(terminal_page, "terminal")

        # ── "Browser" page: checklist (roudix.browsers is a list) ──────────
        browser_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        browser_page.set_margin_top(4)
        browser_page.set_margin_start(16)
        browser_page.set_margin_end(16)
        browser_page.set_margin_bottom(16)

        btitle = Gtk.Label(label="Browser", halign=Gtk.Align.START)
        btitle.add_css_class("title-2")
        bsubtitle = Gtk.Label(
            label="Pick any number — the first one checked below becomes the "
                  "default (niri's MOD+B shortcut).",
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

        # Zen Browser vit à part côté Nix (flake input séparé, pas dans
        # browserDefs) : switch d'activation + choix du loader de mods
        # (natif vs Sine, mutuellement exclusifs côté Nix) + checklist des
        # mods, qui lit/écrit roudix.zen.mods ou roudix.zen.sine.mods selon
        # l'état du switch Sine. Le switch Sine n'a de sens que si Zen est
        # actif, et la checklist de mods que si Sine l'est aussi — donc les
        # trois sont chaînés en cascade plutôt que toujours visibles.
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

        self.sine_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sine_label = Gtk.Label(label="Sine mod loader", halign=Gtk.Align.START)
        sine_label.set_hexpand(True)
        self.sine_switch = Gtk.Switch()
        self.sine_switch.set_valign(Gtk.Align.CENTER)
        current_sine = get_bool_option("roudix.zen.sine.enable", False)
        self.sine_switch.set_active(current_sine)
        self.sine_row.append(sine_label)
        self.sine_row.append(self.sine_switch)
        browser_page.append(self.sine_row)

        self.sine_note = Gtk.Label(
            label="Native Zen mods and Sine mods can't be active at the same "
                  "time — the list below always targets whichever is on.",
        )
        self.sine_note.add_css_class("dim-label")
        self.sine_note.set_wrap(True)
        self.sine_note.set_halign(Gtk.Align.START)
        browser_page.append(self.sine_note)

        zen_mods_current_ids = set(
            get_list_option("roudix.zen.sine.mods" if current_sine else "roudix.zen.mods", [])
        )
        zen_mods_current = {m["id"]: (m["id"] in zen_mods_current_ids) for m in ZEN_MODS}
        self.zen_mods_group = ToggleListGroup("Mods", ZEN_MODS, zen_mods_current)
        browser_page.append(self.zen_mods_group)

        self.zen_mods_placeholder = None
        if not ZEN_MODS:
            self.zen_mods_placeholder = Gtk.Label(
                label="No mods listed yet — add your mod IDs to ZEN_MODS in the script.",
            )
            self.zen_mods_placeholder.add_css_class("dim-label")
            self.zen_mods_placeholder.set_halign(Gtk.Align.START)
            browser_page.append(self.zen_mods_placeholder)

        def _update_zen_cascade(*_):
            zen_on = self.zen_switch.get_active()
            sine_on = self.sine_switch.get_active()
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
        self.login_shell_selector = SelectorGroup("Login shell", LOGIN_SHELLS, current_login_shell, dark)
        login_shell_page.append(self.login_shell_selector)

        login_shell_note = Gtk.Label(
            label="This is your terminal login shell — not the graphical shell "
                  "under Desktop (noctalia/dms/caelestia).",
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
        self.filemanager_selector = SelectorGroup("File manager", FILE_MANAGERS, current_filemanager, dark)
        filemanager_page.append(self.filemanager_selector)

        self.content_stack.add_named(filemanager_page, "filemanager")

        # ── "Chat Client" page ──────────────────────────────────────────────
        chat_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        chat_page.set_margin_top(4)
        chat_page.set_margin_start(16)
        chat_page.set_margin_end(16)
        chat_page.set_margin_bottom(16)

        current_matrix = get_string_option("roudix.matrixClient", "element")
        self.matrix_selector = SelectorGroup("Matrix client", MATRIX_CLIENTS, current_matrix, dark)
        chat_page.append(self.matrix_selector)

        current_discord = get_string_option("roudix.discord", "vencord")
        self.discord_selector = SelectorGroup("Discord", DISCORD_OPTIONS, current_discord, dark)
        chat_page.append(self.discord_selector)

        self.content_stack.add_named(chat_page, "chat")

        # ── "System" page: independent toggles + RGB backend ───────────────
        system_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        system_page.set_margin_top(4)
        system_page.set_margin_start(16)
        system_page.set_margin_end(16)
        system_page.set_margin_bottom(16)

        # roudix.undervolt.only-amd.enable (undervolt.nix) force
        # amdgpu.ppfeaturemask, sans rapport avec Nvidia/Intel — inutile de
        # proposer ce switch sur une machine dont hardware.myGpu n'est pas
        # "amd"/"amd-legacy" (voir hosts/roudix/local.nix).
        current_gpu = get_string_option("hardware.myGpu", "amd")
        self.system_toggles = [
            t for t in SYSTEM_TOGGLES
            if t["id"] != "undervoltAmd" or current_gpu in ("amd", "amd-legacy")
        ]
        system_current = {
            t["id"]: get_bool_option(t["key"], t["default"], path=t.get("file", CONFIG_FILE))
            for t in self.system_toggles
        }
        self.system_group = ToggleListGroup("Toggles", self.system_toggles, system_current)
        system_page.append(self.system_group)

        current_rgb = get_string_option("roudix.rgb", "none")
        self.rgb_selector = SelectorGroup("RGB backend", RGB_BACKENDS, current_rgb, dark)
        system_page.append(self.rgb_selector)

        self.content_stack.add_named(system_page, "system")

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
        self._update_filemanager_visibility(current_de)

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
        # Filet de sécurité : force le ScrolledWindow à se re-mesurer sur la
        # page nouvellement affichée plutôt que de garder l'allocation
        # (potentiellement plus grande) de la page précédente.
        self.content_scroll.queue_resize()

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

    def _update_filemanager_visibility(self, de_id: str):
        """Cache la page File Manager pour gnome/kde (sans effet dessus) et
        retombe sur Desktop si elle était sélectionnée."""
        supported = de_id in FILE_MANAGER_SUPPORTED_DE
        row = self._category_rows["filemanager"]
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
        self.terminal_selector.update_icons(dark)
        self.login_shell_selector.update_icons(dark)
        self.filemanager_selector.update_icons(dark)
        self.matrix_selector.update_icons(dark)
        self.rgb_selector.update_icons(dark)

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

        # Terminal par défaut
        cur_terminal = get_string_option("roudix.terminal", "ghostty")
        new_terminal = self.terminal_selector.selected_id
        terminal_changed = new_terminal != cur_terminal

        # Navigateurs (liste) + Zen (switch séparé)
        cur_browsers = get_list_option("roudix.browsers", ["brave"])
        new_browsers = [b["id"] for b in BROWSERS if self.browser_group.get_states()[b["id"]]]
        browsers_changed = new_browsers != cur_browsers

        cur_zen = get_bool_option("roudix.zen.enable", False)
        new_zen = self.zen_switch.get_active()
        zen_changed = new_zen != cur_zen

        cur_sine = get_bool_option("roudix.zen.sine.enable", False)
        new_sine = self.sine_switch.get_active()
        sine_changed = new_sine != cur_sine

        # La liste de mods cible roudix.zen.mods ou roudix.zen.sine.mods selon
        # l'état choisi pour Sine (pas l'ancien état) — c'est bien celui-là
        # qui sera actif une fois le rebuild fait.
        zen_mods_key = "roudix.zen.sine.mods" if new_sine else "roudix.zen.mods"
        cur_zen_mods = get_list_option(zen_mods_key, [])
        new_zen_mods = [m["id"] for m in ZEN_MODS if self.zen_mods_group.get_states()[m["id"]]]
        zen_mods_changed = new_zen_mods != cur_zen_mods

        # Apps gaming : booléens indépendants, on ne touche que celles qui ont changé
        gaming_changes = _diff_bool_items(GAMING_APPS, self.gaming_apps_group.get_states())

        # Tweaks gaming annexes (ananicy, correctif GTA)
        gaming_extras_changes = _diff_bool_items(GAMING_EXTRAS, self.gaming_extras_group.get_states())

        # Interrupteur maître du groupe gaming
        cur_gaming_master = get_bool_option("roudix.gaming.enable", True)
        new_gaming_master = self.gaming_master_switch.get_active()
        gaming_master_changed = new_gaming_master != cur_gaming_master

        # Shell de login (fish/bash)
        cur_login_shell = get_string_option("roudix.shell", "fish")
        new_login_shell = self.login_shell_selector.selected_id
        login_shell_changed = new_login_shell != cur_login_shell

        # Gestionnaire de fichiers — pertinent uniquement sur les compositeurs bruts
        filemanager_relevant = new_de in FILE_MANAGER_SUPPORTED_DE
        cur_filemanager = get_string_option("roudix.fileManager", "nautilus")
        new_filemanager = self.filemanager_selector.selected_id if filemanager_relevant else cur_filemanager
        filemanager_changed = filemanager_relevant and (new_filemanager != cur_filemanager)

        # Client Matrix
        cur_matrix = get_string_option("roudix.matrixClient", "element")
        new_matrix = self.matrix_selector.selected_id
        matrix_changed = new_matrix != cur_matrix

        # Discord
        cur_discord = get_string_option("roudix.discord", "vencord")
        new_discord = self.discord_selector.selected_id
        discord_changed = new_discord != cur_discord

        # Interrupteurs système indépendants
        system_changes = _diff_bool_items(self.system_toggles, self.system_group.get_states())

        # Backend RGB
        cur_rgb = get_string_option("roudix.rgb", "none")
        new_rgb = self.rgb_selector.selected_id
        rgb_changed = new_rgb != cur_rgb

        if not any([de_changed, shell_changed, integration_changed, editor_changed,
                    terminal_changed, browsers_changed, zen_changed, sine_changed,
                    zen_mods_changed,
                    login_shell_changed, filemanager_changed, matrix_changed,
                    discord_changed,
                    system_changes, rgb_changed,
                    gaming_changes, gaming_extras_changes, gaming_master_changed]):
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
        if terminal_changed:
            changes.append(f"Terminal: <b>{cur_terminal}</b> → <b>{new_terminal}</b>")
        if browsers_changed:
            changes.append(f"Browsers: <b>{', '.join(new_browsers) or 'none'}</b>")
        if zen_changed:
            changes.append(f"Zen Browser: <b>{'enabled' if new_zen else 'disabled'}</b>")
        if sine_changed:
            changes.append(f"Sine mod loader: <b>{'enabled' if new_sine else 'disabled'}</b>")
        if zen_mods_changed:
            changes.append(f"Zen mods: <b>{', '.join(new_zen_mods) or 'none'}</b>")
        if login_shell_changed:
            changes.append(f"Login shell: <b>{cur_login_shell}</b> → <b>{new_login_shell}</b>")
        if filemanager_changed:
            changes.append(f"File manager: <b>{cur_filemanager}</b> → <b>{new_filemanager}</b>")
        if matrix_changed:
            changes.append(f"Matrix client: <b>{cur_matrix}</b> → <b>{new_matrix}</b>")
        if discord_changed:
            changes.append(f"Discord: <b>{cur_discord}</b> → <b>{new_discord}</b>")
        if rgb_changed:
            changes.append(f"RGB backend: <b>{cur_rgb}</b> → <b>{new_rgb}</b>")
        if gaming_master_changed:
            changes.append(f"Gaming: <b>{'enabled' if new_gaming_master else 'disabled'}</b>")
        for _key, new_val, name, _file in gaming_changes.values():
            changes.append(f"{name}: <b>{'enabled' if new_val else 'disabled'}</b>")
        for _key, new_val, name, _file in gaming_extras_changes.values():
            changes.append(f"{name}: <b>{'enabled' if new_val else 'disabled'}</b>")
        for _key, new_val, name, _file in system_changes.values():
            changes.append(f"{name}: <b>{'enabled' if new_val else 'disabled'}</b>")
        body_changes = "\n".join(changes)

        pending = {
            "de_changed": de_changed, "new_de": new_de,
            "shell_changed": shell_changed, "new_shell": new_shell,
            "integration_changed": integration_changed, "new_integration": new_integration,
            "editor_changed": editor_changed, "new_editor": new_editor,
            "terminal_changed": terminal_changed, "new_terminal": new_terminal,
            "browsers_changed": browsers_changed, "new_browsers": new_browsers,
            "zen_changed": zen_changed, "new_zen": new_zen,
            "sine_changed": sine_changed, "new_sine": new_sine,
            "zen_mods_changed": zen_mods_changed, "new_zen_mods": new_zen_mods, "zen_mods_key": zen_mods_key,
            "login_shell_changed": login_shell_changed, "new_login_shell": new_login_shell,
            "filemanager_changed": filemanager_changed, "new_filemanager": new_filemanager,
            "matrix_changed": matrix_changed, "new_matrix": new_matrix,
            "discord_changed": discord_changed, "new_discord": new_discord,
            "rgb_changed": rgb_changed, "new_rgb": new_rgb,
            "gaming_master_changed": gaming_master_changed, "new_gaming_master": new_gaming_master,
            "gaming_changes": gaming_changes,
            "gaming_extras_changes": gaming_extras_changes,
            "system_changes": system_changes,
        }

        dialog = Adw.AlertDialog()
        dialog.set_heading("Apply changes?")
        dialog.set_body(
            f"{body_changes}\n\n"
            "Apply now switches your running session immediately (a few things, "
            "like the desktop/shell, only fully take effect after you log out). "
            "Apply at next boot just prepares the new generation — nothing "
            "changes until you restart."
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("boot", "Apply at Next Boot")
        dialog.add_response("switch", "Apply Now")
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

        if pending["terminal_changed"]:
            result = set_string_option("roudix.terminal", pending["new_terminal"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing terminal config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if pending["browsers_changed"]:
            result = set_list_option("roudix.browsers", pending["new_browsers"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing browsers config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if pending["zen_changed"]:
            result = set_bool_option("roudix.zen.enable", pending["new_zen"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing Zen Browser config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if pending["sine_changed"]:
            result = set_bool_option("roudix.zen.sine.enable", pending["new_sine"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing Sine config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if pending["zen_mods_changed"]:
            result = set_list_option(pending["zen_mods_key"], pending["new_zen_mods"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing Zen mods config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if pending["login_shell_changed"]:
            result = set_string_option("roudix.shell", pending["new_login_shell"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing login shell config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if pending["filemanager_changed"]:
            result = set_string_option("roudix.fileManager", pending["new_filemanager"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing file manager config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if pending["matrix_changed"]:
            result = set_string_option("roudix.matrixClient", pending["new_matrix"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing Matrix client config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if pending["discord_changed"]:
            result = set_string_option("roudix.discord", pending["new_discord"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing Discord config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if pending["rgb_changed"]:
            result = set_string_option("roudix.rgb", pending["new_rgb"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing RGB backend config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if pending["gaming_master_changed"]:
            result = set_bool_option("roudix.gaming.enable", pending["new_gaming_master"])
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing gaming config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        for key, new_val, name, file in pending["gaming_changes"].values():
            result = set_bool_option(key, new_val, path=file)
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing {name} config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        for key, new_val, name, file in pending["gaming_extras_changes"].values():
            result = set_bool_option(key, new_val, path=file)
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing {name} config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        for key, new_val, name, file in pending["system_changes"].values():
            result = set_bool_option(key, new_val, path=file)
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
                f"Running: nh os {mode} --elevation-strategy pkexec "
                f"--accept-flake-config {NH_FLAKE}"
            )
            log.info(cmd_str)
            GLib.idle_add(self._term_append, cmd_str, "dim")
            GLib.idle_add(self._term_append, "Checking repositories...", "dim")

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
                GLib.idle_add(self._term_append, "✓ Rebuild completed and applied to your running session.", "ok")
                GLib.idle_add(
                    self.status.set_markup,
                    "<span color='green'>✓ Done! Applied now — some things (desktop/shell) "
                    "may still need a logout to fully take effect.</span>",
                )
            else:
                GLib.idle_add(self._term_append, "✓ Rebuild completed successfully. Reboot to apply changes.", "ok")
                GLib.idle_add(
                    self.status.set_markup,
                    "<span color='green'>✓ Done! Reboot to apply changes.</span>",
                )
            GLib.idle_add(self._stop_progress)

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
