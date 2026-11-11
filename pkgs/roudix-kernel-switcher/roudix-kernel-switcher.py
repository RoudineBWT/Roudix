#!/usr/bin/env python3
# roudix-kernel-switcher — GTK4/Adwaita GUI for kernel switching.
# Writes hardware.myKernel directly into local.nix and runs nh os boot.
#
# SCX scheduler selection has been moved to its own app, roudix-scheduler
# (see roudix-scheduler.py), to avoid mixing the two responsibilities.

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Pango

import os
import re
import shutil
import socket
import subprocess
import threading
import logging
import sys
import time

# ── Paths ─────────────────────────────────────────────────────────────────────

NH_FLAKE    = os.environ.get("NH_FLAKE", os.path.expanduser("~/.config/roudix"))
# Multi-host: see roudix-switcher.py's ROUDIX_HOST comment — the machine's
# own hostname is also its hosts/<name>/ directory name.
ROUDIX_HOST = os.environ.get("ROUDIX_HOST") or socket.gethostname()
CONFIG_FILE = os.path.join(NH_FLAKE, "hosts", ROUDIX_HOST, "local.nix")

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# ── Logging ───────────────────────────────────────────────────────────────────

LOG_DIR  = os.path.expanduser("~/.local/share/roudix-kernel-switcher")
LOG_FILE = os.path.join(LOG_DIR, "switcher.log")
# Not in /tmp: a predictable world-writable path lets another local user plant a
# symlink there and make us truncate/overwrite one of our files. XDG_RUNTIME_DIR is
# private to the user (0700); fall back to the per-user log dir.
TMP_LOG = os.path.join(os.environ.get("XDG_RUNTIME_DIR") or LOG_DIR, "roudix-kernel-switcher.log")

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

log = logging.getLogger("roudix-kernel-switcher")

# ── translations (gettext) ───────────────────────────────────────────────────
# Messages are written in English: tr("…"). Catalogs live in po/<lang>.po and the Nix
# package compiles them to share/locale/<lang>/LC_MESSAGES/roudix-kernel-switcher.mo. The language
# comes from LANGUAGE / LC_ALL / LC_MESSAGES / LANG; a missing catalog falls back to English.
# Kernel names (cachyos-lto-v3, …) are never translated, only their descriptions.
import gettext as _gettext
import glob as _glob

_DOMAIN = "roudix-kernel-switcher"


def _find_localedir(domain):
    cands = [os.environ.get("ROUDIX_LOCALEDIR", "")]
    d = os.path.dirname(os.path.realpath(__file__))
    while True:
        cands += [os.path.join(d, "share", "locale"), os.path.join(d, "locale")]
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    for c in cands:
        if c and _glob.glob(os.path.join(c, "*", "LC_MESSAGES", domain + ".mo")):
            return c
    return None


_translation = _gettext.translation(_DOMAIN, _find_localedir(_DOMAIN), fallback=True)
tr = _translation.gettext          # tr("text")


# ── Kernel catalogue ──────────────────────────────────────────────────────────

