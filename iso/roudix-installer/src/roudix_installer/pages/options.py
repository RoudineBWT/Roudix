from gi.repository import Adw, Gtk

from roudix_installer.hardware_detect import detect_cpu, detect_gpu
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
        ("zen", L("linux-zen (nixpkgs) — hors overlay xddxdd", "linux-zen (nixpkgs) — outside the xddxdd overlay")),
        ("nixpkgs-lts", L("nixpkgs LTS par défaut — hors overlay xddxdd", "nixpkgs default LTS — outside the xddxdd overlay")),
        ("nixpkgs-latest", L("nixpkgs dernier stable mainline — hors overlay xddxdd", "nixpkgs latest mainline — outside the xddxdd overlay")),
        ("nixpkgs-testing", L("nixpkgs testing (RC/mainline) — hors overlay xddxdd", "nixpkgs testing (RC/mainline) — outside the xddxdd overlay")),
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
        ("zen", L("linux-zen (nixpkgs) — module nvidia rebuild local", "linux-zen (nixpkgs) — locally-rebuilt nvidia module")),
        ("nixpkgs-lts", L("nixpkgs LTS par défaut — module nvidia rebuild local", "nixpkgs default LTS — locally-rebuilt nvidia module")),
        ("nixpkgs-latest", L("nixpkgs dernier stable mainline — module nvidia rebuild local", "nixpkgs latest mainline — locally-rebuilt nvidia module")),
        ("nixpkgs-testing", L("nixpkgs testing (RC/mainline) — module nvidia rebuild local", "nixpkgs testing (RC/mainline) — locally-rebuilt nvidia module")),
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
        ("mangowc", "MangoWC"),
    ]


