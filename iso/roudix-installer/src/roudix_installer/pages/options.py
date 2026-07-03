from gi.repository import Adw, Gtk

from roudix_installer.i18n import L
from roudix_installer.ui_helpers import page_with_header

# ── Option lists, mirrored 1:1 from the pick() calls in roudix-installer.sh ──
# Built as functions (not module constants) so labels reflect whichever
# language was chosen on the Welcome page before this page is constructed.


def _kernels():
    return [
        ("cachyos-latest", L("Standard latest CachyOS kernel", "Standard latest CachyOS kernel")),
        ("cachyos-latest-v3", L("x86_64-v3 optimisé (recommandé, CPU récents)", "x86_64-v3 optimized (recommended, recent CPUs)")),
        ("cachyos-latest-lto", L("LTO — meilleures perfs", "LTO build — better performance")),
        ("cachyos-latest-lto-v3", L("LTO + x86_64-v3 (meilleures perfs, CPU récents)", "LTO + x86_64-v3 (best performance, recent CPUs)")),
        ("cachyos-lts", L("Support long terme", "Long-term support")),
        ("cachyos-lts-v3", "LTS + x86_64-v3"),
        ("cachyos-lts-lto-v3", L("LTS + LTO + x86_64-v3 (stable + perf)", "LTS + LTO + x86_64-v3 (stable + fast)")),
        ("cachyos-rc", L("Release candidate — bleeding edge", "Release candidate — bleeding edge")),
    ]


def _browsers():
    return [
        ("none", L("Aucun", "None")),
        ("brave", "Brave"), ("helium", "Helium"), ("vivaldi", "Vivaldi"),
        ("firefox", "Firefox"), ("librewolf", "LibreWolf"),
        ("google-chrome", "Google Chrome"), ("microsoft-edge", "Microsoft Edge"),
        ("ungoogled-chromium", "Ungoogled Chromium"), ("chromium", "Chromium"),
    ]


def _brave_variants():
    return [
        ("brave", L("Stable (recommandé)", "Stable (recommended)")),
        ("brave-beta", "Beta"), ("brave-nightly", "Nightly"),
        ("brave-origin-beta", "Origin Beta"), ("brave-origin-nightly", "Origin Nightly"),
    ]


def _desktops():
    return [("niri", "Niri"), ("gnome", "GNOME"), ("kde", "KDE Plasma"), ("hyprland", "Hyprland")]


def _shells(desktop_hint_hypr=True):
    base = [
        ("noctalia", L("Noctalia — shell par défaut", "Noctalia — default shell")),
        ("dms", "DankMaterialShell — Material 3"),
    ]
    if desktop_hint_hypr:
        base = base + [("caelestia", L("Caelestia — setup Quickshell", "Caelestia — Quickshell setup"))]
    return base


def _default_shells():
    return [("fish", L("Fish (recommandé)", "Fish (recommended)")), ("bash", "Bash")]


def _rgb_options():
    return [
        ("openlinkhub", "OpenLinkHub — Corsair (iCUE Link, Commander...)"),
        ("openrgb", L("OpenRGB — marques mixtes (Razer, ASUS, MSI...)", "OpenRGB — mixed brands (Razer, ASUS, MSI...)")),
        ("none", L("Aucune gestion RGB", "No RGB control")),
    ]


def _bootloaders():
    return [("limine", L("Limine (recommandé)", "Limine (recommended)")), ("systemd-boot", "systemd-boot")]


def _matrix():
    return [("none", L("Aucun", "None")), ("element", "Element Desktop"),
            ("cinny", L("Cinny (léger, web)", "Cinny (lightweight, web)"))]


