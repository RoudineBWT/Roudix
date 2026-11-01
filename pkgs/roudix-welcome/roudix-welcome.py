#!/usr/bin/env python3
import gi
import os
import sys
import logging
import re
import shlex
import shutil
import subprocess
import threading

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, Adw, GLib, Gio

# ── Paths ─────────────────────────────────────────────────────────────────────
LOG_DIR  = os.path.expanduser("~/.local/share/roudix-welcome")
LOG_FILE = os.path.join(LOG_DIR, "welcome.log")

# Read by the roudix-welcome.service ConditionPathExists=! check (see the
# roudix.welcome Home Manager module) — touching/removing this file is the
# only thing the "Show at startup" switch below does. It never touches
# systemd enablement itself, so the toggle survives `nh os switch` rebuilds
# instead of being fought by Home Manager re-linking the unit every time.
#
# NOTE: this must NOT live under ~/.config/roudix — that's the root of the
# git-cloned Roudix repo itself (the autoupdate/gitwatch "clone directly"
# model), so a marker there gets picked up and auto-committed by gitwatch.
# ~/.local/state is the correct XDG spot for this kind of per-user runtime
# state, and matches LOG_DIR above.
DISABLED_MARKER = os.path.expanduser("~/.local/state/roudix-welcome/disabled")

GITHUB_URL = "https://github.com/RoudineBWT/Roudix"
DOCS_URL   = GITHUB_URL + "#documentation"
ISSUES_URL = GITHUB_URL + "/issues"
RELEASES_URL = GITHUB_URL + "/releases"
# Optional community links: leave empty to hide the button.
YOUTUBE_URL = ""   # e.g. "https://www.youtube.com/@Roudine"
DISCORD_URL = ""   # e.g. "https://discord.gg/xxxx"

# Same default as roudix-kernel-switcher / roudix-scheduler.
NH_FLAKE = os.environ.get("NH_FLAKE", os.path.expanduser("~/.config/roudix"))

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


log = logging.getLogger("roudix-welcome")


# ── translations (gettext) ───────────────────────────────────────────────────
# Messages are written in English: tr("…"). Catalogs live in po/<lang>.po and the Nix
# package compiles them to share/locale/<lang>/LC_MESSAGES/roudix-welcome.mo. The language comes
# from LANGUAGE / LC_ALL / LC_MESSAGES / LANG; a missing catalog falls back to English.
import gettext as _gettext
import glob as _glob

_DOMAIN = "roudix-welcome"


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
tr = _translation.gettext        # tr("text")
trc = _translation.pgettext      # trc("context", "text")


def tr_noop(text):
    """Mark a string for extraction now, translate it later with tr()."""
    return text


def get_pretty_name() -> str:
    """Read PRETTY_NAME from /etc/os-release (set by version.nix) for the
    footer, e.g. 'Roudix 26.11'. Falls back to a plain 'Roudix' label if
    the file is missing or unreadable (e.g. running off-target for a
    quick UI check)."""
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return "Roudix"


def open_uri(uri: str):
    log.info("Opening %s", uri)
    try:
        Gio.AppInfo.launch_default_for_uri(uri, None)
    except GLib.Error:
        log.exception("Could not open %s", uri)


# ── Launcher catalogue ────────────────────────────────────────────────────────
# Each entry launches an already-installed Roudix app as a fully detached
# process (own session, stdout/stderr dropped) so closing roudix-welcome
# never takes the launched app down with it.
APPS = [
    {
        "id":       "roudix-store",
        "icon":     "io.roudix.store",
        "title":    tr("Software Store"),
        "subtitle": tr("Install nixpkgs and Flatpak apps"),
    },
    {
        "id":       "roudix-switcher",
        "icon":     "io.roudix.switcher",
        "title":    tr("Customizer"),
        "subtitle": tr("Desktop, shell, apps and system tweaks"),
    },
    {
        "id":       "roudix-kernel-switcher",
        "icon":     "io.roudix.kernel-switcher",
        "title":    tr("Kernel Switcher"),
        "subtitle": tr("Pick your CachyOS kernel variant"),
    },
    {
        # Binary/desktop id is "roudix-scheduler" (see
        # pkgs/roudix-scheduler-switcher/default.nix) even though the Nix
        # attribute/module is roudix-scheduler-switcher.
        "id":       "roudix-scheduler",
        "icon":     "io.roudix.scheduler",
        "title":    tr("SCX Scheduler"),
        "subtitle": tr("Choose and apply an SCX scheduler"),
    },
]

