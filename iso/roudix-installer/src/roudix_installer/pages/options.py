from gi.repository import Adw, Gtk

from roudix_installer.ui_helpers import page_with_header

# ── Option lists, mirrored 1:1 from the pick() calls in roudix-installer.sh ──

KERNELS = [
    ("cachyos-latest", "Standard latest CachyOS kernel"),
    ("cachyos-latest-v3", "x86_64-v3 optimized (recommandé, CPU récents)"),
    ("cachyos-latest-lto", "LTO build — meilleures perfs"),
    ("cachyos-latest-lto-v3", "LTO + x86_64-v3 (meilleures perfs, CPU récents)"),
    ("cachyos-lts", "Long-term support"),
    ("cachyos-lts-v3", "LTS + x86_64-v3"),
    ("cachyos-lts-lto-v3", "LTS + LTO + x86_64-v3 (stable + perf)"),
    ("cachyos-rc", "Release candidate — bleeding edge"),
]

BROWSERS = [
    ("none", "Aucun"),
    ("brave", "Brave"),
    ("helium", "Helium"),
    ("vivaldi", "Vivaldi"),
    ("firefox", "Firefox"),
    ("librewolf", "LibreWolf"),
    ("google-chrome", "Google Chrome"),
    ("microsoft-edge", "Microsoft Edge"),
    ("ungoogled-chromium", "Ungoogled Chromium"),
    ("chromium", "Chromium"),
]

BRAVE_VARIANTS = [
    ("brave", "Stable (recommandé)"),
    ("brave-beta", "Beta"),
    ("brave-nightly", "Nightly"),
    ("brave-origin-beta", "Origin Beta"),
    ("brave-origin-nightly", "Origin Nightly"),
]

DESKTOPS = [("niri", "Niri"), ("gnome", "GNOME"), ("kde", "KDE Plasma"), ("hyprland", "Hyprland")]
SHELLS_NIRI = [("noctalia", "Noctalia — shell par défaut"), ("dms", "DankMaterialShell — Material 3")]
SHELLS_HYPR = SHELLS_NIRI + [("caelestia", "Caelestia — setup Quickshell")]
DEFAULT_SHELLS = [("fish", "Fish (recommandé)"), ("bash", "Bash")]

RGB_OPTIONS = [
    ("openlinkhub", "OpenLinkHub — Corsair (iCUE Link, Commander...)"),
    ("openrgb", "OpenRGB — marques mixtes (Razer, ASUS, MSI...)"),
    ("none", "Aucune gestion RGB"),
]

BOOTLOADERS = [("limine", "Limine (recommandé)"), ("systemd-boot", "systemd-boot")]
MATRIX = [("none", "Aucun"), ("element", "Element Desktop"), ("cinny", "Cinny (léger, web)")]

TIMEZONES = [
    ("Europe/Brussels", "Belgique"), ("Europe/Paris", "France"), ("Europe/London", "Royaume-Uni"),
    ("Europe/Amsterdam", "Pays-Bas"), ("Europe/Berlin", "Allemagne"), ("Europe/Zurich", "Suisse"),
    ("Europe/Madrid", "Espagne"), ("Europe/Rome", "Italie"), ("Europe/Warsaw", "Pologne"),
    ("Europe/Lisbon", "Portugal"), ("Europe/Stockholm", "Suède"), ("Europe/Oslo", "Norvège"),
    ("Europe/Copenhagen", "Danemark"), ("Europe/Helsinki", "Finlande"), ("Europe/Athens", "Grèce"),
    ("Europe/Istanbul", "Turquie"), ("Africa/Casablanca", "Maroc"), ("Africa/Cairo", "Égypte"),
    ("America/New_York", "États-Unis (Est)"), ("America/Chicago", "États-Unis (Centre)"),
    ("America/Los_Angeles", "États-Unis (Ouest)"), ("America/Toronto", "Canada (Est)"),
    ("America/Sao_Paulo", "Brésil"), ("Asia/Dubai", "Émirats Arabes Unis"),
    ("Asia/Kolkata", "Inde"), ("Asia/Shanghai", "Chine"), ("Asia/Tokyo", "Japon"),
    ("Asia/Seoul", "Corée du Sud"), ("Australia/Sydney", "Australie (Est)"),
    ("Pacific/Auckland", "Nouvelle-Zélande"), ("UTC", "UTC"),
]