def _timezones():
    return [
        ("Europe/Brussels", L("Belgique", "Belgium")), ("Europe/Paris", L("France", "France")),
        ("Europe/London", L("Royaume-Uni", "United Kingdom")), ("Europe/Amsterdam", L("Pays-Bas", "Netherlands")),
        ("Europe/Berlin", L("Allemagne", "Germany")), ("Europe/Zurich", L("Suisse", "Switzerland")),
        ("Europe/Madrid", L("Espagne", "Spain")), ("Europe/Rome", L("Italie", "Italy")),
        ("Europe/Warsaw", L("Pologne", "Poland")), ("Europe/Lisbon", L("Portugal", "Portugal")),
        ("Europe/Stockholm", L("Suède", "Sweden")), ("Europe/Oslo", L("Norvège", "Norway")),
        ("Europe/Copenhagen", L("Danemark", "Denmark")), ("Europe/Helsinki", L("Finlande", "Finland")),
        ("Europe/Athens", L("Grèce", "Greece")), ("Europe/Istanbul", L("Turquie", "Turkey")),
        ("Africa/Casablanca", L("Maroc", "Morocco")), ("Africa/Cairo", L("Égypte", "Egypt")),
        ("America/New_York", L("États-Unis (Est)", "United States (East)")),
        ("America/Chicago", L("États-Unis (Centre)", "United States (Central)")),
        ("America/Los_Angeles", L("États-Unis (Ouest)", "United States (West)")),
        ("America/Toronto", L("Canada (Est)", "Canada (East)")), ("America/Sao_Paulo", L("Brésil", "Brazil")),
        ("Asia/Dubai", L("Émirats Arabes Unis", "United Arab Emirates")), ("Asia/Kolkata", L("Inde", "India")),
        ("Asia/Shanghai", L("Chine", "China")), ("Asia/Tokyo", L("Japon", "Japan")),
        ("Asia/Seoul", L("Corée du Sud", "South Korea")),
        ("Australia/Sydney", L("Australie (Est)", "Australia (East)")),
        ("Pacific/Auckland", L("Nouvelle-Zélande", "New Zealand")), ("UTC", "UTC"),
    ]


def _locales():
    return [
        ("fr_BE.UTF-8", "Français (Belgique)"), ("fr_FR.UTF-8", "Français (France)"),
        ("fr_CH.UTF-8", "Français (Suisse)"), ("en_US.UTF-8", "English (US)"),
        ("en_GB.UTF-8", "English (UK)"), ("de_DE.UTF-8", "Deutsch (Deutschland)"),
        ("nl_BE.UTF-8", "Nederlands (België)"), ("nl_NL.UTF-8", "Nederlands (Nederland)"),
        ("es_ES.UTF-8", "Español (España)"), ("pt_PT.UTF-8", "Português (Portugal)"),
        ("it_IT.UTF-8", "Italiano (Italia)"), ("pl_PL.UTF-8", "Polski (Polska)"),
        ("ru_RU.UTF-8", "Русский (Россия)"), ("ja_JP.UTF-8", "日本語"), ("zh_CN.UTF-8", "中文 (大陆)"),
        ("ko_KR.UTF-8", "한국어"), ("C.UTF-8", L("C (POSIX minimal)", "C (minimal POSIX)")),
    ]


def _keymaps():
    return [
        ("be-latin1", L("Belge AZERTY", "Belgian AZERTY")),
        ("fr", L("Français AZERTY", "French AZERTY")),
        ("fr-latin9", L("Français AZERTY (latin9)", "French AZERTY (latin9)")),
        ("us", "English (US) QWERTY"),
        ("us-acentos", L("English (US) International (touches mortes)", "English (US) International (dead keys)")),
        ("uk", "English (UK) QWERTY"),
        ("de", L("Allemand QWERTZ", "German QWERTZ")), ("ch", L("Suisse QWERTZ", "Swiss QWERTZ")),
        ("nl", L("Néerlandais QWERTY", "Dutch QWERTY")), ("es", L("Espagnol QWERTY", "Spanish QWERTY")),
        ("it", L("Italien QWERTY", "Italian QWERTY")), ("pt-latin1", L("Portugais QWERTY", "Portuguese QWERTY")),
        ("pl2", L("Polonais QWERTY", "Polish QWERTY")), ("ru", L("Russe", "Russian")),
        ("jp106", L("Japonais 106 touches", "Japanese 106-key")),
        ("dvorak", "Dvorak (US)"), ("colemak", "Colemak"),
    ]