# Second group, "System tools". Not every machine has all of them (roudix-config
# only exists for Umbriel/Niri/MangoWC), so tiles whose binary is not on PATH
# are hidden instead of failing on click.
SYSTEM_APPS = [
    {
        "id":       "roudix-disk",
        "icon":     "io.roudix.disk",
        "title":    tr("Disks"),
        "subtitle": tr("Mount, format and manage your extra disks"),
    },
    {
        "id":       "roudix-firewall",
        "icon":     "io.roudix.firewall",
        "title":    tr("Firewall"),
        "subtitle": tr("Open ports and trusted interfaces"),
    },
    {
        "id":       "roudix-hw-sync-gui",
        "icon":     "io.roudix.hw-sync",
        "title":    tr("Hardware Sync"),
        "subtitle": tr("Changed PC? Update your CPU/GPU settings"),
    },
    {
        "id":       "roudix-config",
        "icon":     "io.roudix.config",
        "title":    tr("Compositor Config"),
        "subtitle": tr("Window rules, screens and shortcuts"),
    },
]

# Quick links shown under the tiles (CachyOS Hello style). Entries whose URL is
# empty are skipped.
LINKS = [
    (tr("Documentation"), "help-browser-symbolic",         DOCS_URL),
    (tr("Source code"),   "system-software-install-symbolic", GITHUB_URL),
    (tr("Release notes"), "starred-symbolic",              RELEASES_URL),
    (tr("Report a bug"),  "dialog-warning-symbolic",       ISSUES_URL),
    (tr("YouTube"),       "camera-video-symbolic",         YOUTUBE_URL),
    (tr("Discord"),       "chat-bubble-text-symbolic",     DISCORD_URL),
]

# Maintenance actions ("Tweaks" page), mirroring the shell aliases from
# docs/aliases.md:
#   update  -> roudix-update   (git pull + nh os switch + Flatpaks; runs `sudo -v`,
#                               i.e. needs a real tty -> opened in a terminal)
#   rebuild -> nh os switch    (pkexec instead of sudo: there is no tty in a GUI)
#   cleanup -> delete system generations +3 + nix-collect-garbage (via pkexec)
# mode "dialog" streams the output in RunDialog, "terminal" opens a terminal.
_SW = "/run/current-system/sw/bin"
TWEAKS = [
    {
        "icon":     "software-update-available-symbolic",
        "title":    tr("Check for updates"),
        "subtitle": tr("See if new commits are available (nothing is changed)"),
        "confirm":  None,
        "mode":     "dialog",
        "argv":     ["roudix-update", "--check"],
    },
    {
        "icon":     "system-software-update-symbolic",
        "title":    tr("Update system"),
        "subtitle": tr("Pull, rebuild, switch and update Flatpaks (same as `update`)"),
        "confirm":  tr("Open a terminal and run the update? You will be asked for your password."),
        "mode":     "terminal",
        "argv":     ["roudix-update"],
    },
    {
        "icon":     "view-refresh-symbolic",
        "title":    tr("Apply configuration"),
        "subtitle": tr("Rebuild and switch now (same as `rebuild`)"),
        "confirm":  tr("Rebuild the system now? This can take a while."),
        "mode":     "dialog",
        "argv":     ["nh", "os", "switch", "--elevation-strategy", "pkexec",
                     "--accept-flake-config", f"path:{NH_FLAKE}"],
    },
    {
        "icon":     "user-trash-symbolic",
        "title":    tr("Clean old generations"),
        "subtitle": tr("Keep the last 3 generations, then garbage-collect (same as `cleanup`)"),
        "confirm":  tr("Remove old system generations? You will not be able to roll back to them."),
        "mode":     "dialog",
        "argv":     ["pkexec", "sh", "-c",
                     f"{_SW}/nix-env --delete-generations +3 "
                     f"--profile /nix/var/nix/profiles/system && "
                     f"{_SW}/nix-collect-garbage"],
    },
    {
        "icon":     "text-x-generic-symbolic",
        "title":    tr("Show last update log"),
        "subtitle": tr("Output of the last run of `update`"),
        "confirm":  None,
        "mode":     "dialog",
        "argv":     ["roudix-update", "--log"],
    },
]

