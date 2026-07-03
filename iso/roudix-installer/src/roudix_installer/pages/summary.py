from gi.repository import Adw, Gtk

from roudix_installer.ui_helpers import page_with_header


class SummaryPage(Adw.NavigationPage):
    def __init__(self, state, on_next):
        super().__init__(title="Résumé")
        self.state = state
        self.on_next = on_next

        scroller = Gtk.ScrolledWindow(vexpand=True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                       margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)
        scroller.set_child(box)

        self.group = Adw.PreferencesGroup(title="Vérifie avant de lancer l'installation")
        box.append(self.group)

        install_btn = Gtk.Button(label="Installer Roudix",
                                  css_classes=["destructive-action", "pill"],
                                  halign=Gtk.Align.END, margin_top=12)
        install_btn.connect("clicked", lambda *_: self.on_next())
        box.append(install_btn)

        self.set_child(page_with_header("Résumé", scroller))
        self.connect("shown", lambda *_: self._refresh())

    def _refresh(self):
        # Clear and repopulate in case options were changed after going back
        child = self.group.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.group.remove(child)
            child = nxt

        s = self.state
        disk_label = {
            "simple": f"{s.disk.device} (effacé, EFI+swap+root)",
            "advanced": f"{s.disk.advanced_disko_path} (disko custom)",
            "manual": ", ".join(f"{dev} → {mp}" for dev, mp in s.disk.manual_partitions.items()) or "aucune partition assignée",
        }[s.disk.mode]

        rows = [
            ("Disque", disk_label),
            ("Utilisateur", s.username),
            ("GPU", f"{s.gpu}" + (" (laptop Optimus)" if s.nvidia_laptop else "")),
            ("CPU", s.cpu),
            ("Kernel", s.kernel),
            ("Navigateur", s.browser + (" + Zen" if s.zen_browser else "")),
            ("Bureau", f"{s.desktop}" + (f" + {s.desktop_shell}" if s.desktop in ("niri", "hyprland") else "")),
            ("Shell", s.default_shell),
            ("VM / Gaming", f"{'VM' if s.vm_guest else 'bare metal'} — gaming {'activé' if s.gaming else 'désactivé'}"),
            ("Locale", f"{s.timezone} — {s.locale} — {s.keymap}"),
            ("RGB", s.rgb + (f", RAM {s.memory_type}" if s.rgb == "openlinkhub" and s.memory_rgb_enable else "")),
            ("Extras", ", ".join(filter(None, [
                "GTA fix" if s.gta_fix else "",
                "Flatpak" if s.flatpak else "",
                "Virtualisation" if s.virtualization else "",
                f"autoupdate {s.autoupdate_interval}" if s.autoupdate else "",
            ])) or "aucun"),
            ("Bootloader", s.bootloader),
            ("Matrix", s.matrix_client),
            ("Waydroid", "activé" if s.waydroid_enable else "désactivé"),
        ]
        for title, value in rows:
            self.group.add(Adw.ActionRow(title=title, subtitle=value))
