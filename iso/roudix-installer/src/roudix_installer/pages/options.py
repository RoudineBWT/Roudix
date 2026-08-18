from gi.repository import Adw, Gtk

from roudix_installer.i18n import L
from roudix_installer.ui_helpers import page_with_header

# ── Option lists, mirrored 1:1 from the pick() calls in roudix-installer.sh ──
# Built as functions (not module constants) so labels reflect whichever
# language was chosen on the Welcome page before this page is constructed.


def _kernels():
    return [
        (
            "cachyos-latest",
            L("Standard latest CachyOS kernel", "Standard latest CachyOS kernel"),
        ),
        (
            "cachyos-latest-v3",
            L(
                "x86_64-v3 optimisé (recommandé, CPU récents)",
                "x86_64-v3 optimized (recommended, recent CPUs)",
            ),
        ),
        (
            "cachyos-latest-lto",
            L("LTO — meilleures perfs", "LTO build — better performance"),
        ),
        (
            "cachyos-latest-lto-v3",
            L(
                "LTO + x86_64-v3 (meilleures perfs, CPU récents)",
                "LTO + x86_64-v3 (best performance, recent CPUs)",
            ),
        ),
        ("cachyos-lts", L("Support long terme", "Long-term support")),
        ("cachyos-lts-v3", "LTS + x86_64-v3"),
        (
            "cachyos-lts-lto-v3",
            L(
                "LTS + LTO + x86_64-v3 (stable + perf)",
                "LTS + LTO + x86_64-v3 (stable + fast)",
            ),
        ),
        (
            "cachyos-rc",
            L("Release candidate — bleeding edge", "Release candidate — bleeding edge"),
        ),
    ]


def _kernels_chaotic():
    # Chaotic-Nyx — set volontairement plus réduit que xddxdd (pas de LTO ici :
    # les modules hors-arbre comme nvidia y sont plus fragiles). Requis pour
    # nvidia_cachyos, le driver Nvidia précompilé matché à ce kernel.
    return [
        ("cachyos", L("Par défaut — LTO + BORE", "Default — LTO + BORE")),
        ("cachyos-lts", L("Support long terme", "Long-term support")),
        ("cachyos-server", L("Optimisé serveur (pas de tuning desktop)", "Server optimized (no desktop tuning)")),
        ("cachyos-hardened", L("Sécurité renforcée", "Security hardened")),
    ]