LOCALES = [
    ("fr_BE.UTF-8", "Français (Belgique)"), ("fr_FR.UTF-8", "Français (France)"),
    ("fr_CH.UTF-8", "Français (Suisse)"), ("en_US.UTF-8", "English (US)"),
    ("en_GB.UTF-8", "English (UK)"), ("de_DE.UTF-8", "Deutsch (Deutschland)"),
    ("nl_BE.UTF-8", "Nederlands (België)"), ("nl_NL.UTF-8", "Nederlands (Nederland)"),
    ("es_ES.UTF-8", "Español (España)"), ("pt_PT.UTF-8", "Português (Portugal)"),
    ("it_IT.UTF-8", "Italiano (Italia)"), ("pl_PL.UTF-8", "Polski (Polska)"),
    ("ru_RU.UTF-8", "Русский (Россия)"), ("ja_JP.UTF-8", "日本語"), ("zh_CN.UTF-8", "中文 (大陆)"),
    ("ko_KR.UTF-8", "한국어"), ("C.UTF-8", "C (POSIX minimal)"),
]

KEYMAPS = [
    ("be-latin1", "Belge AZERTY"), ("fr", "Français AZERTY"), ("fr-latin9", "Français AZERTY (latin9)"),
    ("us", "English (US) QWERTY"), ("us-acentos", "English (US) International (touches mortes)"),
    ("uk", "English (UK) QWERTY"),
    ("de", "Allemand QWERTZ"), ("ch", "Suisse QWERTZ"), ("nl", "Néerlandais QWERTY"),
    ("es", "Espagnol QWERTY"), ("it", "Italien QWERTY"), ("pt-latin1", "Portugais QWERTY"),
    ("pl2", "Polonais QWERTY"), ("ru", "Russe"), ("jp106", "Japonais 106 touches"),
    ("dvorak", "Dvorak (US)"), ("colemak", "Colemak"),
]


