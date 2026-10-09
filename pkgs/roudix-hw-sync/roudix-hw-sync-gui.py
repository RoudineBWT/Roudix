#!/usr/bin/env python3
# roudix-hw-sync-gui — GTK4/Adwaita front-end for roudix-hw-sync.
# Changed your PC? Re-detects CPU/GPU and updates hardware.myGpu / myCpu /
# nvidiaLaptop (+ kernel toggle, PRIME bus IDs, AMD undervolt) in local.nix.
# All the logic lives in the roudix-hw-sync CLI, this app only drives it.

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, Pango

import os
import re
import shutil
import socket
import subprocess
import sys
import threading

NH_FLAKE    = os.environ.get("NH_FLAKE", os.path.expanduser("~/.config/roudix"))
ROUDIX_HOST = os.environ.get("ROUDIX_HOST") or socket.gethostname()
CONFIG_FILE = os.path.join(NH_FLAKE, "hosts", ROUDIX_HOST, "local.nix")

# The CLI is installed next to this app (gappsWrapper keeps it in the same bin/).
_here = os.path.dirname(os.path.realpath(__file__))
CORE = os.path.join(_here, "roudix-hw-sync")
if not os.path.exists(CORE):
    CORE = shutil.which("roudix-hw-sync") or "roudix-hw-sync"

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

CPUS = [("amd", "AMD"), ("intel", "Intel")]
GPUS = [
    ("amd",        "AMD — modern (RDNA / GCN 3+, RX 400 and newer)"),
    ("amd-igpu",   "AMD — integrated (Ryzen APU)"),
    ("amd-legacy", "AMD — legacy (GCN 1.x / 2.x, HD 7xxx, R9 2xx)"),
    ("nvidia",     "NVIDIA"),
    ("intel",      "Intel (integrated or Arc)"),
]


def run_core(*args):
    """Run the CLI on the host's local.nix. Returns (rc, stdout, stderr)."""
    try:
        p = subprocess.run([CORE, "-f", CONFIG_FILE, *args],
                           capture_output=True, text=True, timeout=60)
        return p.returncode, p.stdout, p.stderr.strip()
    except Exception as e:  # missing binary, timeout…
        return 127, "", str(e)


def detect():
    rc, out, err = run_core("--detect")
    if rc != 0:
        return None, err or "Detection failed."
    return dict(l.split("=", 1) for l in out.splitlines() if "=" in l), ""


class HwSyncWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Hardware Sync")
        self.set_default_size(640, 800)
        self._loading = True
        self._busy = False
        self._changes = 0
        self._error = False

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.append(Adw.HeaderBar())
        self.set_content(root)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        root.append(scroll)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        for side in ("top", "bottom", "start", "end"):
            getattr(body, f"set_margin_{side}")(16)
        scroll.set_child(body)

        intro = Gtk.Label(
            label="New PC, new graphics card or new processor? Roudix looks at your "
                  "hardware and updates your configuration to match. "
                  "Nothing is changed until you press a button below.")
        intro.set_wrap(True)
        intro.set_halign(Gtk.Align.START)
        intro.add_css_class("dim-label")
        body.append(intro)

        # ── Hardware rows ─────────────────────────────────────────────────
        group = Adw.PreferencesGroup(title="Your hardware")
        body.append(group)

        self._cpu_row = Adw.ComboRow(title="Processor (CPU)")
        self._cpu_row.set_model(Gtk.StringList.new([l for _, l in CPUS]))
        self._cpu_row.connect("notify::selected", self._on_changed)
        group.add(self._cpu_row)

        self._gpu_row = Adw.ComboRow(title="Graphics card (GPU)")
        self._gpu_row.set_model(Gtk.StringList.new([l for _, l in GPUS]))
        self._gpu_row.connect("notify::selected", self._on_changed)
        group.add(self._gpu_row)

        self._laptop_row = Adw.SwitchRow(
            title="Laptop with an NVIDIA graphics card",
            subtitle="Hybrid graphics (Optimus): Intel/AMD chip + NVIDIA card")
        self._laptop_row.connect("notify::active", self._on_changed)
        group.add(self._laptop_row)

        # ── Status + preview ──────────────────────────────────────────────
        self._status = Adw.ActionRow(title="Checking…")
        self._status.add_css_class("card")
        body.append(self._status)

        self._expander = Adw.ExpanderRow(title="Preview of the changes")
        self._expander.add_css_class("card")
        self._diff_lbl = Gtk.Label(xalign=0, selectable=True)
        self._diff_lbl.set_wrap(False)
        self._diff_lbl.add_css_class("monospace")
        self._diff_lbl.set_margin_top(8)
        self._diff_lbl.set_margin_bottom(8)
        self._diff_lbl.set_margin_start(12)
        self._diff_lbl.set_margin_end(12)
        diff_scroll = Gtk.ScrolledWindow()
        diff_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        diff_scroll.set_child(self._diff_lbl)
        diff_row = Adw.PreferencesRow()
        diff_row.set_child(diff_scroll)
        self._expander.add_row(diff_row)
        body.append(self._expander)

        # ── Rebuild log (hidden until a rebuild starts) ───────────────────
        self._log_scroll = Gtk.ScrolledWindow()
        self._log_scroll.set_size_request(-1, 200)
        self._log_scroll.add_css_class("card")
        self._log_scroll.set_visible(False)
        self._log_tv = Gtk.TextView(editable=False, cursor_visible=False,
                                    monospace=True,
                                    wrap_mode=Gtk.WrapMode.WORD_CHAR)
        for side in ("left", "right", "top", "bottom"):
            getattr(self._log_tv, f"set_{side}_margin")(8)
        css = Gtk.CssProvider()
        css.load_from_string("textview.roudix-term, textview.roudix-term > text "
                             "{ background-color: @card_bg_color; color: @card_fg_color; }")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self._css_ref = css
        self._log_tv.add_css_class("roudix-term")
        self._log_buf = self._log_tv.get_buffer()
        for name, color in (("ok", "#a3be8c"), ("error", "#bf616a"),
                            ("warn", "#ebcb8b"), ("dim", None)):
            self._log_buf.create_tag(name, foreground=color)
        self._log_scroll.set_child(self._log_tv)
        body.append(self._log_scroll)

        # ── Bottom bar ────────────────────────────────────────────────────
        root.append(Gtk.Separator())
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        for side in ("top", "bottom", "start", "end"):
            getattr(bar, f"set_margin_{side}")(12)
        root.append(bar)

        self._rescan_btn = Gtk.Button(label="Re-detect")
        self._rescan_btn.connect("clicked", lambda _b: self._load())
        bar.append(self._rescan_btn)

        spacer = Gtk.Box(); spacer.set_hexpand(True); bar.append(spacer)

        self._save_btn = Gtk.Button(label="Apply")
        self._save_btn.set_tooltip_text("Only update local.nix, no rebuild")
        self._save_btn.connect("clicked", lambda _b: self._confirm(rebuild=False))
        bar.append(self._save_btn)

        self._build_btn = Gtk.Button(label="Apply & Rebuild")
        self._build_btn.add_css_class("suggested-action")
        self._build_btn.connect("clicked", lambda _b: self._confirm(rebuild=True))
        bar.append(self._build_btn)

        self._load()

    # ── State ─────────────────────────────────────────────────────────────
    def _selection(self):
        gpu = GPUS[self._gpu_row.get_selected()][0]
        cpu = CPUS[self._cpu_row.get_selected()][0]
        laptop = "true" if (gpu == "nvidia" and self._laptop_row.get_active()) else "false"
        return cpu, gpu, laptop

    def _load(self):
        """(Re)detect the hardware and fill the rows."""
        self._loading = True
        d, err = detect()
        if d is None:
            self._error = True
            self._status.set_title("Could not detect your hardware")
            self._status.set_subtitle(err)
            self._diff_lbl.set_label("")
            self._expander.set_visible(False)
            self._loading = False
            self._update_buttons()
            return
        self._error = False
        self._expander.set_visible(True)
        self._cpu_row.set_selected([c for c, _ in CPUS].index(d["cpu"]) if d["cpu"] in dict(CPUS) else 0)
        self._gpu_row.set_selected([g for g, _ in GPUS].index(d["gpu"]) if d["gpu"] in dict(GPUS) else 0)
        self._laptop_row.set_active(d.get("laptop") == "true")
        self._laptop_row.set_visible(d["gpu"] == "nvidia")
        self._loading = False
        self._refresh_preview()

    def _on_changed(self, *_a):
        if self._loading:
            return
        self._laptop_row.set_visible(self._selection()[1] == "nvidia")
        self._refresh_preview()

    def _refresh_preview(self):
        cpu, gpu, laptop = self._selection()
        rc, out, err = run_core("-n", "--cpu", cpu, "--gpu", gpu, "--laptop", laptop)
        if rc != 0:
            self._error = True
            self._status.set_title("Something went wrong")
            self._status.set_subtitle(err or out)
            self._update_buttons()
            return
        self._error = False
        lines = out.splitlines()
        start = next((i for i, l in enumerate(lines) if l.startswith("---")), None)
        diff = lines[start:] if start is not None else []
        diff = [l for l in diff if not l.startswith("(dry-run")]
        self._changes = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
        self._diff_lbl.set_label("\n".join(diff))
        self._expander.set_sensitive(bool(diff))
        if self._changes == 0:
            self._status.set_title("Your configuration already matches this hardware")
            self._expander.set_expanded(False)
        else:
            n = self._changes
            self._status.set_title(f"{n} line{'s' if n > 1 else ''} will be updated in local.nix")
        # surface CLI warnings (e.g. missing kernel line, undervolt note)
        self._status.set_subtitle(err)
        self._update_buttons()

    def _update_buttons(self):
        ok = not self._error and not self._busy
        self._save_btn.set_sensitive(ok and self._changes > 0)
        self._build_btn.set_sensitive(ok)
        self._rescan_btn.set_sensitive(not self._busy)
        for row in (self._cpu_row, self._gpu_row, self._laptop_row):
            row.set_sensitive(not self._busy)

    # ── Apply ─────────────────────────────────────────────────────────────
    def _confirm(self, rebuild):
        cpu, gpu, laptop = self._selection()
        dialog = Adw.AlertDialog()
        dialog.set_heading("Apply changes?")
        body = f"CPU: <b>{cpu}</b>\nGPU: <b>{gpu}</b>"
        if gpu == "nvidia":
            body += f"\nHybrid laptop: <b>{'yes' if laptop == 'true' else 'no'}</b>"
        body += "\n\nA backup of your settings is kept as <tt>local.nix.bak</tt>."
        if rebuild:
            body += "\nYour system will then be rebuilt, this can take a few minutes."
        dialog.set_body(body)
        dialog.set_body_use_markup(True)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("confirm", "Apply & Rebuild" if rebuild else "Apply")
        dialog.set_response_appearance("confirm", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("confirm")
        dialog.connect("response", self._on_confirm, rebuild)
        dialog.present(self)

    def _on_confirm(self, _dialog, response, rebuild):
        if response != "confirm":
            return
        cpu, gpu, laptop = self._selection()
        if self._changes > 0:
            rc, out, err = run_core("--cpu", cpu, "--gpu", gpu, "--laptop", laptop)
            if rc != 0:
                self._status.set_title("✗ Could not write local.nix")
                self._status.set_subtitle(err or out)
                return
        if not rebuild:
            self._refresh_preview()
            self._status.set_title("✓ local.nix updated — rebuild to apply")
            self._status.set_subtitle("Backup saved as local.nix.bak")
            return
        self._busy = True
        self._update_buttons()
        self._status.set_title("Rebuilding…")
        self._status.set_subtitle("")
        self._log_buf.set_text("")
        self._log_scroll.set_visible(True)
        threading.Thread(target=self._run_rebuild, daemon=True).start()

    def _run_rebuild(self):
        # "boot", not "switch": a GPU/driver change takes effect after a reboot.
        cmd = ["nh", "os", "boot", "--elevation-strategy", "pkexec",
               "--accept-flake-config", f"path:{NH_FLAKE}"]
        GLib.idle_add(self._log, "Running: " + " ".join(cmd), "dim")
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            buf = ""
            for ch in iter(lambda: proc.stdout.read(1), ""):
                if ch == "\r":
                    buf = ""
                elif ch == "\n":
                    line = ANSI_ESCAPE.sub("", buf).strip()
                    buf = ""
                    if line:
                        GLib.idle_add(self._log, line, self._tag(line))
                else:
                    buf += ch
            proc.wait()
            rc = proc.returncode
        except FileNotFoundError:
            GLib.idle_add(self._log, "ERROR: 'nh' not found in PATH.", "error")
            rc = 127
        except Exception as e:
            GLib.idle_add(self._log, f"ERROR: {e}", "error")
            rc = 1
        GLib.idle_add(self._finish, rc)

    @staticmethod
    def _tag(line):
        lo = line.lower()
        if any(w in lo for w in ("error", "failed", "✗")):  return "error"
        if "warn" in lo:                                    return "warn"
        if line.startswith(("Running", "Checking")):        return "dim"
        return None

    def _log(self, text, tag=None):
        buf = self._log_buf
        end = buf.get_end_iter()
        t = buf.get_tag_table().lookup(tag) if tag else None
        if t:
            buf.insert_with_tags(end, text + "\n", t)
        else:
            buf.insert(end, text + "\n")
        adj = self._log_scroll.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    def _finish(self, rc):
        self._busy = False
        if rc == 0:
            self._status.set_title("✓ Done — reboot to use your new hardware settings")
            self._log("", "dim")
            self._log("✓ Rebuild completed. Reboot to apply the changes.", "ok")
        else:
            self._status.set_title(f"✗ Rebuild failed (exit {rc})")
            self._status.set_subtitle("See the log below. Your local.nix was already updated.")
            self._log(f"✗ Rebuild failed (exit code {rc}).", "error")
        self._refresh_preview()


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.roudix.hw-sync",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", lambda app: HwSyncWindow(app).present())


if __name__ == "__main__":
    App().run(sys.argv)