def _browsers():
    return [
        ("none", L("Aucun", "None")),
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


def _brave_variants():
    return [
        ("brave", L("Stable (recommandé)", "Stable (recommended)")),
        ("brave-beta", "Beta"),
        ("brave-nightly", "Nightly"),
        ("brave-origin", "Origin Stable"),
        ("brave-origin-beta", "Origin Beta"),
        ("brave-origin-nightly", "Origin Nightly"),
    ]


def _desktops():
    return [
        ("niri", "Niri"),
        ("gnome", "GNOME"),
        ("kde", "KDE Plasma"),
        ("hyprland", "Hyprland"),
    ]


def _shells(desktop_hint_hypr=True):
    base = [
        ("noctalia", L("Noctalia — shell par défaut", "Noctalia — default shell")),
        ("dms", "DankMaterialShell — Material 3"),
    ]
    if desktop_hint_hypr:
        base = base + [
            (
                "caelestia",
                L("Caelestia — setup Quickshell", "Caelestia — Quickshell setup"),
            )
        ]
    return base


def _default_shells():
    return [("fish", L("Fish (recommandé)", "Fish (recommended)")), ("bash", "Bash")]


def _terminals():
    return [
        ("ghostty", L("Ghostty (recommandé)", "Ghostty (recommended)")),
        ("kitty", "Kitty"),
        ("alacritty", "Alacritty"),
        ("foot", L("Foot (natif Wayland, léger)", "Foot (native Wayland, lightweight)")),
        ("wezterm", "WezTerm"),
    ]


def _rgb_options():
    return [
        ("openlinkhub", "OpenLinkHub — Corsair (iCUE Link, Commander...)"),
        (
            "openrgb",
            L(
                "OpenRGB — marques mixtes (Razer, ASUS, MSI...)",
                "OpenRGB — mixed brands (Razer, ASUS, MSI...)",
            ),
        ),
        ("none", L("Aucune gestion RGB", "No RGB control")),
    ]


def _bootloaders():
    return [
        ("limine", L("Limine (recommandé)", "Limine (recommended)")),
        ("systemd-boot", "systemd-boot"),
    ]


def _matrix():
    return [
        ("none", L("Aucun", "None")),
        ("element", "Element Desktop"),
        ("cinny", L("Cinny (léger, web)", "Cinny (lightweight, web)")),
    ]


def _timezones():
    return [
        ("Europe/Brussels", L("Belgique", "Belgium")),
        ("Europe/Paris", L("France", "France")),
        ("Europe/London", L("Royaume-Uni", "United Kingdom")),
        ("Europe/Amsterdam", L("Pays-Bas", "Netherlands")),
        ("Europe/Berlin", L("Allemagne", "Germany")),
        ("Europe/Zurich", L("Suisse", "Switzerland")),
        ("Europe/Madrid", L("Espagne", "Spain")),
        ("Europe/Rome", L("Italie", "Italy")),
        ("Europe/Warsaw", L("Pologne", "Poland")),
        ("Europe/Lisbon", L("Portugal", "Portugal")),
        ("Europe/Stockholm", L("Suède", "Sweden")),
        ("Europe/Oslo", L("Norvège", "Norway")),
        ("Europe/Copenhagen", L("Danemark", "Denmark")),
        ("Europe/Helsinki", L("Finlande", "Finland")),
        ("Europe/Athens", L("Grèce", "Greece")),
        ("Europe/Istanbul", L("Turquie", "Turkey")),
        ("Africa/Casablanca", L("Maroc", "Morocco")),
        ("Africa/Cairo", L("Égypte", "Egypt")),
        ("America/New_York", L("États-Unis (Est)", "United States (East)")),
        ("America/Chicago", L("États-Unis (Centre)", "United States (Central)")),
        ("America/Los_Angeles", L("États-Unis (Ouest)", "United States (West)")),
        ("America/Toronto", L("Canada (Est)", "Canada (East)")),
        ("America/Sao_Paulo", L("Brésil", "Brazil")),
        ("Asia/Dubai", L("Émirats Arabes Unis", "United Arab Emirates")),
        ("Asia/Kolkata", L("Inde", "India")),
        ("Asia/Shanghai", L("Chine", "China")),
        ("Asia/Tokyo", L("Japon", "Japan")),
        ("Asia/Seoul", L("Corée du Sud", "South Korea")),
        ("Australia/Sydney", L("Australie (Est)", "Australia (East)")),
        ("Pacific/Auckland", L("Nouvelle-Zélande", "New Zealand")),
        ("UTC", "UTC"),
    ]


def _locales():
    return [
        ("fr_BE.UTF-8", "Français (Belgique)"),
        ("fr_FR.UTF-8", "Français (France)"),
        ("fr_CH.UTF-8", "Français (Suisse)"),
        ("en_US.UTF-8", "English (US)"),
        ("en_GB.UTF-8", "English (UK)"),
        ("de_DE.UTF-8", "Deutsch (Deutschland)"),
        ("nl_BE.UTF-8", "Nederlands (België)"),
        ("nl_NL.UTF-8", "Nederlands (Nederland)"),
        ("es_ES.UTF-8", "Español (España)"),
        ("pt_PT.UTF-8", "Português (Portugal)"),
        ("it_IT.UTF-8", "Italiano (Italia)"),
        ("pl_PL.UTF-8", "Polski (Polska)"),
        ("ru_RU.UTF-8", "Русский (Россия)"),
        ("ja_JP.UTF-8", "日本語"),
        ("zh_CN.UTF-8", "中文 (大陆)"),
        ("ko_KR.UTF-8", "한국어"),
        ("C.UTF-8", L("C (POSIX minimal)", "C (minimal POSIX)")),
    ]


def _keymaps():
    return [
        ("be-latin1", L("Belge AZERTY", "Belgian AZERTY")),
        ("fr", L("Français AZERTY", "French AZERTY")),
        ("fr-latin9", L("Français AZERTY (latin9)", "French AZERTY (latin9)")),
        ("us", "English (US) QWERTY"),
        (
            "us-acentos",
            L(
                "English (US) International (touches mortes)",
                "English (US) International (dead keys)",
            ),
        ),
        ("uk", "English (UK) QWERTY"),
        ("de", L("Allemand QWERTZ", "German QWERTZ")),
        ("ch", L("Suisse QWERTZ", "Swiss QWERTZ")),
        ("nl", L("Néerlandais QWERTY", "Dutch QWERTY")),
        ("es", L("Espagnol QWERTY", "Spanish QWERTY")),
        ("it", L("Italien QWERTY", "Italian QWERTY")),
        ("pt-latin1", L("Portugais QWERTY", "Portuguese QWERTY")),
        ("pl2", L("Polonais QWERTY", "Polish QWERTY")),
        ("ru", L("Russe", "Russian")),
        ("jp106", L("Japonais 106 touches", "Japanese 106-key")),
        ("dvorak", "Dvorak (US)"),
        ("colemak", "Colemak"),
    ]


class OptionsPage(Adw.NavigationPage):
    def __init__(self, state, on_next):
        super().__init__(title=L("Options", "Options"))
        self.state = state
        self.on_next = on_next
        self._rows = {}  # id(row) -> value list

        scroller = Gtk.ScrolledWindow(vexpand=True)
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16,
            margin_top=24,
            margin_bottom=24,
            margin_start=24,
            margin_end=24,
        )
        scroller.set_child(box)

        # ── Utilisateur ──
        user_group = Adw.PreferencesGroup(title=L("Utilisateur", "User"))
        self.username_row = Adw.EntryRow(title=L("Nom d'utilisateur", "Username"))
        self.username_row.set_text(state.username)
        user_group.add(self.username_row)

        self.password_row = Adw.PasswordEntryRow(title=L("Mot de passe", "Password"))
        user_group.add(self.password_row)

        self.password_confirm_row = Adw.PasswordEntryRow(
            title=L("Confirmer le mot de passe", "Confirm password")
        )
        user_group.add(self.password_confirm_row)

        self.password_warning = Gtk.Label(
            css_classes=["error", "caption"],
            wrap=True,
            xalign=0,
            visible=False,
        )
        box.append(user_group)
        box.append(self.password_warning)

        # ── Matériel ──
        hw_group = Adw.PreferencesGroup(title=L("Matériel", "Hardware"))
        self.gpu_row = self._combo(
            L("GPU", "GPU"),
            [
                ("amd", "AMD — RDNA / GCN 3+"),
                (
                    "amd-legacy",
                    L("AMD legacy — GCN 1.x/2.x", "AMD legacy — GCN 1.x/2.x"),
                ),
                ("nvidia", "NVIDIA"),
                ("intel", L("Intel intégré", "Intel integrated")),
            ],
            state.gpu,
        )
        hw_group.add(self.gpu_row)

        self.nvidia_laptop_row = Adw.SwitchRow(
            title=L(
                "Laptop Optimus (Intel/AMD + NVIDIA dGPU)",
                "Optimus laptop (Intel/AMD + NVIDIA dGPU)",
            )
        )
        self.nvidia_laptop_row.set_active(state.nvidia_laptop)
        hw_group.add(self.nvidia_laptop_row)

        self.undervolt_row = Adw.SwitchRow(
            title=L(
                "Undervolting GPU AMD (lact, amdgpu.ppfeaturemask)",
                "AMD GPU undervolting (lact, amdgpu.ppfeaturemask)",
            )
        )
        self.undervolt_row.set_active(state.undervolt_enable)
        hw_group.add(self.undervolt_row)

        self.cpu_row = self._combo(
            "CPU", [("amd", "AMD"), ("intel", "Intel")], state.cpu
        )
        hw_group.add(self.cpu_row)

        self.kernel_row = self._combo(L("Kernel", "Kernel"), _kernels(), state.kernel)
        hw_group.add(self.kernel_row)
        box.append(hw_group)
        self._sync_nvidia_row()
        self._sync_undervolt_row()
        self._sync_kernel_row()

        # ── Navigateur ──
        browser_group = Adw.PreferencesGroup(title=L("Navigateur", "Browser"))
        browsers = _browsers()
        self.browser_row = self._combo(
            L("Navigateur", "Browser"),
            browsers,
            state.browser if state.browser in dict(browsers) else "brave",
        )
        browser_group.add(self.browser_row)

        self.brave_variant_row = self._combo(
            L("Variante Brave", "Brave variant"), _brave_variants(), "brave"
        )
        browser_group.add(self.brave_variant_row)

        self.zen_row = Adw.SwitchRow(
            title=L("Installer Zen Browser (en plus)", "Also install Zen Browser")
        )
        self.zen_row.set_active(state.zen_browser)
        browser_group.add(self.zen_row)

        self.zen_mods_row = Adw.EntryRow(
            title=L("Mods Zen (séparés par des virgules)", "Zen mods (comma-separated)")
        )
        self.zen_mods_row.set_text(", ".join(state.zen_mods))
        browser_group.add(self.zen_mods_row)

        self.zen_sine_row = Adw.SwitchRow(
            title=L("Activer Sine (moteur de mods Zen)", "Enable Sine (Zen mod engine)")
        )
        self.zen_sine_row.set_active(state.zen_sine_enable)
        browser_group.add(self.zen_sine_row)

        self.zen_sine_mods_row = Adw.EntryRow(
            title=L("Mods Sine (séparés par des virgules)", "Sine mods (comma-separated)")
        )
        self.zen_sine_mods_row.set_text(", ".join(state.zen_sine_mods))
        browser_group.add(self.zen_sine_mods_row)
        box.append(browser_group)
        self._sync_brave_row()
        self._sync_zen_rows()

        # ── Bureau ──
        desktop_group = Adw.PreferencesGroup(title=L("Bureau", "Desktop"))
        self.desktop_row = self._combo(
            L("Compositeur / bureau", "Compositor / desktop"),
            _desktops(),
            state.desktop,
        )
        desktop_group.add(self.desktop_row)

        self.shell_row = self._combo(
            L("Shell graphique (bar/UI)", "Graphical shell (bar/UI)"),
            _shells(),
            state.desktop_shell,
        )
        desktop_group.add(self.shell_row)

        self.default_shell_row = self._combo(
            L("Shell par défaut", "Default shell"),
            _default_shells(),
            state.default_shell,
        )
        desktop_group.add(self.default_shell_row)

        self.terminal_row = self._combo(
            L("Terminal", "Terminal"), _terminals(), state.terminal
        )
        desktop_group.add(self.terminal_row)
        box.append(desktop_group)
        self._sync_shell_row()

        # ── Système ──
        sys_group = Adw.PreferencesGroup(title=L("Système", "System"))
        self.vm_guest_row = Adw.SwitchRow(
            title=L("Installation dans une VM", "Installing inside a VM")
        )
        self.vm_guest_row.set_active(state.vm_guest)
        sys_group.add(self.vm_guest_row)

        self.gaming_row = Adw.SwitchRow(
            title=L(
                "Paquets gaming (Steam, Wine, Lutris…)",
                "Gaming packages (Steam, Wine, Lutris…)",
            )
        )
        self.gaming_row.set_active(state.gaming)
        sys_group.add(self.gaming_row)

        self.ananicy_row = Adw.SwitchRow(
            title=L(
                "Ananicy (ordonnancement auto pour le gaming)",
                "Ananicy (automatic gaming scheduling)",
            )
        )
        self.ananicy_row.set_active(state.ananicy_enable)
        sys_group.add(self.ananicy_row)

        self.mesa_git_row = Adw.SwitchRow(
            title=L(
                "Mesa git (pilotes graphiques bleeding edge)",
                "Mesa git (bleeding-edge graphics drivers)",
            )
        )
        self.mesa_git_row.set_active(state.mesa_use_git)
        sys_group.add(self.mesa_git_row)

        self.timezone_row = self._combo(
            L("Fuseau horaire", "Timezone"), _timezones(), state.timezone
        )
        sys_group.add(self.timezone_row)

        self.locale_row = self._combo(
            L("Langue système", "System language"), _locales(), state.locale
        )
        sys_group.add(self.locale_row)

        self.keymap_row = self._combo(
            L("Disposition clavier (console)", "Keyboard layout (console)"),
            _keymaps(),
            state.keymap,
        )
        sys_group.add(self.keymap_row)
        box.append(sys_group)
        self._sync_ananicy_row()

        # ── RGB ──
        rgb_group = Adw.PreferencesGroup(title="RGB")
        self.rgb_row = self._combo(
            L("Contrôleur RGB", "RGB controller"), _rgb_options(), state.rgb
        )
        rgb_group.add(self.rgb_row)

        self.memory_rgb_row = Adw.SwitchRow(
            title=L("RGB RAM (Corsair DDR4/DDR5)", "RAM RGB (Corsair DDR4/DDR5)")
        )
        self.memory_rgb_row.set_active(state.memory_rgb_enable)
        rgb_group.add(self.memory_rgb_row)

        self.memory_type_row = self._combo(
            L("Type de RAM", "RAM type"),
            [("ddr5", "DDR5"), ("ddr4", "DDR4")],
            state.memory_type,
        )
        rgb_group.add(self.memory_type_row)

        self.memory_smbus_row = Adw.EntryRow(
            title=L("SMBus (ex: i2c-1)", "SMBus (e.g. i2c-1)")
        )
        self.memory_smbus_row.set_text(state.memory_smbus)
        rgb_group.add(self.memory_smbus_row)

        self.memory_sku_row = Adw.EntryRow(
            title=L("SKU RAM (numéro de pièce)", "RAM SKU (part number)")
        )
        self.memory_sku_row.set_text(state.memory_sku)
        rgb_group.add(self.memory_sku_row)
        box.append(rgb_group)
        self._sync_memory_rows()

        rgb_note = Gtk.Label(
            label=L(
                "SMBus / SKU RAM ne sont pas détectés automatiquement — trouvez-les via "
                "« i2cdetect -l » et « sudo dmidecode -t memory | grep 'Part Number' ».",
                "SMBus / RAM SKU aren't auto-detected — find them via "
                "\"i2cdetect -l\" and \"sudo dmidecode -t memory | grep 'Part Number'\".",
            ),
            css_classes=["dim-label", "caption"],
            wrap=True,
            xalign=0,
        )
        box.append(rgb_note)

        # ── Extras ──
        extra_group = Adw.PreferencesGroup(title=L("Extras", "Extras"))
        self.gta_fix_row = Adw.SwitchRow(
            title=L(
                "Fix GTA Online (bloque l'IP anti-cheat Linux)",
                "GTA Online fix (blocks the Linux anti-cheat IP)",
            )
        )
        self.gta_fix_row.set_active(state.gta_fix)
        extra_group.add(self.gta_fix_row)

        self.flatpak_row = Adw.SwitchRow(title="Flatpak")
        self.flatpak_row.set_active(state.flatpak)
        extra_group.add(self.flatpak_row)

        self.virt_row = Adw.SwitchRow(
            title=L(
                "Virtualisation (libvirt, virt-manager)",
                "Virtualization (libvirt, virt-manager)",
            )
        )
        self.virt_row.set_active(state.virtualization)
        extra_group.add(self.virt_row)

        self.autoupdate_row = Adw.SwitchRow(
            title=L("Mises à jour automatiques", "Automatic updates")
        )
        self.autoupdate_row.set_active(state.autoupdate)
        extra_group.add(self.autoupdate_row)

        self.autoupdate_interval_row = Adw.EntryRow(
            title=L("Intervalle (ex: 1h, 6h, 24h)", "Interval (e.g. 1h, 6h, 24h)")
        )
        self.autoupdate_interval_row.set_text(state.autoupdate_interval)
        extra_group.add(self.autoupdate_interval_row)

        self.bootloader_row = self._combo(
            L("Bootloader", "Bootloader"), _bootloaders(), state.bootloader
        )
        extra_group.add(self.bootloader_row)

        self.matrix_row = self._combo(
            L("Client Matrix", "Matrix client"), _matrix(), state.matrix_client
        )
        extra_group.add(self.matrix_row)

        self.waydroid_row = Adw.SwitchRow(title="Waydroid (Android)")
        self.waydroid_row.set_active(state.waydroid_enable)
        extra_group.add(self.waydroid_row)
        box.append(extra_group)
        self._sync_autoupdate_row()

        # Connected here (not right after each row's creation above) because
        # ComboRow/SwitchRow can fire their notify signal synchronously while
        # still being constructed — connecting early meant these handlers could
        # run before the widgets they toggle existed yet, throwing a silently-
        # swallowed AttributeError instead of actually syncing visibility.
        self.gpu_row.connect("notify::selected", lambda *_: self._sync_nvidia_row())
        self.gpu_row.connect("notify::selected", lambda *_: self._sync_undervolt_row())
        self.gpu_row.connect("notify::selected", lambda *_: self._sync_kernel_row())
        self.browser_row.connect("notify::selected", lambda *_: self._sync_brave_row())
        self.desktop_row.connect("notify::selected", lambda *_: self._sync_shell_row())
        self.rgb_row.connect("notify::selected", lambda *_: self._sync_memory_rows())
        self.memory_rgb_row.connect("notify::active", lambda *_: self._sync_memory_rows())
        self.zen_row.connect("notify::active", lambda *_: self._sync_zen_rows())
        self.zen_sine_row.connect("notify::active", lambda *_: self._sync_zen_rows())
        self.gaming_row.connect("notify::active", lambda *_: self._sync_ananicy_row())
        self.autoupdate_row.connect(
            "notify::active", lambda *_: self._sync_autoupdate_row()
        )

        next_btn = Gtk.Button(
            label=L("Continuer", "Continue"),
            css_classes=["suggested-action", "pill"],
            halign=Gtk.Align.END,
            margin_top=12,
        )
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

    @staticmethod
    def _split_list(text):
        return [part.strip() for part in text.split(",") if part.strip()]

    def _sync_nvidia_row(self):
        self.nvidia_laptop_row.set_visible(
            self._selected_value(self.gpu_row) == "nvidia"
        )

    def _sync_undervolt_row(self):
        self.undervolt_row.set_visible(
            self._selected_value(self.gpu_row) in ("amd", "amd-legacy")
        )

    def _sync_kernel_row(self):
        is_nvidia = self._selected_value(self.gpu_row) == "nvidia"
        pairs = _kernels_chaotic() if is_nvidia else _kernels()
        current = self.state.kernel_chaotic if is_nvidia else self.state.kernel
        values = [v for v, _ in pairs]
        labels = [l for _, l in pairs]
        self.kernel_row.set_title(
            L("Kernel (Chaotic-Nyx)", "Kernel (Chaotic-Nyx)")
            if is_nvidia
            else L("Kernel (xddxdd)", "Kernel (xddxdd)")
        )
        self.kernel_row.set_model(Gtk.StringList.new(labels))
        self.kernel_row.set_selected(values.index(current) if current in values else 0)
        self._rows[id(self.kernel_row)] = values

    def _sync_brave_row(self):
        self.brave_variant_row.set_visible(
            self._selected_value(self.browser_row) == "brave"
        )

    def _sync_shell_row(self):
        desktop = self._selected_value(self.desktop_row)
        self.shell_row.set_visible(desktop in ("niri", "hyprland"))

    def _sync_memory_rows(self):
        is_openlinkhub = self._selected_value(self.rgb_row) == "openlinkhub"
        self.memory_rgb_row.set_visible(is_openlinkhub)
        memory_rgb_active = is_openlinkhub and self.memory_rgb_row.get_active()
        self.memory_type_row.set_visible(memory_rgb_active)
        self.memory_smbus_row.set_visible(memory_rgb_active)
        self.memory_sku_row.set_visible(memory_rgb_active)

    def _sync_zen_rows(self):
        zen_active = self.zen_row.get_active()
        self.zen_mods_row.set_visible(zen_active)
        self.zen_sine_row.set_visible(zen_active)
        self.zen_sine_mods_row.set_visible(zen_active and self.zen_sine_row.get_active())

    def _sync_ananicy_row(self):
        self.ananicy_row.set_visible(self.gaming_row.get_active())

    def _sync_autoupdate_row(self):
        self.autoupdate_interval_row.set_visible(self.autoupdate_row.get_active())

    def _validate(self, _btn):
        password = self.password_row.get_text()
        confirm = self.password_confirm_row.get_text()
        if not password:
            self.password_warning.set_label(
                L("Le mot de passe ne peut pas être vide.", "Password can't be empty.")
            )
            self.password_warning.set_visible(True)
            return
        if password != confirm:
            self.password_warning.set_label(
                L("Les mots de passe ne correspondent pas.", "Passwords don't match.")
            )
            self.password_warning.set_visible(True)
            return
        self.password_warning.set_visible(False)

        s = self.state
        s.username = self.username_row.get_text()
        s.password = password
        s.gpu = self._selected_value(self.gpu_row)
        s.nvidia_laptop = self.nvidia_laptop_row.get_active()
        s.undervolt_enable = self.undervolt_row.get_active()
        s.cpu = self._selected_value(self.cpu_row)
        kernel_value = self._selected_value(self.kernel_row)
        if s.gpu == "nvidia":
            s.kernel_chaotic = kernel_value
        else:
            s.kernel = kernel_value

        browser = self._selected_value(self.browser_row)
        s.browser = (
            self._selected_value(self.brave_variant_row)
            if browser == "brave"
            else browser
        )
        s.zen_browser = self.zen_row.get_active()
        s.zen_sine_enable = self.zen_sine_row.get_active()
        s.zen_mods = self._split_list(self.zen_mods_row.get_text())
        s.zen_sine_mods = self._split_list(self.zen_sine_mods_row.get_text())

        s.desktop = self._selected_value(self.desktop_row)
        s.desktop_shell = self._selected_value(self.shell_row)
        s.default_shell = self._selected_value(self.default_shell_row)
        s.terminal = self._selected_value(self.terminal_row)

        s.vm_guest = self.vm_guest_row.get_active()
        s.gaming = self.gaming_row.get_active()
        s.ananicy_enable = self.ananicy_row.get_active()
        s.mesa_use_git = self.mesa_git_row.get_active()
        s.timezone = self._selected_value(self.timezone_row)
        s.locale = self._selected_value(self.locale_row)
        s.keymap = self._selected_value(self.keymap_row)

        s.rgb = self._selected_value(self.rgb_row)
        s.memory_rgb_enable = self.memory_rgb_row.get_active()
        s.memory_type = self._selected_value(self.memory_type_row)
        s.memory_smbus = self.memory_smbus_row.get_text()
        s.memory_sku = self.memory_sku_row.get_text()

        s.gta_fix = self.gta_fix_row.get_active()
        s.flatpak = self.flatpak_row.get_active()
        s.virtualization = self.virt_row.get_active()
        s.autoupdate = self.autoupdate_row.get_active()
        s.autoupdate_interval = self.autoupdate_interval_row.get_text()
        s.bootloader = self._selected_value(self.bootloader_row)
        s.matrix_client = self._selected_value(self.matrix_row)
        s.waydroid_enable = self.waydroid_row.get_active()

        self.on_next()