def _mark_detected(pairs, detected_value):
    """Appends '(détecté)' to the label of the auto-detected entry, if any."""
    if not detected_value:
        return pairs
    return [
        (value, f"{label} {L('(détecté)', '(detected)')}" if value == detected_value else label)
        for value, label in pairs
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


def _file_managers():
    return [
        ("nautilus", L("Nautilus — GNOME Files (recommandé)", "Nautilus — GNOME Files (recommended)")),
        ("dolphin", L("Dolphin — KDE", "Dolphin — KDE")),
        ("thunar", L("Thunar — XFCE, léger", "Thunar — XFCE, lightweight")),
        ("nemo", L("Nemo — Cinnamon", "Nemo — Cinnamon")),
    ]


def _editors():
    return [
        ("zed", L("Zed — rapide, moderne (recommandé)", "Zed — fast, modern (recommended)")),
        ("vscode", "Visual Studio Code"),
        ("neovim", "Neovim"),
        (
            "none",
            L(
                "Aucun — je gère mon propre éditeur (AppImage, Flatpak...)",
                "None — I'll manage my own editor (AppImage, Flatpak...)",
            ),
        ),
    ]


def _desktop_integrations():
    return [
        (
            "gnome",
            L(
                "GNOME keyring + xdg-desktop-portal-gtk/-gnome (recommandé)",
                "GNOME keyring + xdg-desktop-portal-gtk/-gnome (recommended)",
            ),
        ),
        (
            "kde",
            L(
                "KWallet + xdg-desktop-portal-kde (utile si vous utilisez surtout des apps Qt/KDE)",
                "KWallet + xdg-desktop-portal-kde (useful if you mainly run Qt/KDE apps)",
            ),
        ),
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


def _discord():
    return [
        ("vencord", L("Vencord (préinstallé)", "Vencord (pre-installed)")),
        ("vanilla", L("Vanilla (sans patch)", "Vanilla (no patch)")),
        ("none", L("Aucun", "None")),
    ]


def _timezones():
    return [
        ("Europe/Brussels", L("Belgique", "Belgium")),
        ("Europe/Paris", "France"),
        ("Europe/London", L("Royaume-Uni", "United Kingdom")),
        ("Europe/Amsterdam", L("Pays-Bas", "Netherlands")),
        ("Europe/Berlin", L("Allemagne", "Germany")),
        ("Europe/Vienna", L("Autriche", "Austria")),
        ("Europe/Zurich", L("Suisse", "Switzerland")),
        ("Europe/Luxembourg", "Luxembourg"),
        ("Europe/Madrid", L("Espagne", "Spain")),
        ("Europe/Lisbon", "Portugal"),
        ("Europe/Rome", L("Italie", "Italy")),
        ("Europe/Warsaw", L("Pologne", "Poland")),
        ("Europe/Prague", L("République Tchèque", "Czech Republic")),
        ("Europe/Bratislava", L("Slovaquie", "Slovakia")),
        ("Europe/Budapest", L("Hongrie", "Hungary")),
        ("Europe/Bucharest", L("Roumanie", "Romania")),
        ("Europe/Sofia", L("Bulgarie", "Bulgaria")),
        ("Europe/Athens", L("Grèce", "Greece")),
        ("Europe/Helsinki", L("Finlande", "Finland")),
        ("Europe/Stockholm", L("Suède", "Sweden")),
        ("Europe/Oslo", L("Norvège", "Norway")),
        ("Europe/Copenhagen", L("Danemark", "Denmark")),
        ("Europe/Tallinn", L("Estonie", "Estonia")),
        ("Europe/Riga", L("Lettonie", "Latvia")),
        ("Europe/Vilnius", L("Lituanie", "Lithuania")),
        ("Europe/Kiev", "Ukraine"),
        ("Europe/Moscow", L("Russie (Moscou)", "Russia (Moscow)")),
        ("Europe/Istanbul", L("Turquie", "Turkey")),
        ("Atlantic/Reykjavik", L("Islande", "Iceland")),
        ("Africa/Casablanca", L("Maroc", "Morocco")),
        ("Africa/Algiers", L("Algérie", "Algeria")),
        ("Africa/Tunis", L("Tunisie", "Tunisia")),
        ("Africa/Cairo", L("Égypte", "Egypt")),
        ("Africa/Johannesburg", L("Afrique du Sud", "South Africa")),
        ("Africa/Lagos", L("Nigéria", "Nigeria")),
        ("Africa/Nairobi", "Kenya"),
        ("America/New_York", L("États-Unis (Est)", "United States (East)")),
        ("America/Chicago", L("États-Unis (Centre)", "United States (Central)")),
        ("America/Denver", L("États-Unis (Montagne)", "United States (Mountain)")),
        ("America/Los_Angeles", L("États-Unis (Ouest)", "United States (West)")),
        ("America/Anchorage", L("États-Unis (Alaska)", "United States (Alaska)")),
        ("Pacific/Honolulu", L("États-Unis (Hawaï)", "United States (Hawaii)")),
        ("America/Toronto", L("Canada (Est)", "Canada (East)")),
        ("America/Vancouver", L("Canada (Ouest)", "Canada (West)")),
        ("America/Mexico_City", L("Mexique", "Mexico")),
        ("America/Bogota", L("Colombie", "Colombia")),
        ("America/Lima", L("Pérou", "Peru")),
        ("America/Santiago", L("Chili", "Chile")),
        ("America/Buenos_Aires", L("Argentine", "Argentina")),
        ("America/Sao_Paulo", L("Brésil (São Paulo)", "Brazil (São Paulo)")),
        ("America/Caracas", "Venezuela"),
        ("Asia/Dubai", L("Émirats Arabes Unis", "United Arab Emirates")),
        ("Asia/Riyadh", L("Arabie Saoudite", "Saudi Arabia")),
        ("Asia/Jerusalem", L("Israël", "Israel")),
        ("Asia/Beirut", L("Liban", "Lebanon")),
        ("Asia/Baghdad", L("Irak", "Iraq")),
        ("Asia/Tehran", "Iran"),
        ("Asia/Karachi", "Pakistan"),
        ("Asia/Kolkata", L("Inde", "India")),
        ("Asia/Dhaka", "Bangladesh"),
        ("Asia/Colombo", "Sri Lanka"),
        ("Asia/Kathmandu", L("Népal", "Nepal")),
        ("Asia/Almaty", "Kazakhstan"),
        ("Asia/Tashkent", L("Ouzbékistan", "Uzbekistan")),
        ("Asia/Bangkok", L("Thaïlande", "Thailand")),
        ("Asia/Ho_Chi_Minh", "Vietnam"),
        ("Asia/Jakarta", L("Indonésie (Ouest)", "Indonesia (West)")),
        ("Asia/Singapore", L("Singapour", "Singapore")),
        ("Asia/Kuala_Lumpur", L("Malaisie", "Malaysia")),
        ("Asia/Manila", "Philippines"),
        ("Asia/Shanghai", L("Chine", "China")),
        ("Asia/Hong_Kong", "Hong Kong"),
        ("Asia/Taipei", L("Taïwan", "Taiwan")),
        ("Asia/Seoul", L("Corée du Sud", "South Korea")),
        ("Asia/Tokyo", L("Japon", "Japan")),
        ("Australia/Perth", L("Australie (Ouest)", "Australia (West)")),
        ("Australia/Adelaide", L("Australie (Centre)", "Australia (Central)")),
        ("Australia/Sydney", L("Australie (Est)", "Australia (East)")),
        ("Pacific/Auckland", L("Nouvelle-Zélande", "New Zealand")),
        ("Pacific/Fiji", L("Fidji", "Fiji")),
        ("UTC", "UTC"),
    ]


def _locales():
    return [
        ("en_US.UTF-8", "English (US)"),
        ("en_GB.UTF-8", "English (UK)"),
        ("fr_BE.UTF-8", "Français (Belgique)"),
        ("fr_FR.UTF-8", "Français (France)"),
        ("fr_CH.UTF-8", "Français (Suisse)"),
        ("de_DE.UTF-8", "Deutsch (Deutschland)"),
        ("de_AT.UTF-8", "Deutsch (Österreich)"),
        ("de_CH.UTF-8", "Deutsch (Schweiz)"),
        ("nl_BE.UTF-8", "Nederlands (België)"),
        ("nl_NL.UTF-8", "Nederlands (Nederland)"),
        ("es_ES.UTF-8", "Español (España)"),
        ("es_MX.UTF-8", "Español (México)"),
        ("pt_PT.UTF-8", "Português (Portugal)"),
        ("pt_BR.UTF-8", "Português (Brasil)"),
        ("it_IT.UTF-8", "Italiano (Italia)"),
        ("pl_PL.UTF-8", "Polski (Polska)"),
        ("ru_RU.UTF-8", "Русский (Россия)"),
        ("uk_UA.UTF-8", "Українська (Україна)"),
        ("cs_CZ.UTF-8", "Čeština (Česká republika)"),
        ("sk_SK.UTF-8", "Slovenčina (Slovensko)"),
        ("hu_HU.UTF-8", "Magyar (Magyarország)"),
        ("ro_RO.UTF-8", "Română (România)"),
        ("tr_TR.UTF-8", "Türkçe (Türkiye)"),
        ("ja_JP.UTF-8", "日本語 (日本)"),
        ("zh_CN.UTF-8", "中文 (中国大陆)"),
        ("zh_TW.UTF-8", "中文 (台灣)"),
        ("ko_KR.UTF-8", "한국어 (대한민국)"),
        ("ar_SA.UTF-8", "العربية (المملكة العربية السعودية)"),
        ("he_IL.UTF-8", "עברית (ישראל)"),
        ("hi_IN.UTF-8", "हिन्दी (भारत)"),
        ("sv_SE.UTF-8", "Svenska (Sverige)"),
        ("nb_NO.UTF-8", "Norsk bokmål (Norge)"),
        ("da_DK.UTF-8", "Dansk (Danmark)"),
        ("fi_FI.UTF-8", "Suomi (Suomi)"),
        ("el_GR.UTF-8", "Ελληνικά (Ελλάδα)"),
        ("C.UTF-8", L("C (POSIX minimal)", "C (minimal POSIX)")),
    ]


def _keymaps():
    return [
        ("us", "English (US) QWERTY"),
        ("us-acentos", L("English (US) International (touches mortes)", "English (US) International (dead keys)")),
        ("uk", "English (UK) QWERTY"),
        ("be-latin1", L("Belge AZERTY", "Belgian AZERTY")),
        ("fr", L("Français AZERTY", "French AZERTY")),
        ("fr-latin9", L("Français AZERTY (latin9)", "French AZERTY (latin9)")),
        ("fr_CH", L("Français Suisse QWERTZ", "Swiss French QWERTZ")),
        ("de", L("Allemand QWERTZ", "German QWERTZ")),
        ("de-latin1", L("Allemand QWERTZ (latin1)", "German QWERTZ (latin1)")),
        ("at", L("Autrichien QWERTZ", "Austrian QWERTZ")),
        ("ch", L("Suisse QWERTZ", "Swiss QWERTZ")),
        ("nl", L("Néerlandais QWERTY", "Dutch QWERTY")),
        ("es", L("Espagnol QWERTY", "Spanish QWERTY")),
        ("es-cp850", L("Espagnol QWERTY (cp850)", "Spanish QWERTY (cp850)")),
        ("pt-latin1", L("Portugais QWERTY (latin1)", "Portuguese QWERTY (latin1)")),
        ("br-abnt2", L("Portugais Brésilien ABNT2", "Brazilian Portuguese ABNT2")),
        ("it", L("Italien QWERTY", "Italian QWERTY")),
        ("it-latin1", L("Italien QWERTY (latin1)", "Italian QWERTY (latin1)")),
        ("pl2", L("Polonais QWERTY", "Polish QWERTY")),
        ("ru", L("Russe", "Russian")),
        ("ua", L("Ukrainien", "Ukrainian")),
        ("cz-lat2", L("Tchèque QWERTY (latin2)", "Czech QWERTY (latin2)")),
        ("sk-qwerty", L("Slovaque QWERTY", "Slovak QWERTY")),
        ("hu", L("Hongrois QWERTY", "Hungarian QWERTY")),
        ("ro", L("Roumain QWERTY", "Romanian QWERTY")),
        ("trq", L("Turc Q", "Turkish Q")),
        ("trf", L("Turc F", "Turkish F")),
        ("jp106", L("Japonais 106 touches", "Japanese 106-key")),
        ("sv-latin1", L("Suédois QWERTY (latin1)", "Swedish QWERTY (latin1)")),
        ("no-latin1", L("Norvégien QWERTY (latin1)", "Norwegian QWERTY (latin1)")),
        ("dk-latin1", L("Danois QWERTY (latin1)", "Danish QWERTY (latin1)")),
        ("fi-latin1", L("Finnois QWERTY (latin1)", "Finnish QWERTY (latin1)")),
        ("gr", L("Grec", "Greek")),
        ("il", L("Hébreu", "Hebrew")),
        ("arabic", L("Arabe", "Arabic")),
        ("dvorak", "Dvorak (US)"),
        ("dvorak-l", L("Dvorak gauche", "Dvorak left")),
        ("dvorak-r", L("Dvorak droite", "Dvorak right")),
        ("colemak", "Colemak"),
    ]


def _gfx_keyboard_layouts():
    """XKB layout:variant pairs for the graphical (Wayland) session —
    niri/hyprland/mangowc/umbriel. Distinct from _keymaps() above, which
    is the console/TTY-only keymap (different naming scheme entirely).
    Value is "layout:variant" (variant may be empty), split back apart
    in _validate() before writing roudix.keyboardLayout/Variant.
    """
    return [
        ("us:intl", L("US International (touches mortes, recommandé)", "US International (dead keys, recommended)")),
        ("us:", L("US Basique QWERTY (sans variante)", "US Basic QWERTY (no variant)")),
        ("gb:", L("Britannique QWERTY", "British QWERTY")),
        ("be:", L("Belge AZERTY", "Belgian AZERTY")),
        ("fr:", L("Français AZERTY", "French AZERTY")),
        ("fr:bepo", L("Français BÉPO", "French BÉPO")),
        ("de:", L("Allemand QWERTZ", "German QWERTZ")),
        ("ch:fr", L("Suisse (romand) QWERTZ", "Swiss French QWERTZ")),
        ("ch:de", L("Suisse (allemand) QWERTZ", "Swiss German QWERTZ")),
        ("nl:", L("Néerlandais QWERTY", "Dutch QWERTY")),
        ("es:", L("Espagnol QWERTY", "Spanish QWERTY")),
        ("it:", L("Italien QWERTY", "Italian QWERTY")),
        ("pt:", L("Portugais QWERTY", "Portuguese QWERTY")),
        ("pl:", L("Polonais QWERTY", "Polish QWERTY")),
        ("ru:", L("Russe", "Russian")),
        ("ua:", L("Ukrainien", "Ukrainian")),
        ("jp:", L("Japonais", "Japanese")),
        ("us:dvorak", L("Dvorak (US)", "Dvorak (US)")),
        ("us:colemak", L("Colemak (US)", "Colemak (US)")),
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
        gpu_detected, nvidia_laptop_detected = detect_gpu()
        cpu_detected = detect_cpu()
        # Detection only picks a sensible default — never overrides a
        # value the user already set on a prior visit to this page (this
        # page is only ever built once per session, so at this point
        # `state` still holds nothing but its dataclass defaults).
        if gpu_detected:
            state.gpu = gpu_detected
            state.nvidia_laptop = nvidia_laptop_detected
        if cpu_detected:
            state.cpu = cpu_detected

        hw_group = Adw.PreferencesGroup(title=L("Matériel", "Hardware"))
        self.gpu_row = self._combo(
            L("GPU", "GPU"),
            _mark_detected(
                [
                    ("amd", "AMD — RDNA / GCN 3+"),
                    (
                        "amd-legacy",
                        L("AMD legacy — GCN 1.x/2.x", "AMD legacy — GCN 1.x/2.x"),
                    ),
                    ("nvidia", "NVIDIA"),
                    ("intel", L("Intel intégré", "Intel integrated")),
                ],
                gpu_detected,
            ),
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
            "CPU",
            _mark_detected([("amd", "AMD"), ("intel", "Intel")], cpu_detected),
            state.cpu,
        )
        hw_group.add(self.cpu_row)

        self.kernel_row = self._combo(L("Kernel", "Kernel"), _kernels(), state.kernel)
        hw_group.add(self.kernel_row)
        box.append(hw_group)

        if gpu_detected or cpu_detected:
            hw_note = Gtk.Label(
                label=L(
                    "GPU / CPU détectés automatiquement — modifiable ci-dessus si besoin.",
                    "GPU / CPU auto-detected — change them above if needed.",
                ),
                css_classes=["dim-label", "caption"],
                wrap=True,
                xalign=0,
            )
            box.append(hw_note)

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

        self.zen_variant_row = self._combo(
            L("Canal Zen", "Zen channel"),
            [
                ("twilight", L("Twilight (défaut)", "Twilight (default)")),
                ("beta", "Beta"),
                ("twilight-official", L("Twilight (officiel)", "Twilight (official)")),
            ],
            state.zen_variant,
        )
        browser_group.add(self.zen_variant_row)

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

        self.file_manager_row = self._combo(
            L("Gestionnaire de fichiers", "File manager"),
            _file_managers(),
            state.file_manager,
        )
        desktop_group.add(self.file_manager_row)

        self.editor_row = self._combo(
            L("Éditeur de code", "Code editor"),
            _editors(),
            state.editor,
        )
        desktop_group.add(self.editor_row)

        self.desktop_integration_row = self._combo(
            L(
                "Trousseau / xdg-desktop-portal",
                "Keyring / xdg-desktop-portal",
            ),
            _desktop_integrations(),
            state.desktop_integration,
        )
        desktop_group.add(self.desktop_integration_row)
        box.append(desktop_group)
        self._sync_shell_row()
        self._sync_file_manager_row()
        self._sync_desktop_integration_row()
        self.desktop_row.connect(
            "notify::selected", lambda *_: self._sync_file_manager_row()
        )
        self.desktop_row.connect(
            "notify::selected", lambda *_: self._sync_desktop_integration_row()
        )

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

        self.gaming_apps_rows = {}
        for attr, title_fr, title_en, default in (
            ("lutris", "Lutris", "Lutris", state.gaming_apps_lutris),
            ("heroic", "Heroic Games Launcher (Epic/GOG/Amazon)", "Heroic Games Launcher (Epic/GOG/Amazon)", state.gaming_apps_heroic),
            ("faugus", "Faugus Launcher", "Faugus Launcher", state.gaming_apps_faugus),
            ("prismlauncher", "Prism Launcher (Minecraft)", "Prism Launcher (Minecraft)", state.gaming_apps_prismlauncher),
            ("vintagestory", "Vintage Story", "Vintage Story", state.gaming_apps_vintagestory),
            ("mangohud", "MangoHud (overlay de perfs en jeu)", "MangoHud (in-game perf overlay)", state.gaming_apps_mangohud),
        ):
            row = Adw.SwitchRow(title=L(title_fr, title_en))
            row.set_active(default)
            sys_group.add(row)
            self.gaming_apps_rows[attr] = row

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

        _initial_gfx_value = (
            f"{state.keyboard_layout}:{state.keyboard_variant}"
            if state.keyboard_variant
            else f"{state.keyboard_layout}:"
        )
        self.gfx_keyboard_row = self._combo(
            L(
                "Disposition clavier graphique (Wayland)",
                "Graphical keyboard layout (Wayland)",
            ),
            _gfx_keyboard_layouts(),
            _initial_gfx_value,
        )
        sys_group.add(self.gfx_keyboard_row)
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

        self.discord_row = self._combo(
            L("Discord", "Discord"), _discord(), state.discord
        )
        extra_group.add(self.discord_row)

        self.waydroid_row = Adw.SwitchRow(title="Waydroid (Android)")
        self.waydroid_row.set_active(state.waydroid_enable)
        extra_group.add(self.waydroid_row)
        box.append(extra_group)
        self._sync_autoupdate_row()

        # ── Création de contenu ──
        cc_group = Adw.PreferencesGroup(title=L("Création de contenu", "Content Creation"))
        self.content_creation_row = Adw.SwitchRow(
            title=L(
                "Activer les outils de création de contenu",
                "Enable content-creation tooling",
            )
        )
        self.content_creation_row.set_active(state.content_creation_enable)
        cc_group.add(self.content_creation_row)

        self.obs_row = Adw.SwitchRow(title="OBS Studio")
        self.obs_row.set_active(state.obs_enable)
        cc_group.add(self.obs_row)

        self.obs_plugins_row = Adw.EntryRow(
            title=L("Plugins OBS (séparés par des virgules)", "OBS plugins (comma-separated)")
        )
        self.obs_plugins_row.set_text(", ".join(state.obs_plugins))
        cc_group.add(self.obs_plugins_row)

        self.video_editor_row = self._combo(
            L("Éditeur vidéo", "Video editor"),
            [
                ("kdenlive", "Kdenlive"),
                ("davinci-resolve", L("DaVinci Resolve (gratuit)", "DaVinci Resolve (free)")),
                (
                    "davinci-resolve-studio",
                    L("DaVinci Resolve Studio (payant)", "DaVinci Resolve Studio (paid)"),
                ),
                ("shotcut", "Shotcut"),
                ("none", L("Aucun", "None")),
            ],
            state.video_editor,
        )
        cc_group.add(self.video_editor_row)

        self.virtual_camera_row = Adw.SwitchRow(
            title=L("Webcam virtuelle (v4l2loopback)", "Virtual camera (v4l2loopback)")
        )
        self.virtual_camera_row.set_active(state.virtual_camera_enable)
        cc_group.add(self.virtual_camera_row)

        self.chatterino_row = Adw.SwitchRow(
            title=L(
                "Chatterino2 (chat Twitch tiers)",
                "Chatterino2 (third-party Twitch chat)",
            )
        )
        self.chatterino_row.set_active(state.chatterino_enable)
        cc_group.add(self.chatterino_row)
        box.append(cc_group)
        self._sync_content_creation_rows()

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
        self.content_creation_row.connect(
            "notify::active", lambda *_: self._sync_content_creation_rows()
        )
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

    def _set_combo_value(self, row, value):
        values = self._rows[id(row)]
        if value in values:
            row.set_selected(values.index(value))

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
        self.shell_row.set_visible(desktop in ("niri", "hyprland", "mangowc"))

    def _sync_desktop_integration_row(self):
        # GNOME/KDE manage their own keyring/portal stack — this option
        # only matters for the "bare" compositors.
        desktop = self._selected_value(self.desktop_row)
        self.desktop_integration_row.set_visible(
            desktop in ("niri", "hyprland", "mangowc")
        )

    def _sync_file_manager_row(self):
        # GNOME/KDE have one obvious native file manager, so hide the
        # question entirely and lock the value to it — matches
        # roudix-installer.sh, which doesn't even ask on those desktops.
        # niri/hyprland/mangowc don't ship an opinionated file manager, so
        # show the row and leave whatever the user already picked
        # untouched when landing on one of those.
        desktop = self._selected_value(self.desktop_row)
        if desktop == "gnome":
            self._set_combo_value(self.file_manager_row, "nautilus")
            self.file_manager_row.set_visible(False)
        elif desktop == "kde":
            self._set_combo_value(self.file_manager_row, "dolphin")
            self.file_manager_row.set_visible(False)
        else:
            self.file_manager_row.set_visible(True)

    def _sync_memory_rows(self):
        is_openlinkhub = self._selected_value(self.rgb_row) == "openlinkhub"
        self.memory_rgb_row.set_visible(is_openlinkhub)
        memory_rgb_active = is_openlinkhub and self.memory_rgb_row.get_active()
        self.memory_type_row.set_visible(memory_rgb_active)
        self.memory_smbus_row.set_visible(memory_rgb_active)
        self.memory_sku_row.set_visible(memory_rgb_active)

    def _sync_zen_rows(self):
        zen_active = self.zen_row.get_active()
        self.zen_variant_row.set_visible(zen_active)
        self.zen_mods_row.set_visible(zen_active)
        self.zen_sine_row.set_visible(zen_active)
        self.zen_sine_mods_row.set_visible(zen_active and self.zen_sine_row.get_active())

    def _sync_ananicy_row(self):
        self.ananicy_row.set_visible(self.gaming_row.get_active())
        for row in self.gaming_apps_rows.values():
            row.set_visible(self.gaming_row.get_active())

    def _sync_content_creation_rows(self):
        active = self.content_creation_row.get_active()
        for row in (
            self.obs_row,
            self.obs_plugins_row,
            self.video_editor_row,
            self.virtual_camera_row,
            self.chatterino_row,
        ):
            row.set_visible(active)

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
        s.zen_variant = self._selected_value(self.zen_variant_row)
        s.zen_sine_enable = self.zen_sine_row.get_active()
        s.zen_mods = self._split_list(self.zen_mods_row.get_text())
        s.zen_sine_mods = self._split_list(self.zen_sine_mods_row.get_text())

        s.desktop = self._selected_value(self.desktop_row)
        s.desktop_shell = self._selected_value(self.shell_row)
        s.default_shell = self._selected_value(self.default_shell_row)
        s.terminal = self._selected_value(self.terminal_row)
        s.file_manager = self._selected_value(self.file_manager_row)
        s.editor = self._selected_value(self.editor_row)
        s.desktop_integration = self._selected_value(self.desktop_integration_row)

        s.vm_guest = self.vm_guest_row.get_active()
        s.gaming = self.gaming_row.get_active()
        s.ananicy_enable = self.ananicy_row.get_active()
        s.gaming_apps_lutris = self.gaming_apps_rows["lutris"].get_active()
        s.gaming_apps_heroic = self.gaming_apps_rows["heroic"].get_active()
        s.gaming_apps_faugus = self.gaming_apps_rows["faugus"].get_active()
        s.gaming_apps_prismlauncher = self.gaming_apps_rows["prismlauncher"].get_active()
        s.gaming_apps_vintagestory = self.gaming_apps_rows["vintagestory"].get_active()
        s.gaming_apps_mangohud = self.gaming_apps_rows["mangohud"].get_active()
        s.mesa_use_git = self.mesa_git_row.get_active()
        s.timezone = self._selected_value(self.timezone_row)
        s.locale = self._selected_value(self.locale_row)
        s.keymap = self._selected_value(self.keymap_row)
        gfx_value = self._selected_value(self.gfx_keyboard_row)
        s.keyboard_layout, s.keyboard_variant = gfx_value.split(":", 1)

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
        s.discord = self._selected_value(self.discord_row)
        s.waydroid_enable = self.waydroid_row.get_active()

        s.content_creation_enable = self.content_creation_row.get_active()
        s.obs_enable = self.obs_row.get_active()
        s.obs_plugins = self._split_list(self.obs_plugins_row.get_text())
        s.video_editor = self._selected_value(self.video_editor_row)
        s.virtual_camera_enable = self.virtual_camera_row.get_active()
        s.chatterino_enable = self.chatterino_row.get_active()

        self.on_next()