class OptionsPage(Adw.NavigationPage):
    def __init__(self, state, on_next):
        super().__init__(title=L("Options", "Options"))
        self.state = state
        self.on_next = on_next
        self._rows = {}  # id(row) -> value list

        scroller = Gtk.ScrolledWindow(vexpand=True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                       margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)
        scroller.set_child(box)

        # ── Utilisateur ──
        user_group = Adw.PreferencesGroup(title=L("Utilisateur", "User"))
        self.username_row = Adw.EntryRow(title=L("Nom d'utilisateur", "Username"))
        self.username_row.set_text(state.username)
        user_group.add(self.username_row)
        box.append(user_group)

        # ── Matériel ──
        hw_group = Adw.PreferencesGroup(title=L("Matériel", "Hardware"))
        self.gpu_row = self._combo(L("GPU", "GPU"), [
            ("amd", "AMD — RDNA / GCN 3+"), ("amd-legacy", L("AMD legacy — GCN 1.x/2.x", "AMD legacy — GCN 1.x/2.x")),
            ("nvidia", "NVIDIA"), ("intel", L("Intel intégré", "Intel integrated")),
        ], state.gpu)
        self.gpu_row.connect("notify::selected", lambda *_: self._sync_nvidia_row())
        hw_group.add(self.gpu_row)

        self.nvidia_laptop_row = Adw.SwitchRow(title=L(
            "Laptop Optimus (Intel/AMD + NVIDIA dGPU)", "Optimus laptop (Intel/AMD + NVIDIA dGPU)"))
        self.nvidia_laptop_row.set_active(state.nvidia_laptop)
        hw_group.add(self.nvidia_laptop_row)

        self.cpu_row = self._combo("CPU", [("amd", "AMD"), ("intel", "Intel")], state.cpu)
        hw_group.add(self.cpu_row)

        self.kernel_row = self._combo(L("Kernel", "Kernel"), _kernels(), state.kernel)
        hw_group.add(self.kernel_row)
        box.append(hw_group)
        self._sync_nvidia_row()

        # ── Navigateur ──
        browser_group = Adw.PreferencesGroup(title=L("Navigateur", "Browser"))
        browsers = _browsers()
        self.browser_row = self._combo(L("Navigateur", "Browser"), browsers,
                                        state.browser if state.browser in dict(browsers) else "brave")
        self.browser_row.connect("notify::selected", lambda *_: self._sync_brave_row())
        browser_group.add(self.browser_row)

        self.brave_variant_row = self._combo(L("Variante Brave", "Brave variant"), _brave_variants(), "brave")
        browser_group.add(self.brave_variant_row)

        self.zen_row = Adw.SwitchRow(title=L("Installer Zen Browser (en plus)", "Also install Zen Browser"))
        self.zen_row.set_active(state.zen_browser)
        browser_group.add(self.zen_row)
        box.append(browser_group)
        self._sync_brave_row()

        # ── Bureau ──
        desktop_group = Adw.PreferencesGroup(title=L("Bureau", "Desktop"))
        self.desktop_row = self._combo(L("Compositeur / bureau", "Compositor / desktop"), _desktops(), state.desktop)
        self.desktop_row.connect("notify::selected", lambda *_: self._sync_shell_row())
        desktop_group.add(self.desktop_row)

        self.shell_row = self._combo(L("Shell graphique (bar/UI)", "Graphical shell (bar/UI)"), _shells(), state.desktop_shell)
        desktop_group.add(self.shell_row)

        self.default_shell_row = self._combo(L("Shell par défaut", "Default shell"), _default_shells(), state.default_shell)
        desktop_group.add(self.default_shell_row)
        box.append(desktop_group)
        self._sync_shell_row()

        # ── Système ──
        sys_group = Adw.PreferencesGroup(title=L("Système", "System"))
        self.vm_guest_row = Adw.SwitchRow(title=L("Installation dans une VM", "Installing inside a VM"))
        self.vm_guest_row.set_active(state.vm_guest)
        sys_group.add(self.vm_guest_row)

        self.gaming_row = Adw.SwitchRow(title=L("Paquets gaming (Steam, Wine, Lutris…)", "Gaming packages (Steam, Wine, Lutris…)"))
        self.gaming_row.set_active(state.gaming)
        sys_group.add(self.gaming_row)

        self.timezone_row = self._combo(L("Fuseau horaire", "Timezone"), _timezones(), state.timezone)
        sys_group.add(self.timezone_row)

        self.locale_row = self._combo(L("Langue système", "System language"), _locales(), state.locale)
        sys_group.add(self.locale_row)

        self.keymap_row = self._combo(L("Disposition clavier (console)", "Keyboard layout (console)"), _keymaps(), state.keymap)
        sys_group.add(self.keymap_row)
        box.append(sys_group)

        # ── RGB ──
        rgb_group = Adw.PreferencesGroup(title="RGB")
        self.rgb_row = self._combo(L("Contrôleur RGB", "RGB controller"), _rgb_options(), state.rgb)
        self.rgb_row.connect("notify::selected", lambda *_: self._sync_memory_rows())
        rgb_group.add(self.rgb_row)

        self.memory_rgb_row = Adw.SwitchRow(title=L("RGB RAM (Corsair DDR4/DDR5)", "RAM RGB (Corsair DDR4/DDR5)"))
        self.memory_rgb_row.set_active(state.memory_rgb_enable)
        rgb_group.add(self.memory_rgb_row)

        self.memory_type_row = self._combo(L("Type de RAM", "RAM type"), [("ddr5", "DDR5"), ("ddr4", "DDR4")], state.memory_type)
        rgb_group.add(self.memory_type_row)
        box.append(rgb_group)
        self._sync_memory_rows()

        rgb_note = Gtk.Label(
            label=L(
                "Détection SMBus / SKU RAM non automatisée ici — éditable dans local.nix après install.",
                "SMBus / RAM SKU detection isn't automated here — editable in local.nix after install.",
            ),
            css_classes=["dim-label", "caption"], wrap=True, xalign=0,
        )
        box.append(rgb_note)

        # ── Extras ──
        extra_group = Adw.PreferencesGroup(title=L("Extras", "Extras"))
        self.gta_fix_row = Adw.SwitchRow(title=L(
            "Fix GTA Online (bloque l'IP anti-cheat Linux)", "GTA Online fix (blocks the Linux anti-cheat IP)"))
        self.gta_fix_row.set_active(state.gta_fix)
        extra_group.add(self.gta_fix_row)

        self.flatpak_row = Adw.SwitchRow(title="Flatpak")
        self.flatpak_row.set_active(state.flatpak)
        extra_group.add(self.flatpak_row)

        self.virt_row = Adw.SwitchRow(title=L("Virtualisation (libvirt, virt-manager)", "Virtualization (libvirt, virt-manager)"))
        self.virt_row.set_active(state.virtualization)
        extra_group.add(self.virt_row)

        self.autoupdate_row = Adw.SwitchRow(title=L("Mises à jour automatiques", "Automatic updates"))
        self.autoupdate_row.set_active(state.autoupdate)
        self.autoupdate_row.connect("notify::active", lambda *_: self._sync_autoupdate_row())
        extra_group.add(self.autoupdate_row)

        self.autoupdate_interval_row = Adw.EntryRow(title=L("Intervalle (ex: 1h, 6h, 24h)", "Interval (e.g. 1h, 6h, 24h)"))
        self.autoupdate_interval_row.set_text(state.autoupdate_interval)
        extra_group.add(self.autoupdate_interval_row)

        self.bootloader_row = self._combo(L("Bootloader", "Bootloader"), _bootloaders(), state.bootloader)
        extra_group.add(self.bootloader_row)

        self.matrix_row = self._combo(L("Client Matrix", "Matrix client"), _matrix(), state.matrix_client)
        extra_group.add(self.matrix_row)

        self.waydroid_row = Adw.SwitchRow(title="Waydroid (Android)")
        self.waydroid_row.set_active(state.waydroid_enable)
        extra_group.add(self.waydroid_row)
        box.append(extra_group)
        self._sync_autoupdate_row()

        next_btn = Gtk.Button(label=L("Continuer", "Continue"), css_classes=["suggested-action", "pill"],
                               halign=Gtk.Align.END, margin_top=12)
        next_btn.connect("clicked", self._validate)
        box.append(next_btn)

        self.set_child(page_with_header(L("Options", "Options"), scroller))

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
