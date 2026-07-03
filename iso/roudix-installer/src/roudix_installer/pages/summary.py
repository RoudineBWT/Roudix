from gi.repository import Adw, Gtk

from roudix_installer.i18n import L
from roudix_installer.ui_helpers import page_with_header


class SummaryPage(Adw.NavigationPage):
    def __init__(self, state, on_next):
        super().__init__(title=L("Résumé", "Summary"))
        self.state = state
        self.on_next = on_next

        scroller = Gtk.ScrolledWindow(vexpand=True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                       margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)
        scroller.set_child(box)

        self.group = Adw.PreferencesGroup(title=L("Vérifie avant de lancer l'installation", "Check before starting the install"))
        box.append(self.group)

        install_btn = Gtk.Button(label=L("Installer Roudix", "Install Roudix"),
                                  css_classes=["destructive-action", "pill"],
                                  halign=Gtk.Align.END, margin_top=12)
        install_btn.connect("clicked", lambda *_: self.on_next())
        box.append(install_btn)

        self.set_child(page_with_header(L("Résumé", "Summary"), scroller))
        self.connect("shown", lambda *_: self._refresh())

    def _refresh(self):
        # Clear and repopulate in case options were changed after going back
        child = self.group.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.group.remove(child)
            child = nxt

        s = self.state
        swap_label = f", swap {s.disk.swap_size_gb}G" if s.disk.enable_swap else L(", pas de swap (zram)", ", no swap (zram)")
        wiped = L("effacé", "wiped")
        disk_label = {
            "simple": f"{s.disk.device} — {s.disk.filesystem}, /boot {s.disk.boot_size_gb}G{swap_label} ({wiped})",
            "advanced": f"{s.disk.advanced_disko_path} ({L('disko custom', 'custom disko')})",
            "manual": ", ".join(f"{dev} → {mp}" for dev, mp in s.disk.manual_partitions.items())
                      or L("aucune partition assignée", "no partition assigned"),
        }[s.disk.mode]

        rows = [
            (L("Disque", "Disk"), disk_label),
            (L("Utilisateur", "User"), s.username),
            ("GPU", f"{s.gpu}" + (L(" (laptop Optimus)", " (Optimus laptop)") if s.nvidia_laptop else "")),
            ("CPU", s.cpu),
            ("Kernel", s.kernel),
            (L("Navigateur", "Browser"), s.browser + (" + Zen" if s.zen_browser else "")),
            (L("Bureau", "Desktop"), f"{s.desktop}" + (f" + {s.desktop_shell}" if s.desktop in ("niri", "hyprland") else "")),
            (L("Shell", "Shell"), s.default_shell),
            ("VM / Gaming", f"{'VM' if s.vm_guest else L('bare metal', 'bare metal')} — gaming "
                            f"{L('activé', 'enabled') if s.gaming else L('désactivé', 'disabled')}"),
            (L("Locale", "Locale"), f"{s.timezone} — {s.locale} — {s.keymap}"),
            ("RGB", s.rgb + (f", RAM {s.memory_type}" if s.rgb == "openlinkhub" and s.memory_rgb_enable else "")),
            (L("Extras", "Extras"), ", ".join(filter(None, [
                "GTA fix" if s.gta_fix else "",
                "Flatpak" if s.flatpak else "",
                L("Virtualisation", "Virtualization") if s.virtualization else "",
                f"autoupdate {s.autoupdate_interval}" if s.autoupdate else "",
            ])) or L("aucun", "none")),
            ("Bootloader", s.bootloader),
            ("Matrix", s.matrix_client),
            ("Waydroid", L("activé", "enabled") if s.waydroid_enable else L("désactivé", "disabled")),
        ]
        for title, value in rows:
            self.group.add(Adw.ActionRow(title=title, subtitle=value))