KERNELS = {
    "Nixpkgs": [
        ("zen",             tr("linux-zen — mainline nixpkgs kernel, cached on cache.nixos.org, independent of the xddxdd overlay")),
        ("nixpkgs-lts",     tr("linux LTS — nixpkgs default kernel, cached on cache.nixos.org")),
        ("nixpkgs-latest",  tr("linux latest — newest mainline stable, cached on cache.nixos.org")),
        ("nixpkgs-testing", tr("linux_testing — mainline RC/testing kernel, cached on cache.nixos.org")),
        ("xanmod-lts",      tr("XanMod LTS — nixpkgs, performance governor + lazy preemption + BBRv3")),
        ("xanmod-latest",   tr("XanMod main branch — nixpkgs, newest XanMod")),
    ],
    "Latest": [
        ("cachyos-latest",          tr("Standard latest")),
        ("cachyos-latest-v3",       tr("x86_64-v3  —  recommended for modern CPUs")),
        ("cachyos-latest-v4",       "x86_64-v4  —  AVX-512"),
        ("cachyos-latest-zen4",     tr("AMD Zen 4 optimised")),
        ("cachyos-latest-lto",      "LTO"),
        ("cachyos-latest-lto-v3",   tr("LTO + v3  —  best perf on modern CPUs")),
        ("cachyos-latest-lto-v4",   "LTO + v4"),
        ("cachyos-latest-lto-zen4", "LTO + Zen 4"),
    ],
    "LTS": [
        ("cachyos-lts",             tr("Long-term support")),
        ("cachyos-lts-v3",          "LTS + v3"),
        ("cachyos-lts-v4",          "LTS + v4"),
        ("cachyos-lts-zen4",        "LTS + Zen 4"),
        ("cachyos-lts-lto",         "LTS + LTO"),
        ("cachyos-lts-lto-v3",      tr("LTS + LTO + v3  —  stable + performance")),
        ("cachyos-lts-lto-v4",      "LTS + LTO + v4"),
        ("cachyos-lts-lto-zen4",    "LTS + LTO + Zen 4"),
    ],
    "Variants": [
        ("cachyos-bore",            tr("BORE scheduler")),
        ("cachyos-bore-lto",        "BORE + LTO"),
        ("cachyos-bmq",             tr("BMQ scheduler")),
        ("cachyos-bmq-lto",         "BMQ + LTO"),
        ("cachyos-eevdf",           tr("EEVDF scheduler")),
        ("cachyos-eevdf-lto",       "EEVDF + LTO"),
        ("cachyos-hardened",        tr("Security hardened")),
        ("cachyos-hardened-lto",    tr("Hardened + LTO")),
        ("cachyos-rt-bore",         tr("Real-time + BORE")),
        ("cachyos-rt-bore-lto",     tr("Real-time + BORE + LTO")),
        ("cachyos-deckify",         tr("Steam Deck optimised")),
        ("cachyos-deckify-lto",     "Steam Deck + LTO"),
        ("cachyos-server",          tr("Server optimised")),
        ("cachyos-server-lto",      tr("Server + LTO")),
        ("cachyos-rc",              tr("Release candidate  —  unstable")),
        ("cachyos-rc-lto",          "RC + LTO"),
    ],
}

# Chaotic-Nyx — used only when hardware.myGpu == "nvidia" (ships
# nvidia_cachyos, the precompiled Nvidia driver matched to this kernel —
# deliberately no LTO here, more fragile on out-of-tree modules like nvidia)
KERNELS_CHAOTIC = {
    "Nixpkgs": [
        ("zen",             tr("linux-zen — nvidia module cached only with the open driver; "
                             "closed driver compiles locally on every bump")),
        ("nixpkgs-lts",     tr("linux LTS — same nvidia module caveat as zen")),
        ("nixpkgs-latest",  tr("linux latest — same nvidia module caveat as zen")),
        ("nixpkgs-testing", tr("linux_testing — mainline RC/testing kernel, same nvidia module caveat as zen")),
        ("xanmod-lts",      tr("XanMod LTS — same nvidia module caveat as zen")),
        ("xanmod-latest",   tr("XanMod main branch — same nvidia module caveat as zen")),
    ],
    "Chaotic-Nyx": [
        ("cachyos",          tr("Default  —  LTO + BORE, ships nvidia_cachyos")),
        ("cachyos-lts",      tr("Long-term support")),
        ("cachyos-server",   tr("Server optimised  —  no desktop tuning")),
        ("cachyos-hardened", tr("Security hardened")),
    ],
}


# Group headings (the dict keys above are identifiers and stay English)
GROUP_TITLES = {
    "Latest":   tr("Latest"),
    "Variants": tr("Variants"),
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)