# Terminal emulators Roudix can ship (roudix.terminal) -> how to run a command in them.
TERMINALS = {
    "ghostty":        lambda c: ["ghostty", "-e", *c],
    "kitty":          lambda c: ["kitty", *c],
    "alacritty":      lambda c: ["alacritty", "-e", *c],
    "foot":           lambda c: ["foot", *c],
    "wezterm":        lambda c: ["wezterm", "start", "--", *c],
    "konsole":        lambda c: ["konsole", "-e", *c],
    "ptyxis":         lambda c: ["ptyxis", "--", *c],
    "gnome-terminal": lambda c: ["gnome-terminal", "--", *c],
    "xterm":          lambda c: ["xterm", "-e", *c],
}


def find_terminal():
    """$TERMINAL (set by the compositor modules) first, then the first one installed."""
    pref = os.path.basename(os.environ.get("TERMINAL", ""))
    for name in ([pref] if pref in TERMINALS else []) + list(TERMINALS):
        if shutil.which(name):
            return name
    return None


def run_in_terminal(argv: list[str]) -> bool:
    name = find_terminal()
    if name is None:
        log.error("No terminal emulator found")
        return False
    # Keep the window open at the end so the output can be read.
    inner = " ".join(shlex.quote(a) for a in argv)
    script = f'{inner}; echo; read -rp {shlex.quote(tr("Press Enter to close…"))} _'
    cmd = TERMINALS[name](["bash", "-c", script])
    log.info("Opening %s: %s", name, inner)
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        return True
    except OSError:
        log.exception("Could not start %s", name)
        return False


