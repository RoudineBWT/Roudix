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

# Compositeurs qui supportent le choix de shell graphique
SHELL_SUPPORTED_DE    = {"niri", "hyprland"}
CAELESTIA_SUPPORTED_DE = {"hyprland"}


def shells_for_de(de_id: str) -> list:
    """Return the shell list appropriate for the given DE."""
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


# ── Main window ───────────────────────────────────────────────────────────────

class RoudixSwitcherWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Roudix — Desktop Switcher")
        self.set_default_size(480, 640)
        self.set_resizable(False)

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
        clamp.set_maximum_size(440)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)

        # ── Description ───────────────────────────────────────────────────
        desc = Gtk.Label()
        desc.set_markup(
            "<b>Select your desktop environment</b>\n"
            "<span size='small'>The system will rebuild after your selection.\n"
            "This may take a few minutes.</span>"
        )
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_wrap(True)
        main_box.append(desc)

        # ── DE selector ───────────────────────────────────────────────────
        self.de_selector = SelectorGroup(
            "Desktop environment",
            ENVIRONMENTS,
            current_de,
            dark,
        )
        # Écouter les changements de DE pour afficher/cacher/mettre à jour le shell selector
        for de_id, check in self.de_selector.rows.items():
            check.connect("toggled", self._on_de_toggled)
        main_box.append(self.de_selector)

        # ── Shell selector (niri/hyprland uniquement) ─────────────────────
        # Construire avec la liste correcte selon le DE actuel
        initial_shells = shells_for_de(current_de)
        # Si le shell sauvegardé n'est pas dispo pour ce DE, fallback noctalia
        if current_shell not in {s["id"] for s in initial_shells}:
            current_shell = "noctalia"

        self.shell_selector = SelectorGroup(
            "Graphical shell",
            initial_shells,
            current_shell,
            dark,
        )
        self.shell_selector.set_visible(current_de in SHELL_SUPPORTED_DE)
        main_box.append(self.shell_selector)

        # ── Status area ───────────────────────────────────────────────────
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_box.set_size_request(-1, 48)
        status_box.set_valign(Gtk.Align.CENTER)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_pulse_step(0.07)
        self.progress_bar.set_visible(False)

        self.log_label = Gtk.Label(label="")
        self.log_label.set_justify(Gtk.Justification.CENTER)
        self.log_label.set_max_width_chars(55)
        self.log_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.log_label.set_valign(Gtk.Align.CENTER)
        self.log_label.set_visible(False)
        attrs = Pango.AttrList()
        attrs.insert(Pango.attr_scale_new(0.8))
        self.log_label.set_attributes(attrs)

        self.status = Gtk.Label(label="")
        self.status.set_justify(Gtk.Justification.CENTER)
        self.status.set_max_width_chars(55)
        self.status.set_lines(2)
        self.status.set_ellipsize(Pango.EllipsizeMode.END)
        self.status.set_valign(Gtk.Align.CENTER)

        status_box.append(self.progress_bar)
        status_box.append(self.log_label)
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

    def _start_progress(self):
        self.progress_bar.set_visible(True)
        self.log_label.set_label("")
        self.log_label.set_visible(True)
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
        self.log_label.set_visible(False)
        self.log_label.set_label("")

    def _on_de_toggled(self, check, *_):
        """Affiche/cache le shell selector et met à jour la liste selon le DE choisi."""
        new_de  = self.de_selector.selected_id
        visible = new_de in SHELL_SUPPORTED_DE
        self.shell_selector.set_visible(visible)

        if not visible:
            return

        # Ajouter ou retirer caelestia selon le DE
        if new_de in CAELESTIA_SUPPORTED_DE:
            for item in CAELESTIA:
                self.shell_selector.add_item(item)
        else:
            for item in CAELESTIA:
                self.shell_selector.remove_item(item["id"])

        log.debug(
            "DE changed to '%s' — shell selector updated (caelestia: %s)",
            new_de,
            new_de in CAELESTIA_SUPPORTED_DE,
        )

    def on_theme_changed(self, style_manager, _param):
        dark = style_manager.get_dark()
        log.debug("Theme changed — dark: %s", dark)
        self.de_selector.update_icons(dark)
        self.shell_selector.update_icons(dark)

    # ── Apply logic ───────────────────────────────────────────────────────

    def on_apply(self, btn):
        new_de    = self.de_selector.selected_id
        cur_de    = get_current_de()
        cur_shell = get_current_shell()

        de_changed = new_de != cur_de

        # Le shell n'est pertinent que pour niri/hyprland
        shell_relevant = new_de in SHELL_SUPPORTED_DE
        new_shell      = self.shell_selector.selected_id if shell_relevant else cur_shell
        shell_changed  = shell_relevant and (new_shell != cur_shell)

        if not de_changed and not shell_changed:
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
        body_changes = "\n".join(changes)

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
        dialog.connect("response", self.on_confirm_response, new_de, new_shell, de_changed, shell_changed)
        dialog.present(self)

    def on_confirm_response(self, dialog, response, new_de, new_shell, de_changed, shell_changed):
        if response != "confirm":
            log.info("User cancelled the rebuild dialog.")
            return

        if de_changed:
            result = set_de(new_de)
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing DE config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        if shell_changed:
            result = set_shell(new_shell)
            if result is not True:
                self.status.set_markup(
                    f"<span color='red'>Error writing shell config: {GLib.markup_escape_text(result)}</span>"
                )
                return

        self.status.set_markup("")
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
            log.info(
                "Running: nh os boot --elevation-strategy pkexec --accept-flake-config %s",
                NH_FLAKE,
            )
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

            for line in proc.stdout:
                line = strip_ansi(line).strip()
                if line:
                    log.info(line)
                    GLib.idle_add(self.log_label.set_label, line)

            proc.wait()

            if proc.returncode != 0:
                raise subprocess.CalledProcessError(proc.returncode, "nh")

            log.info("Rebuild completed successfully.")
            GLib.idle_add(self._stop_progress)
            GLib.idle_add(
                self.status.set_markup,
                "<span color='green'>✓ Done! Reboot to apply changes.</span>",
            )

        except subprocess.CalledProcessError as e:
            log.error("Rebuild failed (exit code %d).", e.returncode)
            GLib.idle_add(self._stop_progress)
            GLib.idle_add(
                self.status.set_markup,
                "<span color='red'>✗ Rebuild failed. Check <tt>~/.local/share/roudix-switcher/switcher.log</tt> for details.</span>",
            )
        except Exception as e:
            log.exception("Unexpected error during rebuild.")
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
