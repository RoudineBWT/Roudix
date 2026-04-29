#!/usr/bin/env python3
# roudix-kernel-switcher — GTK4/Adwaita GUI for kernel switching + SCX scheduler
# Writes hardware.myKernel directly into local.nix and runs nh os boot.
# SCX switching uses a single `pkexec scx-switch set/unset` call (one password
# prompt per action). scx-switch is a shell wrapper installed by gaming.nix that
# handles ananicy-cpp stop/start and scxctl in one shot.

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Pango

import os
import re
import shutil
import subprocess
import threading
import logging
import sys
import time

# ── Paths ─────────────────────────────────────────────────────────────────────

NH_FLAKE    = os.environ.get("NH_FLAKE", os.path.expanduser("~/.config/roudix"))
CONFIG_FILE = os.path.join(NH_FLAKE, "hosts", "roudix", "local.nix")

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# ── Logging ───────────────────────────────────────────────────────────────────

LOG_DIR  = os.path.expanduser("~/.local/share/roudix-kernel-switcher")
LOG_FILE = os.path.join(LOG_DIR, "switcher.log")
TMP_LOG  = "/tmp/roudix-kernel-switcher.log"

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

# ── Kernel catalogue ──────────────────────────────────────────────────────────

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

# ── SCX scheduler catalogue ───────────────────────────────────────────────────

SCX_PROFILES = ["Auto", "Gaming", "LowLatency", "PowerSave", "Server"]

# lowercase mode names passed to scxctl --mode and scx_* --mode
PROFILE_MODE = {
    "Auto":       None,
    "Gaming":     "gaming",
    "LowLatency": "lowlatency",
    "PowerSave":  "powersave",
    "Server":     "server",
}

SCX_SCHEDULERS = {
    "none":      ("None",      "Default kernel scheduler — CFS/EEVDF",                SCX_PROFILES[:1]),
    "bpfland":   ("bpfland",   "Best all-around — gaming, desktop, heavy load",        SCX_PROFILES),
    "lavd":      ("lavd",      "Low latency — gaming & interactive, autopilot mode",   SCX_PROFILES),
    "flash":     ("flash",     "Fairness-focused — good latency predictability",       SCX_PROFILES),
    "p2dq":      ("p2dq",      "Pull-based two-level queue — general purpose",         SCX_PROFILES),
    "rusty":     ("rusty",     "Rust-based — good scalability, no profiles",           SCX_PROFILES[:1]),
    "rustland":  ("rustland",  "Userspace Rust scheduler",                             SCX_PROFILES[:1]),
    "cosmos":    ("cosmos",    "Experimental — in active development",                 SCX_PROFILES[:1]),
    "beerland":  ("beerland",  "Experimental — in active development",                 SCX_PROFILES[:1]),
}

# ── SCX backend detection ─────────────────────────────────────────────────────

def has_scxctl() -> bool:
    return shutil.which("scxctl") is not None

def has_scx_switch() -> bool:
    return shutil.which("scx-switch") is not None

# ── Helpers ───────────────────────────────────────────────────────────────────

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
        log.info("Configuration updated: hardware.myKernel = '%s'.", kernel)
        return True
    except Exception as e:
        log.error("Failed to write configuration: %s", e)
        return str(e)


# ── SCX current state detection ───────────────────────────────────────────────

def get_current_scx_via_scxctl() -> tuple[str, str]:
    try:
        import json
        out = subprocess.check_output(
            ["scxctl", "status", "--json"],
            text=True, stderr=subprocess.DEVNULL
        )
        data  = json.loads(out)
        sched = data.get("scheduler", "").replace("scx_", "")
        mode  = data.get("mode", "auto")
        if sched not in SCX_SCHEDULERS:
            sched = "none"
        # normalise mode to our display names
        mode_map = {v: k for k, v in PROFILE_MODE.items() if v}
        profile = mode_map.get(mode.lower(), "Auto")
        return sched, profile
    except Exception:
        # fallback: plain text
        try:
            out = subprocess.check_output(
                ["scxctl", "status"], text=True, stderr=subprocess.DEVNULL
            )
            m = re.search(r"[Ss]cheduler[:\s]+scx_(\w+)", out)
            if m and m.group(1) in SCX_SCHEDULERS:
                return m.group(1), "Auto"
        except Exception:
            pass
        return "none", "Auto"


