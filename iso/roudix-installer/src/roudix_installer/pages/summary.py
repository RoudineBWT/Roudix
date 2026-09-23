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
        self._rows: list[Adw.ActionRow] = []
        box.append(self.group)

        install_btn = Gtk.Button(label=L("Installer Roudix", "Install Roudix"),
                                  css_classes=["destructive-action", "pill"],
                                  halign=Gtk.Align.END, margin_top=12)
        install_btn.connect("clicked", lambda *_: self.on_next())
        box.append(install_btn)

        self.set_child(page_with_header(L("Résumé", "Summary"), scroller))
        self.connect("shown", lambda *_: self._refresh())

    def _refresh(self):
        # Same Adw.PreferencesGroup gotcha as disk.py's partition list:
        # get_first_child()/get_next_sibling() on the group walks its
        # internal structure, not the rows added via .add(), so this
        # never actually removed anything — every visit to Summary was
        # stacking a fresh set of rows under the old ones.
        for row in self._rows:
            self.group.remove(row)
        self._rows.clear()

        s = self.state
        swap_label = f", swap {s.disk.swap_size_gb}G" if s.disk.enable_swap else L(", pas de swap (zram)", ", no swap (zram)")
        wiped = L("effacé", "wiped")
        disk_label = {
            "simple": f"{s.disk.device} — {s.disk.filesystem}, /boot {s.disk.boot_size_gb}G{swap_label} ({wiped})",
            "advanced": f"{s.disk.advanced_disko_path} ({L('disko custom', 'custom disko')})",
            "manual": ", ".join(f"{dev} → {mp}" for dev, mp in s.disk.manual_partitions.items())
                      or L("aucune partition assignée", "no partition assigned"),
        }[s.disk.mode]

        kernel_display = s.kernel_chaotic if s.gpu == "nvidia" else s.kernel
        kernel_source = "Chaotic-Nyx" if s.gpu == "nvidia" else "xddxdd"

        rows = [
            (L("Disque", "Disk"), disk_label),
            (L("Utilisateur", "User"), s.username),
            (L("Mot de passe", "Password"), L("défini ✓", "set ✓") if s.password else L("⚠ non défini", "⚠ not set")),
            ("GPU", f"{s.gpu}" + (L(" (laptop Optimus)", " (Optimus laptop)") if s.nvidia_laptop else "")),
            ("CPU", s.cpu),
            ("Kernel", f"{kernel_display} ({kernel_source})"),
            (L("Navigateur", "Browser"), s.browser + (" + Zen" if s.zen_browser else "")),
            (L("Bureau", "Desktop"), f"{s.desktop}" + (f" + {s.desktop_shell}" if s.desktop in ("niri", "hyprland", "mangowc", "umbriel") else "")),
            (L("Éditeur", "Editor"), s.editor),
            (
                L("Trousseau / portal", "Keyring / portal"),
                s.desktop_integration if s.desktop in ("niri", "hyprland", "mangowc", "umbriel") else L("n/a (géré par le bureau)", "n/a (managed by the desktop)"),
            ),
            (L("Shell", "Shell"), s.default_shell),
            ("VM / Gaming", f"{'VM' if s.vm_guest else L('bare metal', 'bare metal')} — gaming "
                            f"{L('activé', 'enabled') if s.gaming else L('désactivé', 'disabled')}"),
            (L("Locale", "Locale"), f"{s.timezone} — {s.locale} — {s.keymap}"),
            (
                L("Clavier graphique", "Graphical keyboard"),
                f"{s.keyboard_layout}" + (f" ({s.keyboard_variant})" if s.keyboard_variant else ""),
            ),
            ("RGB", s.rgb + (f", RAM {s.memory_type}" if s.rgb == "openlinkhub" and s.memory_rgb_enable else "")),
            (L("Extras", "Extras"), ", ".join(filter(None, [
                "GTA fix" if s.gta_fix else "",
                "Flatpak" if s.flatpak else "",
                L("Virtualisation", "Virtualization") if s.virtualization else "",
                f"autoupdate {s.autoupdate_interval}" if s.autoupdate else "",
            ])) or L("aucun", "none")),
            ("Bootloader", s.bootloader),
            ("Matrix", s.matrix_client),
            ("Discord", s.discord),
            ("Telegram", s.telegram),
            (L("Lecteur vidéo", "Video player"), s.video_player),
            (L("Client torrent", "Torrent client"), s.torrent_client),
            (L("Lecteur de musique", "Music player"), s.music_player),
            ("Waydroid", L("activé", "enabled") if s.waydroid_enable else L("désactivé", "disabled")),
            ("Apps", ", ".join(filter(None, [
                "" if s.app_gimp else L("sans GIMP", "no GIMP"),
                "" if s.app_inkscape else L("sans Inkscape", "no Inkscape"),
                "" if s.app_songrec else L("sans SongRec", "no SongRec"),
                "" if s.app_easyeffects else L("sans EasyEffects", "no EasyEffects"),
            ])) or L("config par défaut", "default set")),
        ] + ([
            ("Spicetify", f"{s.spicetify_theme}"
                + (f" ({s.spicetify_color_scheme})" if s.spicetify_color_scheme else "")
                + " — " + (", ".join(filter(None, [
                    "adblock" if s.spicetify_adblock else "",
                    L("masquer podcasts", "hide podcasts") if s.spicetify_hide_podcasts else "",
                    "marketplace" if s.spicetify_marketplace else "",
                ])) or L("sans extension", "no extensions"))),
        ] if s.music_player == "spotify" else []) + [
            (
                L("Création de contenu", "Content Creation"),
                (
                    f"OBS ({', '.join(filter(None, [
                        'vkcapture' if s.obs_plugin_vkcapture else '',
                        'pipewire-audio' if s.obs_plugin_pipewire_audio_capture else '',
                        'background-removal' if s.obs_plugin_background_removal else '',
                        'move-transition' if s.obs_plugin_move_transition else '',
                        'aitum-multistream' if s.obs_plugin_aitum_multistream else '',
                        'gstreamer' if s.obs_plugin_gstreamer else '',
                        'composite-blur' if s.obs_plugin_composite_blur else '',
                        'advanced-scene-switcher' if s.obs_plugin_advanced_scene_switcher else '',
                        'input-overlay' if s.obs_plugin_input_overlay else '',
                        'waveform' if s.obs_plugin_waveform else '',
                    ])) or L('sans plugin', 'no plugins')}) — {s.video_editor}"
                    + (" — Chatterino" if s.chatterino_enable else "")
                )
                if s.content_creation_enable
                else L("désactivé", "disabled"),
            ),
        ]
        for title, value in rows:
            row = Adw.ActionRow(title=title, subtitle=value)
            self.group.add(row)
            self._rows.append(row)
