#!/usr/bin/env python3
# roudix-kernel-switcher — GTK4/Adwaita GUI for kernel switching
# Writes hardware.myKernel directly into local.nix and runs nh os boot.
# Also manages SCX scheduler live (no reboot) via direct scx_* binaries.

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

NH_FLAKE     = os.environ.get("NH_FLAKE", os.path.expanduser("~/.config/roudix"))
CONFIG_FILE  = os.path.join(NH_FLAKE, "hosts", "roudix", "local.nix")
SCX_PID_FILE = "/tmp/roudix-scx.pid"

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
# (display_name, description, supported_profiles)
# Profiles map to --mode <value> for binaries that support it.

SCX_PROFILES = ["Auto", "Gaming", "LowLatency", "PowerSave", "Server"]

PROFILE_FLAG = {
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


# ── SCX helpers ───────────────────────────────────────────────────────────────

def _read_scx_pid() -> int | None:
    """Return saved SCX PID if the process is still alive, else None."""
    try:
        pid = int(open(SCX_PID_FILE).read().strip())
        os.kill(pid, 0)   # raises if dead
        return pid
    except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
        return None


def _write_scx_pid(pid: int):
    try:
        with open(SCX_PID_FILE, "w") as f:
            f.write(str(pid))
    except OSError as e:
        log.warning("Could not write SCX PID file: %s", e)


def _clear_scx_pid():
    try:
        os.unlink(SCX_PID_FILE)
    except FileNotFoundError:
        pass


def get_current_scx() -> tuple[str, str]:
    """
    Detect the running SCX scheduler by scanning processes for scx_* binaries.
    Returns (sched_id, profile) or ('none', 'Auto').
    """
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
                idx = parts.index("--mode")
                mode_val = parts[idx + 1]
                for p in SCX_PROFILES:
                    if p.lower() == mode_val.lower():
                        profile = p
                        break
            except (ValueError, IndexError):
                pass
            return name, profile
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return "none", "Auto"


def is_ananicy_active() -> bool:
    try:
        r = subprocess.run(
            ["systemctl", "is-active", "ananicy-cpp"],
            capture_output=True, text=True
        )
        return r.stdout.strip() == "active"
    except Exception:
        return False


def set_ananicy(enable: bool) -> bool:
    action = "start" if enable else "stop"
    try:
        subprocess.run(
            ["pkexec", "systemctl", action, "ananicy-cpp"],
            check=True, capture_output=True
        )
        log.info("ananicy-cpp %sed.", action)
        return True
    except subprocess.CalledProcessError as e:
        log.error("Failed to %s ananicy-cpp: %s", action, e)
        return False


def stop_scx() -> tuple[bool, str]:
    """Kill the running SCX scheduler process (if any)."""
    # Try saved PID first
    pid = _read_scx_pid()
    if pid:
        try:
            subprocess.run(["pkexec", "kill", "-TERM", str(pid)], check=True, capture_output=True)
            _clear_scx_pid()
            log.info("SCX scheduler (pid %d) stopped.", pid)
            return True, "SCX stopped — using default CFS/EEVDF."
        except subprocess.CalledProcessError as e:
            log.warning("kill via saved PID failed: %s — trying pkill fallback", e)

    # Fallback: pkill any running scx_* process
    try:
        r = subprocess.run(
            ["pkexec", "pkill", "-TERM", "-f", r"scx_\w+"],
            capture_output=True
        )
        # pkill returns 1 when no process matched — that's fine
    except Exception as e:
        log.warning("pkill fallback failed: %s", e)

    _clear_scx_pid()
    log.info("SCX scheduler stopped (or was not running).")
    return True, "SCX stopped — using default CFS/EEVDF."


def start_scx(scheduler: str, profile: str) -> tuple[bool, str]:
    """
    Launch scx_<scheduler> as a detached background process via pkexec.
    Passes --mode <profile> for schedulers that support it.
    """
    binary = f"scx_{scheduler}"
    path = shutil.which(binary)
    if not path:
        msg = f"{binary} not found in PATH — is scx.full installed?"
        log.error(msg)
        return False, msg

    cmd = ["pkexec", path]
    mode = PROFILE_FLAG.get(profile)
    if mode and len(SCX_SCHEDULERS[scheduler][2]) > 1:
        cmd += ["--mode", mode]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        # Short wait to catch immediate failures (e.g. sched_ext not in kernel)
        time.sleep(0.6)
        rc = proc.poll()
        if rc is not None:
            err = proc.stderr.read().decode(errors="replace").strip()
            msg = strip_ansi(err) or f"{binary} exited immediately (rc={rc})"
            log.error("scx start failed: %s", msg)
            return False, msg

        _write_scx_pid(proc.pid)
        log.info("%s started (pid=%d, profile=%s).", binary, proc.pid, profile)
        return True, f"{binary} started ({profile} mode)."
    except Exception as e:
        log.error("Failed to launch %s: %s", binary, e)
        return False, str(e)


def apply_scx(scheduler: str, profile: str) -> tuple[bool, str]:
    """Stop any running SCX scheduler, then start the requested one (unless 'none')."""
    ok, msg = stop_scx()
    if not ok:
        return False, msg
    if scheduler == "none":
        return True, "SCX stopped — using default CFS/EEVDF."
    return start_scx(scheduler, profile)


# ── Main window ───────────────────────────────────────────────────────────────

class KernelSwitcher(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Kernel Switcher")
        self.set_default_size(640, 820)

        self._selected: str | None = None
        self._current  = detect_current_kernel()
        self._group_anchor = Gtk.CheckButton()

        # SCX state
        self._scx_current, self._scx_profile_current = get_current_scx()
        self._scx_selected = self._scx_current
        self._scx_profile  = self._scx_profile_current
        self._ananicy_was_active = is_ananicy_active()

        # ── Root ──────────────────────────────────────────────────────────
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root)

        header = Adw.HeaderBar()
        root.append(header)

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

        # ── Active kernel banner ──────────────────────────────────────────
        if self._current:
            banner = Adw.ActionRow()
            banner.set_title("Active kernel")
            banner.set_subtitle(self._current)
            banner.add_css_class("card")
            banner.set_margin_bottom(16)
            body.append(banner)

        # ── Kernel groups ─────────────────────────────────────────────────
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

                check.connect("toggled", self._on_kernel_toggled, variant)
                row.add_prefix(check)
                row.set_activatable_widget(check)
                lb.append(row)

        # ── SCX section label ─────────────────────────────────────────────
        scx_lbl = Gtk.Label(label="SCX SCHEDULER  —  LIVE, NO REBOOT REQUIRED")
        scx_lbl.set_halign(Gtk.Align.START)
        scx_lbl.set_margin_top(16)
        scx_lbl.set_margin_bottom(4)
        scx_lbl.add_css_class("caption-heading")
        body.append(scx_lbl)

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

        # Profile row
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

        # ── ananicy-cpp status card ───────────────────────────────────────
        self._ananicy_row = Adw.ActionRow()
        self._ananicy_row.set_title("ananicy-cpp")
        self._ananicy_row.add_css_class("card")
        self._ananicy_row.set_margin_bottom(8)
        self._refresh_ananicy_subtitle()
        body.append(self._ananicy_row)

        # ── SCX apply row ─────────────────────────────────────────────────
        scx_btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        scx_btn_row.set_margin_bottom(16)
        body.append(scx_btn_row)

        self._scx_status_lbl = Gtk.Label(label="Select a scheduler above.")
        self._scx_status_lbl.set_hexpand(True)
        self._scx_status_lbl.set_halign(Gtk.Align.START)
        self._scx_status_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self._scx_status_lbl.add_css_class("dim-label")
        scx_btn_row.append(self._scx_status_lbl)

        self._scx_apply_btn = Gtk.Button(label="Apply Scheduler")
        self._scx_apply_btn.add_css_class("suggested-action")
        self._scx_apply_btn.set_sensitive(False)
        self._scx_apply_btn.connect("clicked", self._on_scx_apply)
        scx_btn_row.append(self._scx_apply_btn)

        # ── Kernel bottom bar ─────────────────────────────────────────────
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

        # ── Build log expander ────────────────────────────────────────────
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

    # ── ananicy subtitle ──────────────────────────────────────────────────

    def _refresh_ananicy_subtitle(self):
        active = is_ananicy_active()
        self._ananicy_was_active = active
        if active:
            self._ananicy_row.set_subtitle(
                "Running — will be stopped automatically when a SCX scheduler is applied"
            )
        else:
            self._ananicy_row.set_subtitle(
                "Stopped — will be restarted automatically when switching back to None"
            )

    # ── Kernel callbacks ──────────────────────────────────────────────────

    def _on_kernel_toggled(self, check, variant):
        if check.get_active():
            self._selected = variant
            changed = variant != self._current
            self._apply_btn.set_sensitive(changed)
            self._status_lbl.set_label(
                f"Will switch to: {variant}" if changed else "Already the active kernel.")

    # ── SCX callbacks ─────────────────────────────────────────────────────

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

        changed = (sched_id != self._scx_current or self._scx_profile != self._scx_profile_current)
        self._scx_apply_btn.set_sensitive(changed)

        ananicy_note = ""
        if sched_id == "none" and not self._ananicy_was_active:
            ananicy_note = " — ananicy-cpp will be restarted."
        elif sched_id != "none" and self._ananicy_was_active:
            ananicy_note = " — ananicy-cpp will be stopped."

        if sched_id == "none":
            self._scx_status_lbl.set_label(f"Will stop SCX scheduler.{ananicy_note}")
        else:
            self._scx_status_lbl.set_label(
                f"Will start scx_{sched_id} ({self._scx_profile}).{ananicy_note}"
            )

    def _on_profile_changed(self, combo, _param):
        idx = combo.get_selected()
        self._scx_profile = SCX_PROFILES[idx] if idx < len(SCX_PROFILES) else "Auto"
        changed = (self._scx_selected != self._scx_current or self._scx_profile != self._scx_profile_current)
        self._scx_apply_btn.set_sensitive(changed)

    def _on_scx_apply(self, _btn):
        self._scx_apply_btn.set_sensitive(False)
        self._scx_status_lbl.set_label("Applying scheduler…")
        threading.Thread(target=self._run_scx_apply, daemon=True).start()

    def _run_scx_apply(self):
        sched   = self._scx_selected
        profile = self._scx_profile

        # Stop ananicy-cpp before loading a SCX scheduler
        if sched != "none" and self._ananicy_was_active:
            log.info("Stopping ananicy-cpp before starting SCX scheduler.")
            set_ananicy(False)

        ok, msg = apply_scx(sched, profile)

        if not ok:
            # Restore ananicy if scx failed
            if sched != "none" and self._ananicy_was_active:
                set_ananicy(True)
            GLib.idle_add(self._scx_finish, False, f"✗ {msg}")
            return

        # Restart ananicy when going back to none
        if sched == "none":
            log.info("Restarting ananicy-cpp after stopping SCX scheduler.")
            set_ananicy(True)

        GLib.idle_add(self._scx_finish, True, f"✓ {msg}")

    def _scx_finish(self, ok: bool, msg: str):
        self._scx_status_lbl.set_label(msg)
        if ok:
            self._scx_current         = self._scx_selected
            self._scx_profile_current = self._scx_profile
        else:
            self._scx_apply_btn.set_sensitive(True)
        self._refresh_ananicy_subtitle()

    # ── Kernel apply ──────────────────────────────────────────────────────

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