def get_current_scx_via_pgrep() -> tuple[str, str]:
    try:
        out = subprocess.check_output(
            ["pgrep", "-a", "-x", r"scx_\w+"],
            text=True, stderr=subprocess.DEVNULL
        )
        for line in out.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            m = re.match(r"scx_(\w+)$", parts[1])
            if not m or m.group(1) not in SCX_SCHEDULERS:
                continue
            name = m.group(1)
            profile = "Auto"
            try:
                idx      = parts.index("--mode")
                mode_val = parts[idx + 1]
                mode_map = {v: k for k, v in PROFILE_MODE.items() if v}
                profile  = mode_map.get(mode_val.lower(), "Auto")
            except (ValueError, IndexError):
                pass
            return name, profile
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return "none", "Auto"


def get_current_scx() -> tuple[str, str]:
    if has_scxctl():
        return get_current_scx_via_scxctl()
    return get_current_scx_via_pgrep()


# ── SCX apply — single pkexec call via scx-switch ────────────────────────────
#
# scx-switch is a shell script installed by gaming.nix that runs as root and
# does everything in one shot:
#   scx-switch set <scheduler> [mode]  → stop ananicy, start scx-loader + scxctl
#   scx-switch unset                   → stop scxctl + scx-loader, start ananicy
#
# One pkexec = one password prompt, regardless of DE.
# Falls back to direct scxctl calls if scx-switch is not installed.

def apply_scx(scheduler: str, profile: str) -> tuple[bool, str]:
    if has_scx_switch():
        return _apply_via_scx_switch(scheduler, profile)
    if has_scxctl():
        log.warning("scx-switch not found — falling back to individual scxctl calls.")
        return _apply_via_scxctl(scheduler, profile)
    log.warning("Neither scx-switch nor scxctl found — falling back to direct binary.")
    return _apply_via_binary(scheduler, profile)


def _apply_via_scx_switch(scheduler: str, profile: str) -> tuple[bool, str]:
    try:
        if scheduler == "none":
            cmd = ["pkexec", "scx-switch", "unset"]
        else:
            cmd = ["pkexec", "scx-switch", "set", scheduler]
            mode = PROFILE_MODE.get(profile)
            if mode:
                cmd.append(mode)
        log.info("Running: %s", " ".join(cmd))
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            if scheduler == "none":
                return True, "SCX stopped — using default CFS/EEVDF. ananicy-cpp restarted."
            return True, f"scx_{scheduler} started ({profile} mode). ananicy-cpp stopped."
        err = strip_ansi((r.stderr or r.stdout).strip())
        log.error("scx-switch failed: %s", err)
        return False, err or f"scx-switch exited {r.returncode}"
    except FileNotFoundError:
        return False, "scx-switch not found in PATH."
    except Exception as e:
        return False, str(e)


def _apply_via_scxctl(scheduler: str, profile: str) -> tuple[bool, str]:
    """Fallback when scx-switch is not installed. Three separate pkexec calls."""
    try:
        if scheduler == "none":
            r = subprocess.run(
                ["pkexec", "scxctl", "stop"],
                capture_output=True, text=True
            )
        else:
            cmd = ["pkexec", "scxctl", "start", "--sched", f"scx_{scheduler}"]
            mode = PROFILE_MODE.get(profile)
            if mode:
                cmd += ["--mode", mode]
            r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            if scheduler == "none":
                return True, "SCX stopped — using default CFS/EEVDF."
            return True, f"scx_{scheduler} started ({profile} mode)."
        err = strip_ansi((r.stderr or r.stdout).strip())
        log.error("scxctl failed: %s", err)
        return False, err or f"scxctl exited {r.returncode}"
    except FileNotFoundError:
        return False, "scxctl not found in PATH."
    except Exception as e:
        return False, str(e)


