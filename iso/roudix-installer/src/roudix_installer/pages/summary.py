from gi.repository import Adw, Gtk

from roudix_installer.i18n import tr, trc
from roudix_installer.ui_helpers import page_with_header


class SummaryPage(Adw.NavigationPage):
    def __init__(self, state, on_next):
        super().__init__(title=tr("Summary"))
        self.state = state
        self.on_next = on_next

        scroller = Gtk.ScrolledWindow(vexpand=True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                       margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)
        scroller.set_child(box)

        self.group = Adw.PreferencesGroup(title=tr("Check before starting the install"))
        self._rows: list[Adw.ActionRow] = []
        box.append(self.group)

        install_btn = Gtk.Button(label=tr("Install Roudix"),
                                  css_classes=["destructive-action", "pill"],
                                  halign=Gtk.Align.END, margin_top=12)
        install_btn.connect("clicked", lambda *_: self.on_next())
        box.append(install_btn)

        self.set_child(page_with_header(tr("Summary"), scroller))
        self.connect("shown", lambda *_: self._refresh())

    @staticmethod
    def _versions_rows(s):
        """nixpkgs (default) or latest (flake) version of the chosen
        compositor and shell — omitted when neither has a flake version."""
        parts = []
        names = {}  # niri / MangoWC / Umbriel: always the flake version
        shells = {"noctalia": "Noctalia", "dms": "DMS", "caelestia": "Caelestia"}
        latest = tr("latest (flake)")
        nixpkgs = "nixpkgs"
        if s.desktop in names:
            parts.append(f"{names[s.desktop]}: {latest if getattr(s, 'latest_' + s.desktop) else nixpkgs}")
        if s.desktop in ("niri", "hyprland", "mangowc", "umbriel") and s.desktop_shell in shells:
            parts.append(f"{shells[s.desktop_shell]}: {latest if getattr(s, 'latest_' + s.desktop_shell) else nixpkgs}")
        return [(tr("Versions"), " · ".join(parts))] if parts else []

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
        swap_label = f", swap {s.disk.swap_size_gb}G" if s.disk.enable_swap else tr(", no swap (zram)")
        wiped = tr("wiped")
        disk_label = {
            "simple": f"{s.disk.device} — {s.disk.filesystem}, /boot {s.disk.boot_size_gb}G{swap_label} ({wiped})",
            "advanced": f"{s.disk.advanced_disko_path} (" + tr("custom disko") + ")",
            "manual": ", ".join(f"{dev} → {mp}" for dev, mp in s.disk.manual_partitions.items())
                      or tr("no partition assigned"),
        }[s.disk.mode]

        kernel_display = s.kernel_chaotic if s.gpu == "nvidia" else s.kernel
        kernel_source = "Chaotic-Nyx" if s.gpu == "nvidia" else "xddxdd"

        machine = "VM" if s.vm_guest else tr("bare metal")
        gaming_state = tr("enabled") if s.gaming else tr("disabled")
        obs_plugins = ", ".join(filter(None, [
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
                    ])) or tr("no plugins")
        rows = [
            (tr("Disk"), disk_label),
            (tr("User"), s.username),
            (tr("Profile / host"), s.hostname),
            (tr("Password"), tr("set ✓") if s.password else tr("⚠ not set")),
            ("GPU", f"{s.gpu}" + (tr(" (Optimus laptop)") if s.nvidia_laptop else "")),
            ("CPU", s.cpu),
            ("Kernel", f"{kernel_display} ({kernel_source})"),
            (tr("Browser"), s.browser + (" + Zen" if s.zen_browser else "")),
            (tr("Desktop"), f"{s.desktop}" + (f" + {s.desktop_shell}" if s.desktop in ("niri", "hyprland", "mangowc", "umbriel") else "")),
            *self._versions_rows(s),
            (tr("Editor"), s.editor),
            (
                tr("Keyring / portal"),
                s.desktop_integration if s.desktop in ("niri", "hyprland", "mangowc", "umbriel") else tr("n/a (managed by the desktop)"),
            ),
            (tr("Shell"), s.default_shell),
            ("VM / Gaming", f"{machine} — gaming "
                            f"{gaming_state}"
                            f"{' + Millennium' if s.gaming and s.gaming_steam_millennium else ''}"),
            (tr("Locale"), f"{s.timezone} — {s.locale} — {s.keymap}"),
            (
                tr("Graphical keyboard"),
                f"{s.keyboard_layout}" + (f" ({s.keyboard_variant})" if s.keyboard_variant else ""),
            ),
            ("RGB", s.rgb + (f", RAM {s.memory_type}" if s.rgb == "openlinkhub" and s.memory_rgb_enable else "")),
            (tr("Branch"), s.branch),
            (tr("Extras"), ", ".join(filter(None, [
                "GTA fix" if s.gta_fix else "",
                "Flatpak" if s.flatpak else "",
                tr("Virtualization") if s.virtualization else "",
                f"autoupdate {s.autoupdate_interval}" if s.autoupdate else "",
            ])) or trc("summary, Extras row: nothing selected", "none")),
            ("Bootloader", s.bootloader),
            ("Matrix", s.matrix_client),
            ("Discord", s.discord),
            ("Telegram", s.telegram),
            (tr("Video player"), s.video_player),
            (tr("Torrent client"), s.torrent_client),
            (tr("Music player"), s.music_player),
            (tr("Mail client"), s.mail_client),
            (tr("Password manager"), s.password_manager),
            ("Waydroid", tr("enabled") if s.waydroid_enable else tr("disabled")),
            ("Apps", ", ".join(filter(None, [
                "+ GIMP" if s.app_gimp else "",
                "+ Inkscape" if s.app_inkscape else "",
                "+ SongRec" if s.app_songrec else "",
                "+ EasyEffects" if s.app_easyeffects else "",
                "+ Signal" if s.app_signal else "",
                "+ ZapZap" if s.app_zapzap else "",
                "+ Fluxer" if s.app_fluxer else "",
            ])) or trc("summary, Apps row: nothing selected", "none")),
        ] + ([
            ("Spicetify", f"{s.spicetify_theme}"
                + (f" ({s.spicetify_color_scheme})" if s.spicetify_color_scheme else "")
                + " — " + (", ".join(filter(None, [
                    "adblock" if s.spicetify_adblock else "",
                    tr("hide podcasts") if s.spicetify_hide_podcasts else "",
                    "marketplace" if s.spicetify_marketplace else "",
                ])) or tr("no extensions"))),
        ] if s.music_player == "spotify" else []) + [
            (
                tr("Content Creation"),
                (
                    f"OBS ({obs_plugins}) — {s.video_editor}"
                    + (" — Chatterino" if s.chatterino_enable else "")
                )
                if s.content_creation_enable
                else tr("disabled"),
            ),
        ]
        for title, value in rows:
            row = Adw.ActionRow(title=title, subtitle=value)
            self.group.add(row)
            self._rows.append(row)
