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
        "subtitle": "Scrollable tiling Wayland compositor + Noctalia shell",
        "icon":     "niri.svg",
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


def load_icon(icon_filename, dark):
    """Load icon from dark/ or light/ subfolder, fallback to theme icon."""
    theme = "dark" if dark else "light"
    path = os.path.join(ICONS_DIR, theme, icon_filename)
    if os.path.exists(path):
        img = Gtk.Image.new_from_file(path)
    else:
        # fallback: try root icons dir
        fallback = os.path.join(ICONS_DIR, icon_filename)
        if os.path.exists(fallback):
            img = Gtk.Image.new_from_file(fallback)
        else:
            img = Gtk.Image.new_from_icon_name(icon_filename)
    img.set_pixel_size(32)
    return img


# ── Main window ───────────────────────────────────────────────────────────────

class RoudixSwitcherWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Roudix — Desktop Switcher")
        self.set_default_size(480, 420)
        self.set_resizable(False)

        self.selected_de = get_current_de()
        log.info("Current desktop environment: %s", self.selected_de)

        # Track icon widgets per env id so we can reload them on theme change
        self.icon_widgets = {}

        # ── Style manager — watch for theme changes ───────────────────────
        self.style_manager = Adw.StyleManager.get_default()
        self.style_manager.connect("notify::dark", self.on_theme_changed)

        # ── Main layout ──────────────────────────────────────────────────
        toolbar = Adw.ToolbarView()
        self.set_content(toolbar)

        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        toolbar.add_top_bar(header)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(440)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)

        # ── Description ──────────────────────────────────────────────────
        desc = Gtk.Label()
        desc.set_markup(
            "<b>Select your desktop environment</b>\n"
            "<span size='small'>The system will rebuild after your selection.\n"
            "This may take a few minutes.</span>"
        )
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_wrap(True)
        main_box.append(desc)

        # ── Environment list ─────────────────────────────────────────────
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.add_css_class("boxed-list")

        self.rows = {}
        for env in ENVIRONMENTS:
            row = Adw.ActionRow()
            row.set_title(env["name"])
            row.set_subtitle(env["subtitle"])

            icon = load_icon(env["icon"], self.style_manager.get_dark())
            self.icon_widgets[env["id"]] = (icon, env["icon"])
            row.add_prefix(icon)

            if env.get("disabled"):
                row.set_sensitive(False)
            else:
                check = Gtk.CheckButton()
                check.set_valign(Gtk.Align.CENTER)
                if env["id"] == self.selected_de:
                    check.set_active(True)
                check.connect("toggled", self.on_check_toggled, env["id"])
                row.add_suffix(check)
                self.rows[env["id"]] = check

            self.list_box.append(row)

        main_box.append(self.list_box)

        # ── Status area (barre de progression + label résultat) ──────────
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
        toolbar.set_content(clamp)

        # ── Buttons ──────────────────────────────────────────────────────
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

    def _start_progress(self):
        """Affiche la barre et démarre le pulse."""
        self.progress_bar.set_visible(True)
        self.log_label.set_label("")
        self.log_label.set_visible(True)
        self.status.set_label("")
        if self._pulse_source is None:
            self._pulse_source = GLib.timeout_add(80, self._do_pulse)

    def _do_pulse(self):
        self.progress_bar.pulse()
        return True  # répéter

    def _stop_progress(self):
        """Arrête le pulse et cache la barre + log_label."""
        if self._pulse_source is not None:
            GLib.source_remove(self._pulse_source)
            self._pulse_source = None
        self.progress_bar.set_visible(False)
        self.log_label.set_visible(False)
        self.log_label.set_label("")

    def on_theme_changed(self, style_manager, _param):
        """Reload all icons when the system theme switches dark/light."""
        dark = style_manager.get_dark()
        log.debug("Theme changed — dark: %s", dark)
        for env_id, (img_widget, icon_filename) in self.icon_widgets.items():
            theme = "dark" if dark else "light"
            path = os.path.join(ICONS_DIR, theme, icon_filename)
            if os.path.exists(path):
                img_widget.set_from_file(path)
            else:
                fallback = os.path.join(ICONS_DIR, icon_filename)
                if os.path.exists(fallback):
                    img_widget.set_from_file(fallback)

    def on_check_toggled(self, check, de_id):
        if check.get_active():
            self.selected_de = de_id
            log.debug("User selected desktop environment: %s", de_id)
            for key, other in self.rows.items():
                if key != de_id:
                    other.handler_block_by_func(self.on_check_toggled)
                    other.set_active(False)
                    other.handler_unblock_by_func(self.on_check_toggled)

    def on_apply(self, btn):
        if self.selected_de == get_current_de():
            log.info("Already on '%s' — nothing to do.", self.selected_de)
            self.status.set_markup(
                f"<span color='gray'>Already on <b>{self.selected_de}</b> — nothing to do.</span>"
            )
            return

        dialog = Adw.AlertDialog()
        dialog.set_heading("Switch desktop environment?")
        dialog.set_body(
            f"This will switch to <b>{self.selected_de}</b> and rebuild your NixOS configuration.\n\n"
            "The rebuild may take a few minutes."
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("confirm", "Apply & Rebuild")
        dialog.set_response_appearance("confirm", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("confirm")
        dialog.connect("response", self.on_confirm_response)
        dialog.present(self)

    def on_confirm_response(self, dialog, response):
        if response != "confirm":
            log.info("User cancelled the rebuild dialog.")
            return

        result = set_de(self.selected_de)
        if result is not True:
            self.status.set_markup(
                f"<span color='red'>Error writing config: {GLib.markup_escape_text(result)}</span>"
            )
            return

        self.status.set_markup("")
        GLib.idle_add(self._start_progress)
        self.apply_btn.set_sensitive(False)
        self.exit_btn.set_sensitive(False)

        log.info("Starting NixOS rebuild for desktop: %s", self.selected_de)

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
                    "--accept-flake-config", NH_FLAKE,
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
                "<span color='green'>✓ Done! Log out and back in to apply changes.</span>",
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