def _apply_via_binary(scheduler: str, profile: str) -> tuple[bool, str]:
    """Last-resort fallback: kill running scx_* binary and start a new one."""
    # stop any running scheduler first
    try:
        subprocess.run(["pkexec", "pkill", "-TERM", "-f", r"scx_\w+"],
                       capture_output=True)
    except Exception as e:
        log.warning("pkill fallback failed: %s", e)

    if scheduler == "none":
        return True, "SCX stopped — using default CFS/EEVDF."

    binary = f"scx_{scheduler}"
    path = shutil.which(binary)
    if not path:
        return False, f"{binary} not found in PATH — is scx.full installed?"

    cmd = ["pkexec", path]
    mode = PROFILE_MODE.get(profile)
    if mode and len(SCX_SCHEDULERS[scheduler][2]) > 1:
        cmd += ["--mode", mode]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                start_new_session=True)
        time.sleep(0.6)
        rc = proc.poll()
        if rc is not None:
            err = proc.stderr.read().decode(errors="replace").strip()
            return False, strip_ansi(err) or f"{binary} exited immediately (rc={rc})"
        log.info("%s started (pid=%d, profile=%s).", binary, proc.pid, profile)
        return True, f"{binary} started ({profile} mode)."
    except Exception as e:
        return False, str(e)


# ── ananicy status (read-only, no set_ananicy needed anymore) ─────────────────

def is_ananicy_active() -> bool:
    try:
        r = subprocess.run(["systemctl", "is-active", "ananicy-cpp"],
                           capture_output=True, text=True)
        return r.stdout.strip() == "active"
    except Exception:
        return False


# ── Kernel page ───────────────────────────────────────────────────────────────

class KernelPage(Gtk.Box):
    def __init__(self, window: "KernelSwitcher"):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._win      = window
        self._current  = detect_current_kernel()
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

        if self._current:
            banner = Adw.ActionRow()
            banner.set_title("Active kernel")
            banner.set_subtitle(self._current)
            banner.add_css_class("card")
            banner.set_margin_bottom(16)
            body.append(banner)

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
                check.set_group(self._anchor)
                check.set_valign(Gtk.Align.CENTER)
                if variant == self._current:
                    check.set_active(True)
                check.connect("toggled", self._on_toggled, variant)
                row.add_prefix(check)
                row.set_activatable_widget(check)
                lb.append(row)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(sep)

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.set_margin_top(12)
        bar.set_margin_bottom(12)
        bar.set_margin_start(16)
        bar.set_margin_end(16)
        self.append(bar)

        self._status_lbl = Gtk.Label(label="Select a kernel variant above.")
        self._status_lbl.set_hexpand(True)
        self._status_lbl.set_halign(Gtk.Align.START)
        self._status_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self._status_lbl.add_css_class("dim-label")
        bar.append(self._status_lbl)

        self._apply_btn = Gtk.Button(label="Apply & Rebuild")
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
        dialog.connect("response", self._on_confirm)
        dialog.present(self._win)

    def _on_confirm(self, dialog, response):
        if response != "confirm":
            return
        result = set_kernel(self._selected)
        if result is not True:
            self._status_lbl.set_label(f"✗ Error writing config: {result}")
            return
        self._apply_btn.set_sensitive(False)
        self._status_lbl.set_label("Building…")
        self._log_buf.set_text("")
        self._term_line("=" * 50, "section")
        self._term_line("Important Notices:", "section")
        self._term_line("=" * 50, "section")
        self._term_line("No issues currently reported.", "info")
        self._term_line("", "dim")
        self._term_line("=" * 50, "section")
        if self._pulse_source is None:
            self._pulse_source = GLib.timeout_add(80, self._do_pulse)
        threading.Thread(target=self._run_rebuild, daemon=True).start()

    def _run_rebuild(self):
        cmd_str = f"Running: nh os boot --elevation-strategy pkexec --accept-flake-config {NH_FLAKE}"
        log.info(cmd_str)
        GLib.idle_add(self._term_line, cmd_str, "dim")
        GLib.idle_add(self._term_line, "Checking repositories...", "dim")
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
            GLib.idle_add(self._term_line, "ERROR: 'nh' not found in PATH.", "error")
            rc = 127
        except Exception as e:
            GLib.idle_add(self._term_line, f"ERROR: {e}", "error")
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
            self._current = kernel
            self._status_lbl.set_label(f"✓ Done — reboot to apply {kernel}.")
            self._term_line("", "dim")
            self._term_line("✓ Rebuild completed successfully. Reboot to apply changes.", "ok")
        else:
            self._status_lbl.set_label(f"✗ Build failed (exit {rc}). See log.")
            self._term_line("", "dim")
            self._term_line(f"✗ Rebuild failed (exit code {rc}).", "error")
            self._apply_btn.set_sensitive(True)


