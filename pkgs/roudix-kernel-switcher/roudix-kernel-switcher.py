#!/usr/bin/env python3
# roudix-kernel-switcher — GTK4/Adwaita GUI for kernel switching
# Writes hardware.myKernel directly into local.nix and runs nh os boot.

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Pango

import os
import re
import subprocess
import threading
import logging
import sys

# ── Paths ─────────────────────────────────────────────────────────────────────

NH_FLAKE    = os.environ.get("NH_FLAKE", os.path.expanduser("~/.config/roudix"))
CONFIG_FILE = os.path.join(NH_FLAKE, "hosts", "roudix", "local.nix")

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# ── Logging ───────────────────────────────────────────────────────────────────

LOG_DIR  = os.path.expanduser("~/.local/share/roudix-kernel-switcher")
LOG_FILE = os.path.join(LOG_DIR, "switcher.log")

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

log = logging.getLogger("roudix-kernel-switcher")

# ── kernel catalogue ──────────────────────────────────────────────────────────

KERNELS = {
    "Latest": [
        ("cachyos-latest",          "Standard latest"),
        ("cachyos-latest-v3",       "x86_64-v3  —  recommended for modern CPUs"),
        ("cachyos-latest-v4",       "x86_64-v4  —  AVX-512"),
        ("cachyos-latest-zen4",     "AMD Zen 4 optimised"),
        ("cachyos-latest-lto",      "LTO"),
        ("cachyos-latest-lto-v3",   "LTO + v3  —  best perf on modern CPUs"),
        ("cachyos-latest-lto-v4",   "LTO + v4"),
        ("cachyos-latest-lto-zen4", "LTO + Zen 4"),
    ],
    "LTS": [
        ("cachyos-lts",             "Long-term support"),
        ("cachyos-lts-v3",          "LTS + v3"),
        ("cachyos-lts-v4",          "LTS + v4"),
        ("cachyos-lts-zen4",        "LTS + Zen 4"),
        ("cachyos-lts-lto",         "LTS + LTO"),
        ("cachyos-lts-lto-v3",      "LTS + LTO + v3  —  stable + performance"),
        ("cachyos-lts-lto-v4",      "LTS + LTO + v4"),
        ("cachyos-lts-lto-zen4",    "LTS + LTO + Zen 4"),
    ],
    "Variants": [
        ("cachyos-bore",            "BORE scheduler"),
        ("cachyos-bore-lto",        "BORE + LTO"),
        ("cachyos-bmq",             "BMQ scheduler"),
        ("cachyos-bmq-lto",         "BMQ + LTO"),
        ("cachyos-eevdf",           "EEVDF scheduler"),
        ("cachyos-eevdf-lto",       "EEVDF + LTO"),
        ("cachyos-hardened",        "Security hardened"),
        ("cachyos-hardened-lto",    "Hardened + LTO"),
        ("cachyos-rt-bore",         "Real-time + BORE"),
        ("cachyos-rt-bore-lto",     "Real-time + BORE + LTO"),
        ("cachyos-deckify",         "Steam Deck optimised"),
        ("cachyos-deckify-lto",     "Steam Deck + LTO"),
        ("cachyos-server",          "Server optimised"),
        ("cachyos-server-lto",      "Server + LTO"),
        ("cachyos-rc",              "Release candidate  —  unstable"),
        ("cachyos-rc-lto",          "RC + LTO"),
    ],
}

# ── helpers ───────────────────────────────────────────────────────────────────

def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)


def detect_current_kernel() -> str | None:
    try:
        text = open(CONFIG_FILE).read()
        m = re.search(r'hardware\.myKernel\s*=\s*"([^"]+)"', text)
        return m.group(1) if m else None
    except OSError:
        return None


def set_kernel(kernel: str) -> bool | str:
    """Write hardware.myKernel into local.nix. Returns True on success, error string on failure."""
    try:
        with open(CONFIG_FILE) as f:
            content = f.read()
        new = re.sub(
            r'hardware\.myKernel\s*=\s*"[^"]*"',
            f'hardware.myKernel = "{kernel}"',
            content,
        )
        with open(CONFIG_FILE, "w") as f:
            f.write(new)
        log.info("Configuration updated: hardware.myKernel set to '%s'.", kernel)
        return True
    except Exception as e:
        log.error("Failed to write configuration: %s", e)
        return str(e)


# ── main window ───────────────────────────────────────────────────────────────

