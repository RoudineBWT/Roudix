#!/usr/bin/env python3
"""
Roudix Installer — entry point.

A small GTK4 / libadwaita wizard that replaces Calamares for Roudix.
It reuses the exact logic of roudix-installer.sh (option choices ->
Nix config generation) but drives it from a GUI instead of a bash
prompt loop, and delegates partitioning to disko instead of KPMCore.

Flow:
    Welcome -> Disk -> Options -> Summary -> Progress
"""
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk  # noqa: E402

from roudix_installer.pages.disk import DiskPage
from roudix_installer.pages.options import OptionsPage
from roudix_installer.pages.progress import ProgressPage
from roudix_installer.pages.summary import SummaryPage
from roudix_installer.pages.welcome import WelcomePage
from roudix_installer.state import InstallState


class RoudixInstallerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Roudix Installer")
        self.set_default_size(880, 620)

        self.state = InstallState()

        # NavigationView *is* the window content — each page brings its own
        # Adw.ToolbarView/HeaderBar (see ui_helpers.page_with_header), which
        # is what makes the automatic back button appear per page.
        self.stack = Adw.NavigationView()
        self.set_content(self.stack)

        self.pages = {
            "welcome": WelcomePage(self.state, on_next=lambda: self.goto("disk")),
            "disk": DiskPage(self.state, on_next=lambda: self.goto("options")),
            "options": OptionsPage(self.state, on_next=lambda: self.goto("summary")),
            "summary": SummaryPage(self.state, on_next=lambda: self.goto("progress")),
            "progress": ProgressPage(self.state),
        }

        self.stack.push(self.pages["welcome"])

    def goto(self, name: str):
        self.stack.push(self.pages[name])


class RoudixInstallerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="dev.roudix.Installer",
                          flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = RoudixInstallerWindow(self)
        win.present()


def main():
    import importlib.resources

    from gi.repository import Gdk

    app = RoudixInstallerApp()

    def on_startup(*_):
        # Roudix branding is a dark theme (Catppuccin Mocha) — force dark
        # so libadwaita's own widgets (popovers, switches...) match instead
        # of following the live ISO's system light/dark setting.
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        provider = Gtk.CssProvider()
        css_path = importlib.resources.files("roudix_installer") / "style.css"
        provider.load_from_path(str(css_path))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    app.connect("startup", on_startup)
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
