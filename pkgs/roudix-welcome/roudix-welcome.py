#!/usr/bin/env python3
import gi
import os
import sys
import logging
import subprocess

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio

# ── Paths ─────────────────────────────────────────────────────────────────────
LOG_DIR  = os.path.expanduser("~/.local/share/roudix-welcome")
LOG_FILE = os.path.join(LOG_DIR, "welcome.log")

# Read by the roudix-welcome.service ConditionPathExists=! check (see the
# roudix.welcome Home Manager module) — touching/removing this file is the
# only thing the "Show at startup" switch below does. It never touches
# systemd enablement itself, so the toggle survives `nh os switch` rebuilds
# instead of being fought by Home Manager re-linking the unit every time.
DISABLED_MARKER = os.path.expanduser("~/.config/roudix/welcome-disabled")

GITHUB_URL = "https://github.com/RoudineBWT/Roudix"


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


def _detect_lang() -> str:
    # Same bilingual idiom as roudix-switcher / roudix-installer.
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        val = os.environ.get(var, "")
        if val:
            return "fr" if val.lower().startswith("fr") else "en"
    return "en"


LANG = _detect_lang()


def L(fr: str, en: str) -> str:
    return fr if LANG == "fr" else en


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
        "id":       "roudix-switcher",
        "icon":     "io.roudix.switcher",
        "title":    L("Personnalisation", "Customizer"),
        "subtitle": L(
            "Bureau, shell, apps et réglages système",
            "Desktop, shell, apps and system tweaks",
        ),
    },
    {
        "id":       "roudix-kernel-switcher",
        "icon":     "io.roudix.kernel-switcher",
        "title":    L("Kernel", "Kernel Switcher"),
        "subtitle": L(
            "Choisis ta variante de kernel CachyOS",
            "Pick your CachyOS kernel variant",
        ),
    },
    {
        # Binary/desktop id is "roudix-scheduler" (see
        # pkgs/roudix-scheduler-switcher/default.nix) even though the Nix
        # attribute/module is roudix-scheduler-switcher.
        "id":       "roudix-scheduler",
        "icon":     "io.roudix.scheduler",
        "title":    L("Ordonnanceur SCX", "SCX Scheduler"),
        "subtitle": L(
            "Choisis et applique un ordonnanceur SCX",
            "Choose and apply an SCX scheduler",
        ),
    },
]


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


class RoudixWelcomeWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title(L("Bienvenue sur Roudix", "Welcome to Roudix"))
        self.set_default_size(560, 720)
        self.set_resizable(False)

        toolbar = Adw.ToolbarView()
        self.set_content(toolbar)

        header = Adw.HeaderBar()
        header.set_show_title(False)
        toolbar.add_top_bar(header)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        toolbar.set_content(scroll)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(460)
        scroll.set_child(clamp)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(8)
        main_box.set_margin_bottom(24)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)
        clamp.set_child(main_box)

        # ── Hero: logo + title (branding = roudix-logo, from roudix-branding,
        # already installed system-wide and hicolor/scalable-resolvable) ──────
        logo = Gtk.Image.new_from_icon_name("roudix-logo")
        logo.set_pixel_size(96)
        logo.set_margin_top(8)
        main_box.append(logo)

        title = Gtk.Label()
        title.set_markup(
            f"<span size='x-large' weight='bold'>"
            f"{L('Bienvenue sur Roudix', 'Welcome to Roudix')}</span>"
        )
        main_box.append(title)

        # ── Description ──────────────────────────────────────────────────────
        # A short blurb about the distro itself, not just about this window
        # (per Roudine's request) — what Roudix is, in a couple of lines.
        description = Gtk.Label()
        description.set_markup(
            L(
                "<span size='small'>"
                "Roudix est ta distribution NixOS personnelle : compositeurs "
                "Wayland (Niri, Hyprland, MangoWC, Umbriel), GNOME et KDE, "
                "kernel CachyOS et tout un tas de réglages pensés pour toi — "
                "et pour la famille et les amis à qui tu la partages. Utilise "
                "les raccourcis ci-dessous pour personnaliser ton système "
                "ou changer de kernel et d'ordonnanceur.</span>",
                "<span size='small'>"
                "Roudix is your personal NixOS distribution: Wayland "
                "compositors (Niri, Hyprland, MangoWC, Umbriel), GNOME and "
                "KDE, a CachyOS kernel, and a bunch of tweaks built for you — "
                "and for the family and friends you share it with. Use the "
                "shortcuts below to customize your system or switch kernel "
                "and scheduler.</span>",
            )
        )
        description.add_css_class("dim-label")
        description.set_wrap(True)
        description.set_justify(Gtk.Justification.CENTER)
        description.set_max_width_chars(48)
        main_box.append(description)

        # ── Launchers ─────────────────────────────────────────────────────────
        apps_group = Adw.PreferencesGroup()
        apps_group.set_title(L("Applications Roudix", "Roudix Apps"))
        main_box.append(apps_group)

        for entry in APPS:
            row = Adw.ActionRow()
            row.set_title(entry["title"])
            row.set_subtitle(entry["subtitle"])
            row.set_icon_name(entry["icon"])
            row.set_activatable(True)

            open_btn = Gtk.Button(label=L("Ouvrir", "Open"))
            open_btn.add_css_class("flat")
            open_btn.set_valign(Gtk.Align.CENTER)
            open_btn.connect("clicked", lambda _b, aid=entry["id"]: launch(aid))
            row.add_suffix(open_btn)
            row.connect("activated", lambda _r, aid=entry["id"]: launch(aid))

            apps_group.add(row)

        # ── Resources ─────────────────────────────────────────────────────────
        links_group = Adw.PreferencesGroup()
        links_group.set_title(L("Ressources", "Resources"))
        main_box.append(links_group)

        github_row = Adw.ActionRow()
        github_row.set_title(L("Code source & documentation", "Source code & documentation"))
        github_row.set_subtitle("github.com/RoudineBWT/Roudix")
        github_row.set_icon_name("system-software-install-symbolic")
        github_row.set_activatable(True)
        github_btn = Gtk.Button(label=L("Ouvrir", "Open"))
        github_btn.add_css_class("flat")
        github_btn.set_valign(Gtk.Align.CENTER)
        github_btn.connect("clicked", lambda _b: open_uri(GITHUB_URL))
        github_row.add_suffix(github_btn)
        github_row.connect("activated", lambda _r: open_uri(GITHUB_URL))
        links_group.add(github_row)

        # ── Startup toggle ────────────────────────────────────────────────────
        startup_group = Adw.PreferencesGroup()
        main_box.append(startup_group)

        startup_row = Adw.SwitchRow()
        startup_row.set_title(L("Afficher au démarrage", "Show at startup"))
        startup_row.set_subtitle(
            L(
                "Réaffiche cette fenêtre à chaque connexion",
                "Show this window again on every login",
            )
        )
        startup_row.set_active(not os.path.exists(DISABLED_MARKER))
        startup_row.connect("notify::active", self.on_startup_toggled)
        startup_group.add(startup_row)

        # ── Close + version footer ───────────────────────────────────────────
        close_btn = Gtk.Button(label=L("Fermer", "Close"))
        close_btn.add_css_class("pill")
        close_btn.set_halign(Gtk.Align.CENTER)
        close_btn.set_margin_top(4)
        close_btn.connect("clicked", lambda _b: self.close())
        main_box.append(close_btn)

        version_label = Gtk.Label(label=get_pretty_name())
        version_label.add_css_class("dim-label")
        version_label.add_css_class("caption")
        version_label.set_halign(Gtk.Align.CENTER)
        main_box.append(version_label)

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
        win = RoudixWelcomeWindow(app)
        win.present()


def main():
    setup_logging()
    log.info("=== Roudix Welcome started ===")
    app = RoudixWelcomeApp()
    sys.exit(app.run(sys.argv))


if __name__ == "__main__":
    main()
