import importlib.resources
from pathlib import Path

from gi.repository import Adw, Gtk

from roudix_installer import host_profile, i18n
from roudix_installer.i18n import L
from roudix_installer.ui_helpers import page_with_header

REAL_LOGO = Path("/run/current-system/sw/share/icons/hicolor/256x256/apps/roudix-logo.png")


def _host_label(name: str) -> str:
    return {
        "roudix": L("roudix — bureau complet, toutes les options", "roudix — full desktop, every option"),
        "nixie": L("nixie — portable léger, peu de questions", "nixie — light laptop, few questions"),
    }.get(name, name)


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
        # Order matches the subtitle above ("Choose your language / Choisis ta
        # langue" — English first): English button first, then French.
        en_btn = Gtk.Button(label="English", css_classes=["pill"])
        en_btn.connect("clicked", lambda *_: self._choose_lang("en"))
        fr_btn = Gtk.Button(label="Français", css_classes=["pill"])
        fr_btn.connect("clicked", lambda *_: self._choose_lang("fr"))
        button_row.append(en_btn)
        button_row.append(fr_btn)
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

        # Which hosts/<name>/ profile to install. Asked here, before the
        # Options page is built, because the profile decides which
        # questions that page shows (see host_profile.py).
        self._hosts = host_profile.available_hosts()
        if self.state.hostname not in self._hosts:
            self.state.hostname = self._hosts[0]
        if len(self._hosts) > 1:
            group = Adw.PreferencesGroup(title=L("Profil à installer", "Profile to install"))
            group.set_size_request(460, -1)
            group.set_halign(Gtk.Align.CENTER)
            self.host_row = Adw.ComboRow(
                title=L("Profil / hôte", "Profile / host"),
                model=Gtk.StringList.new([_host_label(n) for n in self._hosts]),
            )
            self.host_row.set_selected(self._hosts.index(self.state.hostname))
            self.host_row.connect("notify::selected", lambda *_: self._on_host_selected())
            group.add(self.host_row)
            self.box.append(group)
            self.host_note = Gtk.Label(css_classes=["dim-label", "caption"], wrap=True)
            self.box.append(self.host_note)
            self._on_host_selected()

        start_btn = Gtk.Button(label=L("Commencer", "Get started"),
                                css_classes=["suggested-action", "pill"])
        start_btn.set_halign(Gtk.Align.CENTER)
        start_btn.connect("clicked", lambda *_: self.on_next())
        self.box.append(start_btn)

    def _on_host_selected(self):
        name = self._hosts[self.host_row.get_selected()]
        self.state.hostname = name
        if host_profile.find_example(name) is None:
            note = L(
                "Attention : ce profil est introuvable dans cette ISO — toutes les questions seront posées.",
                "Warning: this profile can't be found in this ISO — every question will be asked.",
            )
        elif host_profile.listed_options(name) is None:
            note = L("Toutes les questions seront posées.", "Every question will be asked.")
        else:
            note = L(
                "Seules les questions utiles à ce profil seront posées.",
                "Only the questions relevant to this profile will be asked.",
            )
        self.host_note.set_label(note)
