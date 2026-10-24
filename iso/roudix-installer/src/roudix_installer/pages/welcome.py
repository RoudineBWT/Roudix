import importlib.resources
from pathlib import Path

from gi.repository import Adw, Gtk

from roudix_installer import existing_nixos, host_profile, i18n
from roudix_installer.i18n import tr
from roudix_installer.ui_helpers import page_with_header

REAL_LOGO = Path("/run/current-system/sw/share/icons/hicolor/256x256/apps/roudix-logo.png")


def _host_label(name: str) -> str:
    return {
        "roudix": tr("roudix — full desktop, every option"),
        "nixie": tr("nixie — light laptop, few questions"),
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

        # One line, every language: nobody has chosen theirs yet.
        subtitle = Gtk.Label(
            label=" · ".join(prompt for _code, _name, prompt in i18n.LANGUAGES),
            css_classes=["dim-label"], wrap=True, justify=Gtk.Justification.CENTER,
        )
        self.box.append(subtitle)

        # A dropdown scales to any number of languages: adding one to
        # i18n.LANGUAGES is enough, the welcome page needs no layout change.
        group = Adw.PreferencesGroup()
        group.set_size_request(380, -1)
        group.set_halign(Gtk.Align.CENTER)
        self.lang_row = Adw.ComboRow(
            model=Gtk.StringList.new([name for _code, name, _prompt in i18n.LANGUAGES]),
        )
        self.lang_row.set_title("\N{GLOBE WITH MERIDIANS}")
        # Long lists: let the popover be searched by typing.
        if len(i18n.LANGUAGES) > 8:
            self.lang_row.set_expression(
                Gtk.PropertyExpression.new(Gtk.StringObject, None, "string"))
            self.lang_row.set_enable_search(True)
        codes = [code for code, _name, _prompt in i18n.LANGUAGES]
        if i18n.LANG in codes:
            self.lang_row.set_selected(codes.index(i18n.LANG))
        group.add(self.lang_row)
        self.box.append(group)

        # No text on the button: no language is chosen yet, so any label would
        # be in the wrong one. The arrow flips by itself in RTL.
        next_btn = Gtk.Button(icon_name="go-next-symbolic",
                              css_classes=["suggested-action", "pill"])
        next_btn.set_halign(Gtk.Align.CENTER)
        next_btn.connect(
            "clicked",
            lambda *_: self._choose_lang(i18n.LANGUAGES[self.lang_row.get_selected()][0]),
        )
        self.box.append(next_btn)

    def _choose_lang(self, lang: str):
        i18n.set_lang(lang)
        # Mirror the whole UI for right-to-left languages (Arabic…); GTK re-lays out
        # the widgets that already exist and the ones built later.
        Gtk.Widget.set_default_direction(
            Gtk.TextDirection.RTL if i18n.is_rtl(lang) else Gtk.TextDirection.LTR
        )
        self._show_welcome_step()

    def _show_welcome_step(self):
        self._clear_below_title()

        if self.state.mode == existing_nixos.MODE_EXISTING:
            text = tr("This machine already runs NixOS. Roudix is built next to your current system: "
                      "nothing is wiped, /etc/nixos is backed up first, and your previous system stays "
                      "in the boot menu. Two steps: options, then off we go.")
        else:
            text = tr("We're about to install Roudix on this machine. Three steps: disk, options, then off we go.")
        subtitle = Gtk.Label(label=text, css_classes=["dim-label"], wrap=True)
        self.box.append(subtitle)

        # Which hosts/<name>/ profile to install. Asked here, before the
        # Options page is built, because the profile decides which
        # questions that page shows (see host_profile.py).
        self._hosts = host_profile.available_hosts()
        if self.state.hostname not in self._hosts:
            self.state.hostname = self._hosts[0]
        if len(self._hosts) > 1:
            group = Adw.PreferencesGroup(title=tr("Profile to install"))
            group.set_size_request(460, -1)
            group.set_halign(Gtk.Align.CENTER)
            self.host_row = Adw.ComboRow(
                title=tr("Profile / host"),
                model=Gtk.StringList.new([_host_label(n) for n in self._hosts]),
            )
            self.host_row.set_selected(self._hosts.index(self.state.hostname))
            self.host_row.connect("notify::selected", lambda *_: self._on_host_selected())
            group.add(self.host_row)
            self.box.append(group)
            self.host_note = Gtk.Label(css_classes=["dim-label", "caption"], wrap=True)
            self.box.append(self.host_note)
            self._on_host_selected()

        start_btn = Gtk.Button(label=tr("Get started"),
                                css_classes=["suggested-action", "pill"])
        start_btn.set_halign(Gtk.Align.CENTER)
        start_btn.connect("clicked", lambda *_: self.on_next())
        self.box.append(start_btn)

    def _on_host_selected(self):
        name = self._hosts[self.host_row.get_selected()]
        self.state.hostname = name
        if host_profile.find_example(name) is None:
            note = tr("Warning: this profile can't be found in this ISO — every question will be asked.")
        elif host_profile.listed_options(name) is None:
            note = tr("Every question will be asked.")
        else:
            note = tr("Only the questions relevant to this profile will be asked.")
        self.host_note.set_label(note)