# ── Scheduler page ────────────────────────────────────────────────────────────

class SchedulerPage(Gtk.Box):
    def __init__(self, window: "KernelSwitcher"):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._win = window

        self._scx_current, self._scx_profile_current = get_current_scx()
        self._scx_selected = self._scx_current
        self._scx_profile  = self._scx_profile_current

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

        # active scheduler banner
        self._active_banner = Adw.ActionRow()
        self._active_banner.set_title("Active scheduler")
        self._active_banner.set_subtitle(self._active_subtitle())
        self._active_banner.add_css_class("card")
        self._active_banner.set_margin_bottom(8)
        body.append(self._active_banner)

        # backend info
        if has_scx_switch():
            backend_label = "scx-switch + scxctl"
        elif has_scxctl():
            backend_label = "scxctl  —  install scx-switch for single password prompt"
        else:
            backend_label = "direct binary  —  scxctl not found"

        backend_row = Adw.ActionRow()
        backend_row.set_title("Backend")
        backend_row.set_subtitle(backend_label)
        backend_row.add_css_class("card")
        backend_row.set_margin_bottom(16)
        body.append(backend_row)

        # scheduler list
        scx_lb = Gtk.ListBox()
        scx_lb.set_selection_mode(Gtk.SelectionMode.NONE)
        scx_lb.add_css_class("boxed-list")
        scx_lb.set_margin_bottom(8)
        body.append(scx_lb)

        self._scx_anchor = Gtk.CheckButton()
        self._scx_checks: dict[str, Gtk.CheckButton] = {}

        for sched_id, (name, desc, _profiles) in SCX_SCHEDULERS.items():
            row = Adw.ActionRow()
            row.set_title(name)
            row.set_subtitle(desc)
            check = Gtk.CheckButton()
            check.set_group(self._scx_anchor)
            check.set_valign(Gtk.Align.CENTER)
            if sched_id == self._scx_current:
                check.set_active(True)
            check.connect("toggled", self._on_scx_toggled, sched_id)
            row.add_prefix(check)
            row.set_activatable_widget(check)
            scx_lb.append(row)
            self._scx_checks[sched_id] = check

        # profile row
        profile_row = Adw.ActionRow()
        profile_row.set_title("Profile")
        profile_row.set_subtitle("Scheduler mode — bpfland, lavd, flash and p2dq only")
        self._profile_combo = Gtk.DropDown()
        self._profile_combo.set_model(Gtk.StringList.new(SCX_PROFILES))
        self._profile_combo.set_valign(Gtk.Align.CENTER)
        if self._scx_profile_current in SCX_PROFILES:
            self._profile_combo.set_selected(SCX_PROFILES.index(self._scx_profile_current))
        _, _, cur_profiles = SCX_SCHEDULERS.get(self._scx_current, ("", "", SCX_PROFILES[:1]))
        self._profile_combo.set_sensitive(len(cur_profiles) > 1)
        self._profile_combo.connect("notify::selected", self._on_profile_changed)
        profile_row.add_suffix(self._profile_combo)
        scx_lb.append(profile_row)

        # ananicy status (read-only info, managed by scx-switch)
        self._ananicy_row = Adw.ActionRow()
        self._ananicy_row.set_title("ananicy-cpp")
        self._ananicy_row.add_css_class("card")
        self._ananicy_row.set_margin_top(8)
        self._ananicy_row.set_margin_bottom(8)
        self._refresh_ananicy_subtitle()
        body.append(self._ananicy_row)

        # bottom bar
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(sep)

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.set_margin_top(12)
        bar.set_margin_bottom(12)
        bar.set_margin_start(16)
        bar.set_margin_end(16)
        self.append(bar)

        self._status_lbl = Gtk.Label(label="Select a scheduler above.")
        self._status_lbl.set_hexpand(True)
        self._status_lbl.set_halign(Gtk.Align.START)
        self._status_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self._status_lbl.add_css_class("dim-label")
        bar.append(self._status_lbl)

        self._apply_btn = Gtk.Button(label="Apply Scheduler")
        self._apply_btn.add_css_class("suggested-action")
        self._apply_btn.set_sensitive(False)
        self._apply_btn.connect("clicked", self._on_apply)
        bar.append(self._apply_btn)

    def _active_subtitle(self) -> str:
        if self._scx_current == "none":
            return "None — CFS/EEVDF"
        label = SCX_SCHEDULERS.get(self._scx_current, (self._scx_current, "", []))[0]
        return f"{label}  •  {self._scx_profile_current}"

    def _refresh_ananicy_subtitle(self):
        active = is_ananicy_active()
        if active:
            self._ananicy_row.set_subtitle(
                "Running — will be stopped automatically when a SCX scheduler is applied"
            )
        else:
            self._ananicy_row.set_subtitle(
                "Stopped — will be restarted automatically when switching back to None"
            )

    def _on_scx_toggled(self, check, sched_id):
        if not check.get_active():
            return
        self._scx_selected = sched_id
        _, _, profiles = SCX_SCHEDULERS[sched_id]
        has_profiles = len(profiles) > 1
        self._profile_combo.set_sensitive(has_profiles)
        if not has_profiles:
            self._profile_combo.set_selected(0)
            self._scx_profile = "Auto"

        changed = (sched_id != self._scx_current or
                   self._scx_profile != self._scx_profile_current)
        self._apply_btn.set_sensitive(changed)

        ananicy_active = is_ananicy_active()
        ananicy_note = ""
        if sched_id == "none" and not ananicy_active:
            ananicy_note = " — ananicy-cpp will be restarted."
        elif sched_id != "none" and ananicy_active:
            ananicy_note = " — ananicy-cpp will be stopped."

        if sched_id == "none":
            self._status_lbl.set_label(f"Will stop SCX scheduler.{ananicy_note}")
        else:
            self._status_lbl.set_label(
                f"Will start scx_{sched_id} ({self._scx_profile}).{ananicy_note}"
            )

    def _on_profile_changed(self, combo, _param):
        idx = combo.get_selected()
        self._scx_profile = SCX_PROFILES[idx] if idx < len(SCX_PROFILES) else "Auto"
        changed = (self._scx_selected != self._scx_current or
                   self._scx_profile != self._scx_profile_current)
        self._apply_btn.set_sensitive(changed)

    def _on_apply(self, _btn):
        self._apply_btn.set_sensitive(False)
        self._status_lbl.set_label("Applying scheduler…")
        threading.Thread(target=self._run_apply, daemon=True).start()

    def _run_apply(self):
        ok, msg = apply_scx(self._scx_selected, self._scx_profile)
        GLib.idle_add(self._finish, ok, f"{'✓' if ok else '✗'} {msg}")

    def _finish(self, ok: bool, msg: str):
        self._status_lbl.set_label(msg)
        if ok:
            self._scx_current         = self._scx_selected
            self._scx_profile_current = self._scx_profile
            self._active_banner.set_subtitle(self._active_subtitle())
        else:
            self._apply_btn.set_sensitive(True)
        self._refresh_ananicy_subtitle()


# ── Main window ───────────────────────────────────────────────────────────────

class KernelSwitcher(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Kernel Switcher")
        self.set_default_size(640, 780)

        self._stack = Adw.ViewStack()

        kernel_page = KernelPage(self)
        self._stack.add_titled_with_icon(
            kernel_page, "kernel", "Kernel",
            "preferences-system-symbolic"
        )

        sched_page = SchedulerPage(self)
        self._stack.add_titled_with_icon(
            sched_page, "scheduler", "Scheduler",
            "utilities-system-monitor-symbolic"
        )

        header = Adw.HeaderBar()
        title_widget = Adw.ViewSwitcher()
        title_widget.set_stack(self._stack)
        title_widget.set_policy(Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(title_widget)

        switcher_bar = Adw.ViewSwitcherBar()
        switcher_bar.set_stack(self._stack)
        switcher_bar.set_reveal(True)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.append(header)
        root.append(self._stack)
        root.append(switcher_bar)
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
    log.info("scxctl available: %s", has_scxctl())
    log.info("scx-switch available: %s", has_scx_switch())
    App().run(sys.argv)

if __name__ == "__main__":
    main()