class OptionsPage(Adw.NavigationPage):
    def __init__(self, state, on_next):
        super().__init__(title="Options")
        self.state = state
        self.on_next = on_next
        self._rows = {}  # field name -> (ComboRow, value list)

        scroller = Gtk.ScrolledWindow(vexpand=True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                       margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)
        scroller.set_child(box)

        # ── Utilisateur ──
        user_group = Adw.PreferencesGroup(title="Utilisateur")
        self.username_row = Adw.EntryRow(title="Nom d'utilisateur")
        self.username_row.set_text(state.username)
        user_group.add(self.username_row)
        box.append(user_group)

        # ── Matériel ──
        hw_group = Adw.PreferencesGroup(title="Matériel")
        self.gpu_row = self._combo("GPU", [
            ("amd", "AMD — RDNA / GCN 3+"), ("amd-legacy", "AMD legacy — GCN 1.x/2.x"),
            ("nvidia", "NVIDIA"), ("intel", "Intel intégré"),
        ], state.gpu)
        self.gpu_row.connect("notify::selected", lambda *_: self._sync_nvidia_row())
        hw_group.add(self.gpu_row)

        self.nvidia_laptop_row = Adw.SwitchRow(title="Laptop Optimus (Intel/AMD + NVIDIA dGPU)")
        self.nvidia_laptop_row.set_active(state.nvidia_laptop)
        hw_group.add(self.nvidia_laptop_row)

        self.cpu_row = self._combo("CPU", [("amd", "AMD"), ("intel", "Intel")], state.cpu)
        hw_group.add(self.cpu_row)

        self.kernel_row = self._combo("Kernel", KERNELS, state.kernel)
        hw_group.add(self.kernel_row)
        box.append(hw_group)
        self._sync_nvidia_row()

        # ── Navigateur ──
        browser_group = Adw.PreferencesGroup(title="Navigateur")
        self.browser_row = self._combo("Navigateur", BROWSERS, state.browser
                                        if state.browser in dict(BROWSERS) else "brave")
        self.browser_row.connect("notify::selected", lambda *_: self._sync_brave_row())
        browser_group.add(self.browser_row)

        self.brave_variant_row = self._combo("Variante Brave", BRAVE_VARIANTS, "brave")
        browser_group.add(self.brave_variant_row)

        self.zen_row = Adw.SwitchRow(title="Installer Zen Browser (en plus)")
        self.zen_row.set_active(state.zen_browser)
        browser_group.add(self.zen_row)
        box.append(browser_group)
        self._sync_brave_row()

        # ── Bureau ──
        desktop_group = Adw.PreferencesGroup(title="Bureau")
        self.desktop_row = self._combo("Compositeur / bureau", DESKTOPS, state.desktop)
        self.desktop_row.connect("notify::selected", lambda *_: self._sync_shell_row())
        desktop_group.add(self.desktop_row)

        self.shell_row = self._combo("Shell graphique (bar/UI)", SHELLS_HYPR, state.desktop_shell)
        desktop_group.add(self.shell_row)

        self.default_shell_row = self._combo("Shell par défaut", DEFAULT_SHELLS, state.default_shell)
        desktop_group.add(self.default_shell_row)
        box.append(desktop_group)
        self._sync_shell_row()

        # ── Système ──
        sys_group = Adw.PreferencesGroup(title="Système")
        self.vm_guest_row = Adw.SwitchRow(title="Installation dans une VM")
        self.vm_guest_row.set_active(state.vm_guest)
        sys_group.add(self.vm_guest_row)

        self.gaming_row = Adw.SwitchRow(title="Paquets gaming (Steam, Wine, Lutris…)")
        self.gaming_row.set_active(state.gaming)
        sys_group.add(self.gaming_row)

        self.timezone_row = self._combo("Fuseau horaire", TIMEZONES, state.timezone)
        sys_group.add(self.timezone_row)

        self.locale_row = self._combo("Langue système", LOCALES, state.locale)
        sys_group.add(self.locale_row)

        self.keymap_row = self._combo("Disposition clavier (console)", KEYMAPS, state.keymap)
        sys_group.add(self.keymap_row)
        box.append(sys_group)

        # ── RGB ──
        rgb_group = Adw.PreferencesGroup(title="RGB")
        self.rgb_row = self._combo("Contrôleur RGB", RGB_OPTIONS, state.rgb)
        self.rgb_row.connect("notify::selected", lambda *_: self._sync_memory_rows())
        rgb_group.add(self.rgb_row)

        self.memory_rgb_row = Adw.SwitchRow(title="RGB RAM (Corsair DDR4/DDR5)")
        self.memory_rgb_row.set_active(state.memory_rgb_enable)
        rgb_group.add(self.memory_rgb_row)

        self.memory_type_row = self._combo("Type de RAM", [("ddr5", "DDR5"), ("ddr4", "DDR4")], state.memory_type)
        rgb_group.add(self.memory_type_row)
        box.append(rgb_group)
        self._sync_memory_rows()

        rgb_note = Gtk.Label(
            label="Détection SMBus / SKU RAM non automatisée ici — éditable dans local.nix après install.",
            css_classes=["dim-label", "caption"], wrap=True, xalign=0,
        )
        box.append(rgb_note)

        # ── Extras ──
        extra_group = Adw.PreferencesGroup(title="Extras")
        self.gta_fix_row = Adw.SwitchRow(title="Fix GTA Online (bloque l'IP anti-cheat Linux)")
        self.gta_fix_row.set_active(state.gta_fix)
        extra_group.add(self.gta_fix_row)

        self.flatpak_row = Adw.SwitchRow(title="Flatpak")
        self.flatpak_row.set_active(state.flatpak)
        extra_group.add(self.flatpak_row)

        self.virt_row = Adw.SwitchRow(title="Virtualisation (libvirt, virt-manager)")
        self.virt_row.set_active(state.virtualization)
        extra_group.add(self.virt_row)

        self.autoupdate_row = Adw.SwitchRow(title="Mises à jour automatiques")
        self.autoupdate_row.set_active(state.autoupdate)
        self.autoupdate_row.connect("notify::active", lambda *_: self._sync_autoupdate_row())
        extra_group.add(self.autoupdate_row)

        self.autoupdate_interval_row = Adw.EntryRow(title="Intervalle (ex: 1h, 6h, 24h)")
        self.autoupdate_interval_row.set_text(state.autoupdate_interval)
        extra_group.add(self.autoupdate_interval_row)

        self.bootloader_row = self._combo("Bootloader", BOOTLOADERS, state.bootloader)
        extra_group.add(self.bootloader_row)

        self.matrix_row = self._combo("Client Matrix", MATRIX, state.matrix_client)
        extra_group.add(self.matrix_row)

        self.waydroid_row = Adw.SwitchRow(title="Waydroid (Android)")
        self.waydroid_row.set_active(state.waydroid_enable)
        extra_group.add(self.waydroid_row)
        box.append(extra_group)
        self._sync_autoupdate_row()

        next_btn = Gtk.Button(label="Continuer", css_classes=["suggested-action", "pill"],
                               halign=Gtk.Align.END, margin_top=12)
        next_btn.connect("clicked", self._validate)
        box.append(next_btn)

        self.set_child(page_with_header("Options", scroller))

    # ── helpers ──────────────────────────────────────────────────────────

    def _combo(self, title, pairs, current_value):
        values = [v for v, _ in pairs]
        labels = [l for _, l in pairs]
        row = Adw.ComboRow(title=title, model=Gtk.StringList.new(labels))
        row.set_selected(values.index(current_value) if current_value in values else 0)
        self._rows[id(row)] = values
        return row

    def _selected_value(self, row):
        return self._rows[id(row)][row.get_selected()]

    def _sync_nvidia_row(self):
        self.nvidia_laptop_row.set_visible(self._selected_value(self.gpu_row) == "nvidia")

    def _sync_brave_row(self):
        self.brave_variant_row.set_visible(self._selected_value(self.browser_row) == "brave")

    def _sync_shell_row(self):
        desktop = self._selected_value(self.desktop_row)
        self.shell_row.set_visible(desktop in ("niri", "hyprland"))

    def _sync_memory_rows(self):
        is_openlinkhub = self._selected_value(self.rgb_row) == "openlinkhub"
        self.memory_rgb_row.set_visible(is_openlinkhub)
        self.memory_type_row.set_visible(is_openlinkhub and self.memory_rgb_row.get_active())

    def _sync_autoupdate_row(self):
        self.autoupdate_interval_row.set_visible(self.autoupdate_row.get_active())

    def _validate(self, _btn):
        s = self.state
        s.username = self.username_row.get_text()
        s.gpu = self._selected_value(self.gpu_row)
        s.nvidia_laptop = self.nvidia_laptop_row.get_active()
        s.cpu = self._selected_value(self.cpu_row)
        s.kernel = self._selected_value(self.kernel_row)

        browser = self._selected_value(self.browser_row)
        s.browser = self._selected_value(self.brave_variant_row) if browser == "brave" else browser
        s.zen_browser = self.zen_row.get_active()

        s.desktop = self._selected_value(self.desktop_row)
        s.desktop_shell = self._selected_value(self.shell_row)
        s.default_shell = self._selected_value(self.default_shell_row)

        s.vm_guest = self.vm_guest_row.get_active()
        s.gaming = self.gaming_row.get_active()
        s.timezone = self._selected_value(self.timezone_row)
        s.locale = self._selected_value(self.locale_row)
        s.keymap = self._selected_value(self.keymap_row)

        s.rgb = self._selected_value(self.rgb_row)
        s.memory_rgb_enable = self.memory_rgb_row.get_active()
        s.memory_type = self._selected_value(self.memory_type_row)

        s.gta_fix = self.gta_fix_row.get_active()
        s.flatpak = self.flatpak_row.get_active()
        s.virtualization = self.virt_row.get_active()
        s.autoupdate = self.autoupdate_row.get_active()
        s.autoupdate_interval = self.autoupdate_interval_row.get_text()
        s.bootloader = self._selected_value(self.bootloader_row)
        s.matrix_client = self._selected_value(self.matrix_row)
        s.waydroid_enable = self.waydroid_row.get_active()

        self.on_next()