def detect_current_gpu() -> str | None:
    try:
        text = open(CONFIG_FILE).read()
        m = re.search(r'hardware\.myGpu\s*=\s*"([^"]+)"', text)
        return m.group(1) if m else None
    except OSError:
        return None


def detect_nvidia_source() -> str:
    """hardware.nvidiaKernelSource: "chaotic" (default) or "xddxdd"."""
    try:
        text = open(CONFIG_FILE).read()
        m = re.search(r'^[ \t]*hardware\.nvidiaKernelSource\s*=\s*"([^"]+)"', text, re.M)
        return "xddxdd" if (m and m.group(1) == "xddxdd") else "chaotic"
    except OSError:
        return "chaotic"


def detect_nvidia_beta() -> bool:
    """hardware.nvidiaBeta (active line only, default false)."""
    try:
        text = open(CONFIG_FILE).read()
        m = re.search(r'^[ \t]*hardware\.nvidiaBeta\s*=\s*(true|false)', text, re.M)
        return bool(m and m.group(1) == "true")
    except OSError:
        return False


def detect_current_kernel(is_nvidia: bool) -> str | None:
    """is_nvidia = "reads the Chaotic-Nyx key" (nvidia and source == chaotic)."""
    key = "myKernelChaotic" if is_nvidia else "myKernel"
    try:
        text = open(CONFIG_FILE).read()
        m = re.search(rf'hardware\.{key}\s*=\s*"([^"]+)"', text)
        return m.group(1) if m else None
    except OSError:
        return None


def _set_option_text(content: str, key: str, literal: str) -> str:
    """Set `hardware.<key> = <literal>;` in a local.nix text: replace the active
    line, else uncomment a commented one, else add it before the last `}`."""
    active = re.compile(rf'^([ \t]*hardware\.{key}[ \t]*=[ \t]*)[^;\n]*;', re.M)
    if active.search(content):
        return active.sub(lambda m: f"{m.group(1)}{literal};", content, count=1)
    commented = re.compile(rf'^([ \t]*)#[ \t]*(hardware\.{key}[ \t]*=[ \t]*)[^;\n]*;', re.M)
    if commented.search(content):
        return commented.sub(lambda m: f"{m.group(1)}{m.group(2)}{literal};", content, count=1)
    idx = content.rstrip().rfind("}")
    if idx == -1:
        return content
    return content[:idx] + f"  hardware.{key} = {literal};\n" + content[idx:]


def write_config(kernel: str | None, chaotic: bool, gpu_nvidia: bool,
                 source: str, beta: bool) -> bool | str:
    """One write for everything: the kernel key, and on nvidia hosts the
    kernel source and beta-driver options."""
    try:
        with open(CONFIG_FILE) as f:
            content = f.read()
        if gpu_nvidia:
            content = _set_option_text(content, "nvidiaKernelSource", f'"{source}"')
            content = _set_option_text(content, "nvidiaBeta", "true" if beta else "false")
            # Only one of myKernel / myKernelChaotic should be active at a time
            other = "myKernel" if chaotic else "myKernelChaotic"
            content = re.sub(rf'^([ \t]*)(hardware\.{other}[ \t]*=)',
                             lambda m: f"{m.group(1)}# {m.group(2)}", content, flags=re.M)
        if kernel:
            key = "myKernelChaotic" if chaotic else "myKernel"
            content = _set_option_text(content, key, f'"{kernel}"')
        with open(CONFIG_FILE, "w") as f:
            f.write(content)
        log.info("Configuration updated: kernel=%s chaotic=%s source=%s beta=%s",
                 kernel, chaotic, source, beta)
        return True
    except Exception as e:
        log.error("Failed to write configuration: %s", e)
        return str(e)


# ── Kernel page ───────────────────────────────────────────────────────────────

