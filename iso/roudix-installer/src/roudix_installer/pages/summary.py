from gi.repository import Adw, Gtk


class SummaryPage(Adw.NavigationPage):
    def __init__(self, state, on_next):
        super().__init__(title="Résumé")
        self.state = state
        self.on_next = on_next

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                       margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)

        self.group = Adw.PreferencesGroup(title="Vérifie avant de lancer l'installation")
        box.append(self.group)

        install_btn = Gtk.Button(label="Installer Roudix",
                                  css_classes=["destructive-action", "pill"],
                                  halign=Gtk.Align.END, margin_top=12)
        install_btn.connect("clicked", lambda *_: self.on_next())
        box.append(install_btn)

        self.set_child(box)
        self.connect("shown", lambda *_: self._refresh())

    def _refresh(self):
        # Clear and repopulate in case options were changed after going back
        child = self.group.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.group.remove(child)
            child = nxt

        s = self.state
        rows = [
            ("Disque", f"{s.disk.device or s.disk.advanced_disko_path} ({s.disk.mode})"),
            ("Machine", f"{s.hostname} — utilisateur {s.username}"),
            ("Bureau", f"{s.desktop} + {s.shell}"),
            ("Kernel", s.kernel),
            ("Bootloader", s.bootloader),
            ("Navigateur", s.browser),
            ("Matrix", s.matrix_client),
            ("Waydroid", "activé" if s.waydroid_enable else "désactivé"),
        ]
        for title, value in rows:
            self.group.add(Adw.ActionRow(title=title, subtitle=value))