class KernelSwitcher(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Kernel Switcher")
        self.set_default_size(620, 700)

        self._selected: str | None = None
        self._current = detect_current_kernel()
        self._group_anchor = Gtk.CheckButton()

        # root
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root)

        # header
        header = Adw.HeaderBar()
        root.append(header)

        # scrollable body
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        root.append(scroll)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        body.set_margin_top(16)
        body.set_margin_bottom(16)
        body.set_margin_start(16)
        body.set_margin_end(16)
        scroll.set_child(body)

        # active kernel banner
        if self._current:
            banner = Adw.ActionRow()
            banner.set_title("Active kernel")
            banner.set_subtitle(self._current)
            banner.add_css_class("card")
            banner.set_margin_bottom(16)
            body.append(banner)

        # kernel groups
        for group_name, entries in KERNELS.items():
            grp_lbl = Gtk.Label(label=group_name.upper())
            grp_lbl.set_halign(Gtk.Align.START)
            grp_lbl.set_margin_top(8)
            grp_lbl.set_margin_bottom(4)
            grp_lbl.add_css_class("caption-heading")
            body.append(grp_lbl)

            lb = Gtk.ListBox()
            lb.set_selection_mode(Gtk.SelectionMode.NONE)
            lb.add_css_class("boxed-list")
            lb.set_margin_bottom(12)
            body.append(lb)

            for variant, desc in entries:
                row = Adw.ActionRow()
                row.set_title(variant)
                row.set_subtitle(desc)

                check = Gtk.CheckButton()
                check.set_group(self._group_anchor)
                check.set_valign(Gtk.Align.CENTER)
                if variant == self._current:
                    check.set_active(True)
                    self._selected = variant

                check.connect("toggled", self._on_toggled, variant)
                row.add_prefix(check)
                row.set_activatable_widget(check)
                lb.append(row)

        # bottom bar
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        root.append(sep)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_row.set_margin_top(12)
        btn_row.set_margin_bottom(12)
        btn_row.set_margin_start(16)
        btn_row.set_margin_end(16)
        root.append(btn_row)

        self._status_lbl = Gtk.Label(label="Select a kernel variant above.")
        self._status_lbl.set_hexpand(True)
        self._status_lbl.set_halign(Gtk.Align.START)
        self._status_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self._status_lbl.add_css_class("dim-label")
        btn_row.append(self._status_lbl)

        self._apply_btn = Gtk.Button(label="Apply & Rebuild")
        self._apply_btn.add_css_class("suggested-action")
        self._apply_btn.set_sensitive(False)
        self._apply_btn.connect("clicked", self._on_apply)
        btn_row.append(self._apply_btn)

        # log expander
        self._log_expander = Gtk.Expander(label="Build log")
        self._log_expander.set_margin_start(16)
        self._log_expander.set_margin_end(16)
        self._log_expander.set_margin_bottom(12)

        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_min_content_height(160)
        log_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self._log_buf = Gtk.TextBuffer()
        log_tv = Gtk.TextView(buffer=self._log_buf)
        log_tv.set_editable(False)
        log_tv.set_monospace(True)
        log_tv.set_wrap_mode(Gtk.WrapMode.CHAR)
        log_scroll.set_child(log_tv)
        self._log_tv = log_tv
        self._log_expander.set_child(log_scroll)
        root.append(self._log_expander)

    def _on_toggled(self, check, variant):
        if check.get_active():
            self._selected = variant
            changed = variant != self._current
            self._apply_btn.set_sensitive(changed)
            self._status_lbl.set_label(
                f"Will switch to: {variant}" if changed else "Already the active kernel.")

    def _on_apply(self, _btn):
        if not self._selected:
            return

        # Confirmation dialog — same pattern as roudix-switcher
        dialog = Adw.AlertDialog()
        dialog.set_heading("Apply changes?")
        dialog.set_body(
            f"Kernel: <b>{self._current or '?'}</b> → <b>{self._selected}</b>\n\n"
            "Your NixOS configuration will be rebuilt. This may take a few minutes."
        )
        dialog.set_body_use_markup(True)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("confirm", "Apply & Rebuild")
        dialog.set_response_appearance("confirm", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("confirm")
        dialog.connect("response", self._on_confirm_response)
        dialog.present(self)

    def _on_confirm_response(self, dialog, response):
        if response != "confirm":
            return

        result = set_kernel(self._selected)
        if result is not True:
            self._status_lbl.set_label(f"✗ Error writing config: {result}")
            return

        self._apply_btn.set_sensitive(False)
        self._status_lbl.set_label("Running nh os boot …")
        self._log_buf.set_text("")
        self._log_expander.set_expanded(True)
        threading.Thread(target=self._run_rebuild, daemon=True).start()

    def _run_rebuild(self):
        try:
            log.info("Running: nh os boot --elevation-strategy pkexec --accept-flake-config path:%s", NH_FLAKE)
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
                clean = strip_ansi(line)
                log.info(clean.rstrip())
                GLib.idle_add(self._append_log, clean)
            proc.wait()
            rc = proc.returncode
        except FileNotFoundError:
            GLib.idle_add(self._append_log, "ERROR: 'nh' not found in PATH.\n")
            rc = 127
        except Exception as e:
            GLib.idle_add(self._append_log, f"ERROR: {e}\n")
            rc = 1
        GLib.idle_add(self._finish, self._selected, rc)

    def _append_log(self, line):
        end = self._log_buf.get_end_iter()
        self._log_buf.insert(end, line)
        adj = self._log_tv.get_parent().get_vadjustment()
        adj.set_value(adj.get_upper())

    def _finish(self, kernel, rc):
        if rc == 0:
            self._current = kernel
            self._status_lbl.set_label(f"✓ Done — reboot to apply {kernel}.")
        else:
            self._status_lbl.set_label(f"✗ Build failed (exit {rc}). See log.")
            self._apply_btn.set_sensitive(True)


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.roudix.kernel-switcher",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", lambda app: KernelSwitcher(app).present())

def main():
    setup_logging()
    log.info("=== Roudix Kernel Switcher started ===")
    log.info("NH_FLAKE: %s", NH_FLAKE)
    log.info("CONFIG_FILE: %s", CONFIG_FILE)
    App().run(sys.argv)

if __name__ == "__main__":
    main()
