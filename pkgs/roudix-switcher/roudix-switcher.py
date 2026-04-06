#!/usr/bin/env python3
import gi
import os
import subprocess
import sys

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

CONFIG_FILE = os.path.expanduser("~/.config/roudix/hosts/roudix/configuration.nix")
NH_FLAKE    = os.path.expanduser("~/.config/roudix")

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR  = os.path.join(SCRIPT_DIR, "../share/roudix-switcher/icons")

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
        "subtitle": "KDE Plasma — Highly customizable and feature-rich desktop environment ",
        "icon":     "kde.svg",
    },
]


def make_icon(icon_value):
    """Load a custom SVG from the icons/ folder, fallback to theme icon name."""
    path = os.path.join(ICONS_DIR, icon_value)
    if os.path.exists(path):
        img = Gtk.Image.new_from_file(path)
    else:
        img = Gtk.Image.new_from_icon_name(icon_value)
    img.set_pixel_size(32)
    return img


def get_current_de():
    try:
        with open(CONFIG_FILE) as f:
            for line in f:
                if "roudix.desktop.type" in line:
                    import re
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
        import re
        new = re.sub(
            r'roudix\.desktop\.type\s*=\s*"[^"]*"',
            f'roudix.desktop.type = "{de_id}"',
            content,
        )
        with open(CONFIG_FILE, "w") as f:
            f.write(new)
        return True
    except Exception as e:
        return str(e)


class RoudixSwitcherWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Roudix — Desktop Switcher")
        self.set_default_size(480, 420)
        self.set_resizable(False)

        self.selected_de = get_current_de()

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

            icon = make_icon(env["icon"])
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

        # ── Status label ─────────────────────────────────────────────────
        self.status = Gtk.Label(label="")
        self.status.set_wrap(True)
        self.status.set_justify(Gtk.Justification.CENTER)
        main_box.append(self.status)

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

    def on_check_toggled(self, check, de_id):
        if check.get_active():
            self.selected_de = de_id
            # Uncheck all others
            for key, other in self.rows.items():
                if key != de_id:
                    other.handler_block_by_func(self.on_check_toggled)
                    other.set_active(False)
                    other.handler_unblock_by_func(self.on_check_toggled)

    def on_apply(self, btn):
        if self.selected_de == get_current_de():
            self.status.set_markup(
                f"<span color='gray'>Already on <b>{self.selected_de}</b> — nothing to do.</span>"
            )
            return

        # Confirm dialog
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
            return

        result = set_de(self.selected_de)
        if result is not True:
            self.status.set_markup(f"<span color='red'>Error: {result}</span>")
            return

        self.status.set_markup("<span color='orange'>Rebuilding… this window will close when done.</span>")
        self.apply_btn.set_sensitive(False)
        self.exit_btn.set_sensitive(False)

        GLib.timeout_add(100, self.run_rebuild)

    def run_rebuild(self):
        try:
            subprocess.run(
                ["nh", "os", "switch", "--accept-flake-config", NH_FLAKE],
                check=True,
            )
            self.status.set_markup("<span color='green'>Done! Log out and back in to apply changes.</span>")
        except subprocess.CalledProcessError as e:
            self.status.set_markup(f"<span color='red'>Rebuild failed. Check your terminal for details.</span>")
        finally:
            self.apply_btn.set_sensitive(True)
            self.exit_btn.set_sensitive(True)
        return False


class RoudixSwitcherApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.roudix.switcher")
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        win = RoudixSwitcherWindow(app)
        win.present()


def main():
    app = RoudixSwitcherApp()
    sys.exit(app.run(sys.argv))


if __name__ == "__main__":
    main()