def launch(app_id: str):
    log.info("Launching %s", app_id)
    try:
        subprocess.Popen(
            [app_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except FileNotFoundError:
        log.exception("Could not find %s on PATH", app_id)


CSS = """
.roudix-tile {
    padding: 0;
    border-radius: 16px;
    transition: all 150ms ease;
}
.roudix-tile:hover {
    background-color: alpha(@accent_bg_color, 0.12);
}
.roudix-version-pill {
    padding: 2px 12px;
    border-radius: 999px;
    background-color: alpha(@accent_bg_color, 0.18);
    color: @accent_color;
    font-weight: bold;
}
.roudix-hero-title {
    font-size: 28pt;
    font-weight: 800;
}
.roudix-term {
    font-family: monospace;
    font-size: 10pt;
}
"""


def icon_or_fallback(name: str, fallback: str = "application-x-executable-symbolic") -> str:
    display = Gdk.Display.get_default()
    if display is not None and not Gtk.IconTheme.get_for_display(display).has_icon(name):
        return fallback
    return name


class RunDialog(Adw.Dialog):
    """Runs a command and streams its output (nh/flatpak) in a small log view."""

    def __init__(self, title: str, argv: list[str]):
        super().__init__()
        self._argv = argv
        self._running = True
        self.set_title(title)
        self.set_content_width(600)
        self.set_content_height(440)
        self.set_can_close(False)          # no closing mid-run

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        header.set_show_start_title_buttons(False)
        self._spinner = Gtk.Spinner(spinning=True)
        header.pack_start(self._spinner)
        self._close_btn = Gtk.Button(label=tr("Close"))
        self._close_btn.set_sensitive(False)
        self._close_btn.connect("clicked", lambda _b: self.force_close())
        header.pack_end(self._close_btn)
        toolbar.add_top_bar(header)

        self._buf = Gtk.TextBuffer()
        tv = Gtk.TextView(buffer=self._buf)
        tv.set_editable(False)
        tv.set_cursor_visible(False)
        tv.set_monospace(True)
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        tv.set_top_margin(8)
        tv.set_bottom_margin(8)
        tv.set_left_margin(12)
        tv.set_right_margin(12)
        tv.add_css_class("roudix-term")
        self._scroll = Gtk.ScrolledWindow()
        self._scroll.set_child(tv)
        self._scroll.set_vexpand(True)
        toolbar.set_content(self._scroll)

        self._status = Gtk.Label(label=tr("Running…"))
        self._status.add_css_class("dim-label")
        self._status.set_margin_top(6)
        self._status.set_margin_bottom(6)
        toolbar.add_bottom_bar(self._status)
        self.set_child(toolbar)

    def start(self):
        threading.Thread(target=self._worker, daemon=True).start()

    def _append(self, line: str):
        self._buf.insert(self._buf.get_end_iter(), line + "\n")
        adj = self._scroll.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False

    def _worker(self):
        cmd = " ".join(self._argv)
        log.info("Running: %s", cmd)
        GLib.idle_add(self._append, "$ " + cmd)
        rc = 1
        try:
            proc = subprocess.Popen(
                self._argv,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, errors="replace",
            )
            for raw in proc.stdout:
                # progress bars rewrite the line with \r: keep the last frame
                line = ANSI_RE.sub("", raw.rstrip("\n").split("\r")[-1]).rstrip()
                if line:
                    log.info(line)
                    GLib.idle_add(self._append, line)
            proc.wait()
            rc = proc.returncode
        except FileNotFoundError:
            GLib.idle_add(self._append, tr("ERROR: '{cmd}' not found in PATH.").format(cmd=self._argv[0]))
            rc = 127
        except Exception as e:                      # noqa: BLE001
            GLib.idle_add(self._append, tr("ERROR: {error}").format(error=e))
        GLib.idle_add(self._finish, rc)

    def _finish(self, rc: int):
        self._running = False
        self._spinner.set_spinning(False)
        self._status.set_label(
            tr("✓ Done") if rc == 0 else tr("✗ Failed (exit code {rc})").format(rc=rc)
        )
        self.set_can_close(True)
        self._close_btn.set_sensitive(True)
        return False


class RoudixWelcomeWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title(tr("Welcome to Roudix"))
        self.set_default_size(620, 760)
        self.set_size_request(360, 480)
        self.set_resizable(True)

        css = Gtk.CssProvider()
        css.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self._css_ref = css

        # ── Pages (Welcome / Tweaks), CachyOS Hello style ────────────────────
        self.stack = Adw.ViewStack()
        self.stack.add_titled_with_icon(
            self._wrap(self._build_welcome_page()), "welcome",
            tr("Welcome"), "go-home-symbolic")
        self.stack.add_titled_with_icon(
            self._wrap(self._build_tweaks_page()), "tweaks",
            tr("Tweaks"), "emblem-system-symbolic")

        switcher = Adw.ViewSwitcher()
        switcher.set_stack(self.stack)
        switcher.set_policy(Adw.ViewSwitcherPolicy.WIDE)

        header = Adw.HeaderBar()
        header.set_title_widget(switcher)

        bottom_bar = Adw.ViewSwitcherBar()
        bottom_bar.set_stack(self.stack)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(header)
        toolbar.set_content(self.stack)
        toolbar.add_bottom_bar(bottom_bar)
        self.set_content(toolbar)

        # Narrow window: header switcher → bottom bar
        bp = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 500sp"))
        bp.add_setter(header, "title-widget", None)
        bp.add_setter(bottom_bar, "reveal", True)
        self.add_breakpoint(bp)

    # ── helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def _wrap(child: Gtk.Widget) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        clamp = Adw.Clamp()
        clamp.set_maximum_size(540)
        clamp.set_child(child)
        scroll.set_child(clamp)
        return scroll

    @staticmethod
    def _page_box() -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.set_margin_top(12)
        box.set_margin_bottom(24)
        box.set_margin_start(16)
        box.set_margin_end(16)
        return box

    def _make_tile(self, entry: dict) -> Gtk.Button:
        btn = Gtk.Button()
        btn.add_css_class("card")
        btn.add_css_class("roudix-tile")
        btn.connect("clicked", lambda _b, aid=entry["id"]: launch(aid))

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(18)
        box.set_margin_bottom(18)
        box.set_margin_start(12)
        box.set_margin_end(12)

        img = Gtk.Image.new_from_icon_name(icon_or_fallback(entry["icon"]))
        img.set_pixel_size(48)
        box.append(img)

        title = Gtk.Label(label=entry["title"])
        title.add_css_class("heading")
        title.set_wrap(True)
        title.set_justify(Gtk.Justification.CENTER)
        box.append(title)

        sub = Gtk.Label(label=entry["subtitle"])
        sub.add_css_class("dim-label")
        sub.add_css_class("caption")
        sub.set_wrap(True)
        sub.set_justify(Gtk.Justification.CENTER)
        sub.set_max_width_chars(24)
        box.append(sub)

        btn.set_child(box)
        return btn

    def _make_grid(self, entries: list) -> Gtk.Grid:
        grid = Gtk.Grid(column_spacing=12, row_spacing=12)
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        for i, entry in enumerate(entries):
            grid.attach(self._make_tile(entry), i % 2, i // 2, 1, 1)
        return grid

    # ── Welcome page ─────────────────────────────────────────────────────────
    def _build_welcome_page(self) -> Gtk.Widget:
        main = self._page_box()

        # Hero
        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        hero.set_halign(Gtk.Align.CENTER)
        logo = Gtk.Image.new_from_icon_name("roudix-logo")
        logo.set_pixel_size(112)
        hero.append(logo)

        title = Gtk.Label(label=tr("Welcome to Roudix"))
        title.add_css_class("roudix-hero-title")
        title.set_wrap(True)
        title.set_justify(Gtk.Justification.CENTER)
        hero.append(title)

        tagline = Gtk.Label(label=tr("Your NixOS, your way — shared with the people you care about."))
        tagline.add_css_class("dim-label")
        tagline.set_wrap(True)
        tagline.set_justify(Gtk.Justification.CENTER)
        tagline.set_max_width_chars(44)
        hero.append(tagline)

        pill = Gtk.Label(label=get_pretty_name())
        pill.add_css_class("roudix-version-pill")
        pill.add_css_class("caption")
        pill.set_halign(Gtk.Align.CENTER)
        pill.set_margin_top(4)
        hero.append(pill)
        main.append(hero)

        # Tiles (2 columns): Roudix apps, then system tools (only installed ones)
        main.append(self._make_grid(APPS))
        tools = [e for e in SYSTEM_APPS if shutil.which(e["id"])]
        if tools:
            heading = Gtk.Label(label=tr("System tools"), xalign=0)
            heading.add_css_class("heading")
            main.append(heading)
            main.append(self._make_grid(tools))

        # Quick links
        links = [(t, i, u) for (t, i, u) in LINKS if u]
        if links:
            group = Adw.PreferencesGroup()
            group.set_title(tr("Resources"))
            flow = Gtk.FlowBox()
            flow.set_selection_mode(Gtk.SelectionMode.NONE)
            flow.set_homogeneous(True)
            flow.set_max_children_per_line(3)
            flow.set_min_children_per_line(2)
            flow.set_column_spacing(8)
            flow.set_row_spacing(8)
            for text, icon, url in links:
                b = Gtk.Button()
                b.set_child(Adw.ButtonContent(icon_name=icon, label=text))
                b.add_css_class("pill")
                b.connect("clicked", lambda _b, u=url: open_uri(u))
                flow.append(b)
            group.add(flow)
            main.append(group)

        # Startup toggle (same marker mechanism as before)
        startup_group = Adw.PreferencesGroup()
        startup_row = Adw.SwitchRow()
        startup_row.set_title(tr("Show at startup"))
        startup_row.set_subtitle(tr("Show this window again on every login"))
        startup_row.set_active(not os.path.exists(DISABLED_MARKER))
        startup_row.connect("notify::active", self.on_startup_toggled)
        startup_group.add(startup_row)
        main.append(startup_group)
        return main

    # ── Tweaks page ──────────────────────────────────────────────────────────
    def _build_tweaks_page(self) -> Gtk.Widget:
        main = self._page_box()

        maint = Adw.PreferencesGroup()
        maint.set_title(tr("Maintenance"))
        maint.set_description(tr("Common system tasks, one click away."))
        for entry in TWEAKS:
            row = Adw.ActionRow()
            row.set_title(entry["title"])
            row.set_subtitle(entry["subtitle"])
            row.add_prefix(Gtk.Image.new_from_icon_name(entry["icon"]))
            btn = Gtk.Button(label=tr("Run"))
            btn.add_css_class("suggested-action")
            btn.set_valign(Gtk.Align.CENTER)
            btn.connect("clicked", lambda _b, e=entry: self.on_tweak(e))
            row.add_suffix(btn)
            row.set_activatable_widget(btn)
            maint.add(row)
        main.append(maint)

        cfg = Adw.PreferencesGroup()
        cfg.set_title(tr("Configuration"))
        row = Adw.ActionRow()
        row.set_title(tr("Open configuration folder"))
        row.set_subtitle(NH_FLAKE)
        row.add_prefix(Gtk.Image.new_from_icon_name("folder-symbolic"))
        row.add_suffix(Gtk.Image.new_from_icon_name("go-next-symbolic"))
        row.set_activatable(True)
        row.connect("activated", lambda _r: open_uri(Gio.File.new_for_path(NH_FLAKE).get_uri()))
        cfg.add(row)
        main.append(cfg)
        return main

    def on_tweak(self, entry: dict):
        if not entry.get("confirm"):
            self._run(entry)
            return
        dlg = Adw.AlertDialog(heading=entry["title"], body=entry["confirm"])
        dlg.add_response("cancel", tr("Cancel"))
        dlg.add_response("run", tr("Run"))
        dlg.set_response_appearance("run", Adw.ResponseAppearance.SUGGESTED)
        dlg.set_default_response("cancel")
        dlg.set_close_response("cancel")
        dlg.connect("response", lambda _d, r, e=entry: self._run(e) if r == "run" else None)
        dlg.present(self)

    def _run(self, entry: dict):
        if entry.get("mode") == "terminal":
            if not run_in_terminal(entry["argv"]):
                dlg = Adw.AlertDialog(
                    heading=tr("No terminal found"),
                    body=tr("Open a terminal yourself and run `update`."),
                )
                dlg.add_response("ok", tr("Close"))
                dlg.present(self)
            return
        dlg = RunDialog(entry["title"], entry["argv"])
        dlg.present(self)
        dlg.start()

    def on_startup_toggled(self, row, _pspec):
        show_at_startup = row.get_active()
        try:
            if show_at_startup:
                if os.path.exists(DISABLED_MARKER):
                    os.remove(DISABLED_MARKER)
                    log.info("Startup re-enabled (marker removed)")
            else:
                os.makedirs(os.path.dirname(DISABLED_MARKER), exist_ok=True)
                open(DISABLED_MARKER, "a").close()
                log.info("Startup disabled (marker created)")
        except OSError:
            log.exception("Could not update startup marker at %s", DISABLED_MARKER)


class RoudixWelcomeApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="io.roudix.welcome",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        win = self.props.active_window or RoudixWelcomeWindow(app)
        win.present()


def main():
    setup_logging()
    log.info("=== Roudix Welcome started ===")
    app = RoudixWelcomeApp()
    sys.exit(app.run(sys.argv))


if __name__ == "__main__":
    main()
