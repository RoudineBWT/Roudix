import importlib.resources
from pathlib import Path

from gi.repository import Adw, Gtk

from roudix_installer import i18n
from roudix_installer.i18n import L
from roudix_installer.ui_helpers import page_with_header

REAL_LOGO = Path("/run/current-system/sw/share/icons/hicolor/256x256/apps/roudix-logo.png")


class WelcomePage(Adw.NavigationPage):
    def __init__(self, state, on_next):
        super().__init__(title="Roudix")
        self.state = state
        self.on_next = on_next

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                            margin_top=48, margin_bottom=48, margin_start=48, margin_end=48,
                            valign=Gtk.Align.CENTER)

        if REAL_LOGO.exists():
            logo_path = REAL_LOGO
        else:
            logo_path = importlib.resources.files("roudix_installer") / "logo.svg"

        self.logo = Gtk.Picture.new_for_filename(str(logo_path))
        self.logo.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.logo.set_size_request(120, 120)
        self.logo.set_halign(Gtk.Align.CENTER)
        self.box.append(self.logo)

        self.title_label = Gtk.Label(label="Roudix", css_classes=["title-1"])
        self.box.append(self.title_label)

        self.header_wrap = page_with_header("Roudix", self.box)
        self.set_child(self.header_wrap)

        self._show_language_step()

    def _clear_below_title(self):
        child = self.title_label.get_next_sibling()
        while child is not None:
            nxt = child.get_next_sibling()
            self.box.remove(child)
            child = nxt

    def _show_language_step(self):
        self._clear_below_title()

        subtitle = Gtk.Label(
            label="Choose your language / Choisis ta langue",
            css_classes=["dim-label"],
        )
        self.box.append(subtitle)

        button_row = Gtk.Box(spacing=12, halign=Gtk.Align.CENTER)
        fr_btn = Gtk.Button(label="Français", css_classes=["pill"])
        fr_btn.connect("clicked", lambda *_: self._choose_lang("fr"))
        en_btn = Gtk.Button(label="English", css_classes=["pill"])
        en_btn.connect("clicked", lambda *_: self._choose_lang("en"))
        button_row.append(fr_btn)
        button_row.append(en_btn)
        self.box.append(button_row)

    def _choose_lang(self, lang: str):
        i18n.set_lang(lang)
        self._show_welcome_step()

    def _show_welcome_step(self):
        self._clear_below_title()

        subtitle = Gtk.Label(
            label=L(
                "On va installer Roudix sur cette machine. Trois étapes : disque, options, puis c'est parti.",
                "We're about to install Roudix on this machine. Three steps: disk, options, then off we go.",
            ),
            css_classes=["dim-label"], wrap=True,
        )
        self.box.append(subtitle)

        start_btn = Gtk.Button(label=L("Commencer", "Get started"),
                                css_classes=["suggested-action", "pill"])
        start_btn.set_halign(Gtk.Align.CENTER)
        start_btn.connect("clicked", lambda *_: self.on_next())
        self.box.append(start_btn)