class KernelPage(Gtk.Box):
    def __init__(self, window: "KernelSwitcher"):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._win      = window
        self._gpu_nvidia  = detect_current_gpu() == "nvidia"
        self._source      = detect_nvidia_source() if self._gpu_nvidia else "xddxdd"
        self._beta        = detect_nvidia_beta() if self._gpu_nvidia else False
        self._orig_source = self._source
        self._orig_beta   = self._beta
        # "_is_nvidia" = "uses the Chaotic-Nyx catalogue" (nvidia host that did
        # not opt into hardware.nvidiaKernelSource = "xddxdd")
        self._is_nvidia = self._gpu_nvidia and self._source == "chaotic"
        self._catalogue = KERNELS_CHAOTIC if self._is_nvidia else KERNELS
        self._active_kernel = detect_current_kernel(self._is_nvidia)
        self._current  = self._active_kernel
        self._selected = self._current
        self._anchor   = Gtk.CheckButton()

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.append(scroll)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        body.set_margin_top(16)
        body.set_margin_bottom(16)
        body.set_margin_start(16)
        body.set_margin_end(16)
        scroll.set_child(body)

        self._source_note = Gtk.Label(
            label=tr("Kernel source: {source}").format(source=self._source_label()))
        self._source_note.set_halign(Gtk.Align.START)
        self._source_note.add_css_class("dim-label")
        self._source_note.add_css_class("caption")
        self._source_note.set_margin_bottom(8)
        body.append(self._source_note)

        if self._gpu_nvidia:
            self._nvidia_note = Gtk.Label(label=self._nvidia_note_text())
            self._nvidia_note.set_halign(Gtk.Align.START)
            self._nvidia_note.set_wrap(True)
            self._nvidia_note.add_css_class("dim-label")
            self._nvidia_note.add_css_class("caption")
            self._nvidia_note.set_margin_bottom(12)
            body.append(self._nvidia_note)

            opts_lbl = Gtk.Label(label=tr("Nvidia options").upper())
            opts_lbl.set_halign(Gtk.Align.START)
            opts_lbl.set_margin_bottom(4)
            opts_lbl.add_css_class("caption-heading")
            body.append(opts_lbl)

            opts = Gtk.ListBox()
            opts.set_selection_mode(Gtk.SelectionMode.NONE)
            opts.add_css_class("boxed-list")
            opts.set_margin_bottom(12)
            body.append(opts)

            self._src_row = Adw.ComboRow()
            self._src_row.set_title(tr("Kernel source"))
            self._src_row.set_subtitle(
                tr("Chaotic-Nyx: precompiled Nvidia module. "
                   "xddxdd: more kernels, Nvidia module built locally."))
            self._src_row.set_model(Gtk.StringList.new(["Chaotic-Nyx", "xddxdd"]))
            self._src_row.set_selected(0 if self._source == "chaotic" else 1)
            self._src_row.connect("notify::selected", self._on_source_changed)
            opts.append(self._src_row)

            self._beta_row = Adw.SwitchRow()
            self._beta_row.set_title(tr("Beta driver"))
            self._beta_row.set_subtitle(
                tr("Test the beta Nvidia driver. Always built locally, "
                   "so rebuilds take longer."))
            self._beta_row.set_active(self._beta)
            self._beta_row.connect("notify::active", self._on_beta_toggled)
            opts.append(self._beta_row)

        # The kernel list is rebuilt when the Nvidia kernel source changes
        self._cat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        body.append(self._cat_box)
        self._build_catalogue()

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(sep)

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.set_margin_top(12)
        bar.set_margin_bottom(12)
        bar.set_margin_start(16)
        bar.set_margin_end(16)
        self.append(bar)

        self._status_lbl = Gtk.Label(label=tr("Select a kernel variant above."))
        self._status_lbl.set_hexpand(True)
        self._status_lbl.set_halign(Gtk.Align.START)
        self._status_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self._status_lbl.add_css_class("dim-label")
        bar.append(self._status_lbl)

        self._apply_btn = Gtk.Button(label=tr("Apply & Rebuild"))
        self._apply_btn.add_css_class("suggested-action")
        self._apply_btn.set_sensitive(False)
        self._apply_btn.connect("clicked", self._on_apply)
        bar.append(self._apply_btn)

        # ── Integrated terminal ───────────────────────────────────────────
        term_scroll = Gtk.ScrolledWindow()
        term_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        term_scroll.set_size_request(-1, 180)
        term_scroll.set_margin_start(16)
        term_scroll.set_margin_end(16)
        term_scroll.set_margin_bottom(12)
        term_scroll.add_css_class("card")

        self._log_tv = Gtk.TextView()
        self._log_tv.set_editable(False)
        self._log_tv.set_cursor_visible(False)
        self._log_tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._log_tv.set_monospace(True)
        self._log_tv.set_left_margin(10)
        self._log_tv.set_right_margin(10)
        self._log_tv.set_top_margin(8)
        self._log_tv.set_bottom_margin(8)
        self._log_tv.add_css_class("roudix-term")

        # add_provider_for_display so CSS works inside a Gtk.Box subclass
        _css = Gtk.CssProvider()
        _css.load_from_string(
            "textview.roudix-term,"
            "textview.roudix-term > text {"
            "  background-color: @card_bg_color;"
            "  color: @card_fg_color;"
            "}"
        )
        from gi.repository import Gdk
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            _css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        self._css_ref = _css

        self._log_buf = self._log_tv.get_buffer()
        self._log_buf.create_tag("section", foreground="#5e81ac", weight=Pango.Weight.BOLD)
        self._log_buf.create_tag("info",    foreground=None)
        self._log_buf.create_tag("ok",      foreground="#a3be8c")
        self._log_buf.create_tag("error",   foreground="#bf616a")
        self._log_buf.create_tag("warn",    foreground="#ebcb8b")
        self._log_buf.create_tag("dim",     foreground=None, scale=0.85)

        self._pulse_source = None

        term_scroll.set_child(self._log_tv)
        self.append(term_scroll)

    def _source_label(self) -> str:
        return tr("Chaotic-Nyx (GPU: nvidia)") if self._is_nvidia else "xddxdd"

    def _nvidia_note_text(self) -> str:
        if self._is_nvidia:
            return tr("Nvidia GPU detected — only Chaotic-Nyx variants are shown, "
                      "so nvidia_cachyos (precompiled driver) stays matched to your kernel.")
        return tr("Nvidia GPU detected — these kernels build the Nvidia module locally, "
                  "so rebuilds take longer.")

    def _build_catalogue(self):
        child = self._cat_box.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self._cat_box.remove(child)
            child = nxt
        self._anchor = Gtk.CheckButton()

        if self._current:
            banner = Adw.ActionRow()
            banner.set_title(tr("Active kernel"))
            banner.set_subtitle(self._current)
            banner.add_css_class("card")
            banner.set_margin_bottom(16)
            self._cat_box.append(banner)

        for group_name, entries in self._catalogue.items():
            grp_lbl = Gtk.Label(label=GROUP_TITLES.get(group_name, group_name).upper())
            grp_lbl.set_halign(Gtk.Align.START)
            grp_lbl.set_margin_top(8)
            grp_lbl.set_margin_bottom(4)
            grp_lbl.add_css_class("caption-heading")
            self._cat_box.append(grp_lbl)

            lb = Gtk.ListBox()
            lb.set_selection_mode(Gtk.SelectionMode.NONE)
            lb.add_css_class("boxed-list")
            lb.set_margin_bottom(12)
            self._cat_box.append(lb)

            for variant, desc in entries:
                row = Adw.ActionRow()
                row.set_title(variant)
                row.set_subtitle(desc)
                check = Gtk.CheckButton()
                check.set_group(self._anchor)
                check.set_valign(Gtk.Align.CENTER)
                if variant == self._selected:
                    check.set_active(True)
                check.connect("toggled", self._on_toggled, variant)
                row.add_prefix(check)
                row.set_activatable_widget(check)
                lb.append(row)

    def _on_source_changed(self, row, _pspec):
        self._source = "chaotic" if row.get_selected() == 0 else "xddxdd"
        self._is_nvidia = self._source == "chaotic"
        self._catalogue = KERNELS_CHAOTIC if self._is_nvidia else KERNELS
        # The "active kernel" only makes sense for the source in the config;
        # on the other source the user has to pick one.
        self._current = self._active_kernel if self._source == self._orig_source else None
        self._selected = self._current
        self._nvidia_note.set_label(self._nvidia_note_text())
        self._source_note.set_label(
            tr("Kernel source: {source}").format(source=self._source_label()))
        self._build_catalogue()
        self._refresh_apply()

    def _on_beta_toggled(self, row, _pspec):
        self._beta = row.get_active()
        self._refresh_apply()

    def _refresh_apply(self):
        source_changed = self._gpu_nvidia and self._source != self._orig_source
        beta_changed = self._gpu_nvidia and self._beta != self._orig_beta
        kernel_changed = bool(self._selected) and self._selected != self._current
        if source_changed and not self._selected:
            can, msg = False, tr("Select a kernel variant above.")
        elif kernel_changed:
            can, msg = True, tr("Will switch to: {variant}").format(variant=self._selected)
        elif source_changed or beta_changed:
            can, msg = True, tr("Nvidia options changed.")
        elif self._selected:
            can, msg = False, tr("Already the active kernel.")
        else:
            can, msg = False, tr("Select a kernel variant above.")
        self._apply_btn.set_sensitive(can)
        self._status_lbl.set_label(msg)

    def _on_toggled(self, check, variant):
        if check.get_active():
            self._selected = variant
            self._refresh_apply()

    def _on_apply(self, _btn):
        if not self._apply_btn.get_sensitive():
            return
        shown = self._selected or self._active_kernel or "?"
        body = tr("Kernel: <b>{current}</b> → <b>{selected}</b>").format(
            current=self._active_kernel or "?", selected=shown)
        if self._gpu_nvidia and (self._source != self._orig_source
                                 or self._beta != self._orig_beta):
            body += "\n" + tr("Nvidia options: {source}, beta driver: {beta}").format(
                source=self._source, beta="✓" if self._beta else "✗")
        dialog = Adw.AlertDialog()
        dialog.set_heading(tr("Apply changes?"))
        dialog.set_body(
            body + "\n\n" +
            tr("Your NixOS configuration will be rebuilt. This may take a few minutes.")
        )
        dialog.set_body_use_markup(True)
        dialog.add_response("cancel", tr("Cancel"))
        dialog.add_response("confirm", tr("Apply & Rebuild"))
        dialog.set_response_appearance("confirm", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("confirm")
        dialog.connect("response", self._on_confirm)
        dialog.present(self._win)

    def _on_confirm(self, dialog, response):
        if response != "confirm":
            return
        result = write_config(self._selected, self._is_nvidia, self._gpu_nvidia,
                              self._source, self._beta)
        if result is not True:
            self._status_lbl.set_label(tr("✗ Error writing config: {error}").format(error=result))
            return
        self._apply_btn.set_sensitive(False)
        self._status_lbl.set_label(tr("Building…"))
        self._log_buf.set_text("")
        self._term_line("=" * 50, "section")
        self._term_line(tr("Important Notices:"), "section")
        self._term_line("=" * 50, "section")
        self._term_line(tr("No issues currently reported."), "info")
        self._term_line("", "dim")
        self._term_line("=" * 50, "section")
        if self._pulse_source is None:
            self._pulse_source = GLib.timeout_add(80, self._do_pulse)
        threading.Thread(target=self._run_rebuild, daemon=True).start()

    def _run_rebuild(self):
        cmd = f"nh os boot --elevation-strategy pkexec --accept-flake-config {NH_FLAKE}"
        log.info("Running: %s", cmd)   # the log file stays in English
        GLib.idle_add(self._term_line, tr("Running: {cmd}").format(cmd=cmd), "dim")
        GLib.idle_add(self._term_line, tr("Checking repositories..."), "dim")
        try:
            proc = subprocess.Popen(
                ["nh", "os", "boot",
                 "--elevation-strategy", "pkexec",
                 "--accept-flake-config", f"path:{NH_FLAKE}"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            _buf = ""
            for ch in iter(lambda: proc.stdout.read(1), ""):
                if ch == "\r":
                    _buf = ""
                elif ch == "\n":
                    line = strip_ansi(_buf).strip()
                    _buf = ""
                    if line:
                        log.info(line)
                        GLib.idle_add(self._term_line, line, self._pick_tag(line))
                else:
                    _buf += ch
            if _buf.strip():
                line = strip_ansi(_buf).strip()
                if line:
                    log.info(line)
                    GLib.idle_add(self._term_line, line, self._pick_tag(line))
            proc.wait()
            rc = proc.returncode
        except FileNotFoundError:
            GLib.idle_add(self._term_line, tr("ERROR: 'nh' not found in PATH."), "error")
            rc = 127
        except Exception as e:
            GLib.idle_add(self._term_line, tr("ERROR: {error}").format(error=e), "error")
            rc = 1
        GLib.idle_add(self._finish_rebuild, self._selected, rc)

    def _term_line(self, text: str, tag_name: str = "info"):
        buf = self._log_buf
        end = buf.get_end_iter()
        tag = buf.get_tag_table().lookup(tag_name)
        if tag:
            buf.insert_with_tags(end, text + "\n", tag)
        else:
            buf.insert(end, text + "\n")
        adj = self._log_tv.get_parent().get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    def _pick_tag(self, line: str) -> str:
        lo = line.lower()
        if line.startswith("="):                                          return "section"
        if any(w in lo for w in ("error", "failed", "✗", "fail")):       return "error"
        if any(w in lo for w in ("warning", "warn")):                     return "warn"
        if any(w in lo for w in ("done", "success", "✓", "completed", "ok")): return "ok"
        if line.startswith(("Running", "Checking")):                      return "dim"
        return "info"

    def _do_pulse(self):
        return True

    def _finish_rebuild(self, kernel, rc):
        if self._pulse_source is not None:
            GLib.source_remove(self._pulse_source)
            self._pulse_source = None
        if rc == 0:
            if kernel:
                self._active_kernel = kernel
            self._orig_source = self._source
            self._orig_beta = self._beta
            self._current = self._active_kernel
            self._status_lbl.set_label(
                tr("✓ Done — reboot to apply {kernel}.").format(kernel=self._active_kernel or "?"))
            self._term_line("", "dim")
            self._term_line(tr("✓ Rebuild completed successfully. Reboot to apply changes."), "ok")
        else:
            self._status_lbl.set_label(tr("✗ Build failed (exit {rc}). See log.").format(rc=rc))
            self._term_line("", "dim")
            self._term_line(tr("✗ Rebuild failed (exit code {rc}).").format(rc=rc), "error")
            self._apply_btn.set_sensitive(True)


# ── Main window ───────────────────────────────────────────────────────────────

class KernelSwitcher(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Kernel Switcher")
        self.set_default_size(640, 780)

        # SCX scheduler selection now lives in its own dedicated app,
        # roudix-scheduler (see scx.nix / roudix-scheduler.py).
        kernel_page = KernelPage(self)

        header = Adw.HeaderBar()

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.append(header)
        root.append(kernel_page)
        self.set_content(root)


# ── Application ───────────────────────────────────────────────────────────────

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
