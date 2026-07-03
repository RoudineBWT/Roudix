import importlib.resources

from gi.repository import Adw, Gtk

from roudix_installer.ui_helpers import page_with_header


class WelcomePage(Adw.NavigationPage):
    def __init__(self, state, on_next):
        super().__init__(title="Bienvenue")
        self.state = state

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                       margin_top=48, margin_bottom=48, margin_start=48, margin_end=48,
                       valign=Gtk.Align.CENTER)

        logo_path = importlib.resources.files("roudix_installer") / "logo.svg"
        logo = Gtk.Picture.new_for_filename(str(logo_path))
        logo.set_content_fit(Gtk.ContentFit.CONTAIN)
        logo.set_size_request(120, 120)
        logo.set_halign(Gtk.Align.CENTER)

        title = Gtk.Label(label="Roudix", css_classes=["title-1"])
        subtitle = Gtk.Label(
            label="On va installer Roudix sur cette machine. "
                  "Trois étapes : disque, options, puis c'est parti.",
            css_classes=["dim-label"],
            wrap=True,
        )

        start_btn = Gtk.Button(label="Commencer", css_classes=["suggested-action", "pill"])
        start_btn.set_halign(Gtk.Align.CENTER)
        start_btn.connect("clicked", lambda *_: on_next())

        for w in (logo, title, subtitle, start_btn):
            box.append(w)

        self.set_child(page_with_header("Bienvenue", box))
