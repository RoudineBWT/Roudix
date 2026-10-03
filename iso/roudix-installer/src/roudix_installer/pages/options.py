from gi.repository import Adw, Gtk

from roudix_installer import host_defaults, host_profile
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
    # Chaotic-Nyx — deliberately smaller set than xddxdd (no LTO here:
    # out-of-tree modules like nvidia are more fragile with it). Required
    # for nvidia_cachyos, the precompiled Nvidia driver matched to this kernel.
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
        ("umbriel", "Umbriel"),
    ]


def _mark_detected(pairs, detected_value):
    """Appends '(détecté)' to the label of the auto-detected entry, if any."""
    if not detected_value:
        return pairs
    return [
        (value, f"{label} {L('(détecté)', '(detected)')}" if value == detected_value else label)
        for value, label in pairs
    ]


def _shells(desktop=None):
    # Umbriel only has Noctalia support so far; Caelestia's setup is
    # Hyprland-specific (its Quickshell config assumes Hyprland's IPC), so it
    # only makes sense to offer it there. Niri/MangoWC get Noctalia + DMS.
    if desktop == "umbriel":
        return [("noctalia", L("Noctalia — shell par défaut", "Noctalia — default shell"))]

    base = [
        ("noctalia", L("Noctalia — shell par défaut", "Noctalia — default shell")),
        ("dms", "DankMaterialShell — Material 3"),
    ]
    if desktop == "hyprland":
        base = base + [
            (
                "caelestia",
                L("Caelestia — setup Quickshell", "Caelestia — Quickshell setup"),
            )
        ]
    return base


# Compositors / shells that have a flake ("latest") version next to the
# nixpkgs one. Hyprland has no flake version in Roudix: no switch for it.
LATEST_DESKTOPS = {"niri": "Niri", "mangowc": "MangoWC", "umbriel": "Umbriel"}
LATEST_SHELLS = {"noctalia": "Noctalia", "dms": "DMS", "caelestia": "Caelestia"}


def _latest_title(name):
    return L(f"{name} — dernière version (flake)", f"{name} — latest version (flake)")


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


def _branches():
    return [
        ("main", L("main — stable, ~toutes les 2 semaines (recommandé)", "main — stable, ~every 2 weeks (recommended)")),
        ("testing", L("testing — ~tous les 2 jours, peut parfois casser", "testing — ~every 2 days, may occasionally break")),
        ("dev", L("dev — derniers changements, le moins stable", "dev — latest changes, least stable")),
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


def _telegram():
    return [
        ("none", L("Aucun", "None")),
        ("telegram", L("Telegram (client officiel)", "Telegram (official client)")),
        ("ayugram", L("AyuGram (fork : mode fantôme, anti-suppression...)", "AyuGram (fork: ghost mode, anti-recall...)")),
    ]


def _video_player():
    return [
        ("vlc", L("VLC (défaut, plus large support de formats)", "VLC (default, widest format support)")),
        ("clapper", L("Clapper (GTK4 moderne)", "Clapper (modern GTK4)")),
        ("mpv", L("mpv (+ yt-dlp)", "mpv (+ yt-dlp)")),
        ("celluloid", L("Celluloid (interface GTK pour mpv)", "Celluloid (GTK front-end for mpv)")),
        ("none", L("Aucun", "None")),
    ]


def _torrent_client():
    return [
        ("none", L("Aucun", "None")),
        ("qbittorrent", "qBittorrent"),
        ("fragments", L("Fragments (client GNOME minimaliste)", "Fragments (minimal GNOME client)")),
        ("deluge", "Deluge"),
    ]


def _music_player():
    return [
        ("spotify", L("Spotify + Spicetify (défaut)", "Spotify + Spicetify (default)")),
        ("ytmdesktop", "YouTube Music Desktop"),
        ("sonora", "Sonora (Spotify / YouTube Music)"),
        ("none", L("Aucun", "None")),
    ]


def _mail_client():
    return [
        ("none", L("Aucun", "None")),
        ("thunderbird", L("Thunderbird (complet)", "Thunderbird (full-featured)")),
        (
            "betterbird",
            L("Betterbird (fork de Thunderbird)", "Betterbird (Thunderbird fork)"),
        ),
        ("geary", L("Geary (léger, GNOME)", "Geary (lightweight, GNOME)")),
    ]


def _password_manager():
    return [
        ("none", L("Aucun", "None")),
        ("bitwarden", L("Bitwarden (coffre synchronisé)", "Bitwarden (cloud-synced vault)")),
        ("keepassxc", L("KeePassXC (coffre local, hors-ligne)", "KeePassXC (local, offline vault)")),
        ("protonpass", L("Proton Pass (coffre synchronisé)", "Proton Pass (cloud-synced vault)")),
    ]


def _spicetify_themes():
    return [
        ("colorful", L("Colorful (défaut)", "Colorful (default)")),
        ("comfy", "Comfy"),
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

        # ── Answers pre-filled from the chosen profile ──
        # For a profile that lists its options (nixie), start from the values
        # of its local.nix.example instead of the wizard's generic defaults.
        # Done before hardware detection below, so a detected GPU/CPU still
        # wins over the example's (which describes one specific machine).
        seeded = host_defaults.seed_state(state, state.hostname, allowed=self._seed_allowed())
        if seeded:
            box.append(Gtk.Label(
                label=L(
                    f"Réponses préremplies avec les valeurs du profil « {state.hostname} ».",
                    f"Answers pre-filled with the \u201c{state.hostname}\u201d profile's values.",
                ),
                css_classes=["dim-label", "caption"], wrap=True, xalign=0,
            ))

        # ── Hardware ──
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

        self.laptop_row = Adw.SwitchRow(
            title=L(
                "Ordinateur portable (TLP)",
                "Laptop (TLP)",
            )
        )
        self.laptop_row.set_active(state.laptop)
        hw_group.add(self.laptop_row)

        # roudix.laptop.enable force-disables tuned (see
        # modules/system/power/laptop.nix) — surface the same trade-off
        # here that the gaming module warns about at eval time.
        self.laptop_gaming_note = Gtk.Label(
            label=L(
                "Désactive tuned au profit de TLP : si le jeu est aussi activé, "
                "game-performance lancera les jeux normalement mais sans le "
                "profil CPU roudix-gaming.",
                "Disables tuned in favor of TLP: if gaming is also enabled, "
                "game-performance will still launch games normally but "
                "without the roudix-gaming CPU profile.",
            ),
            css_classes=["dim-label", "caption"],
            wrap=True,
            xalign=0,
            visible=False,
        )

        self.thinkpad_row = Adw.SwitchRow(
            title=L(
                "ThinkPad (seuils de charge batterie 40/80%)",
                "ThinkPad (40/80% battery charge thresholds)",
            )
        )
        self.thinkpad_row.set_active(state.laptop_thinkpad)
        hw_group.add(self.thinkpad_row)

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
        box.append(self.laptop_gaming_note)

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
            _shells(state.desktop),
            state.desktop_shell,
        )
        desktop_group.add(self.shell_row)

        # roudix.desktop.latest.<id>: off (default) = nixpkgs version, on =
        # latest version from the project's flake. One row for the chosen
        # compositor, one for the chosen shell; each is only shown while that
        # compositor / shell is selected (see _sync_latest_rows).
        self.latest_de_row = Adw.SwitchRow(
            title=_latest_title("Niri"),
            subtitle=L(
                "Désactivé : version de nixpkgs",
                "Off: nixpkgs version",
            ),
        )
        self.latest_de_row.set_active(False)
        desktop_group.add(self.latest_de_row)

        self.latest_shell_row = Adw.SwitchRow(
            title=_latest_title("Noctalia"),
            subtitle=L(
                "Désactivé : version de nixpkgs",
                "Off: nixpkgs version",
            ),
        )
        self.latest_shell_row.set_active(False)
        desktop_group.add(self.latest_shell_row)

        self.latest_note = Gtk.Label(
            label=L(
                "⚠ Les configurations Roudix sont écrites en priorité pour les "
                "versions flake (les plus récentes). Sur la version nixpkgs, une "
                "erreur de configuration disant qu'une option, un réglage ou une "
                "clé « n'existe pas » est normale : elle a été ajoutée après la "
                "version de nixpkgs. Patiente que nixpkgs la rattrape, ou active "
                "la dernière version.",
                "⚠ Roudix configurations are written for the flake (latest) "
                "versions first. On the nixpkgs version, a configuration error "
                "saying that an option, a setting or a key \"does not exist\" is "
                "normal: it was added after the nixpkgs version. Wait for nixpkgs "
                "to catch up, or turn the latest version on.",
            ),
            css_classes=["dim-label", "caption"],
            wrap=True,
            xalign=0,
            visible=False,
        )
        self.latest_note.set_margin_start(12)
        self.latest_note.set_margin_end(12)
        self.latest_note.set_margin_top(6)
        self.latest_note.set_margin_bottom(6)
        desktop_group.add(self.latest_note)

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
        self._sync_latest_rows()
        self._sync_file_manager_row()
        self._sync_desktop_integration_row()
        self.desktop_row.connect(
            "notify::selected", lambda *_: self._sync_file_manager_row()
        )
        self.desktop_row.connect(
            "notify::selected", lambda *_: self._sync_desktop_integration_row()
        )

        # ── System ──
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

        self.millennium_row = Adw.SwitchRow(
            title=L(
                "Millennium (client Steam modifié : thèmes et plugins)",
                "Millennium (modded Steam client: themes and plugins)",
            ),
            subtitle=L(
                "Mod non officiel — désactivé = Steam standard",
                "Unofficial mod — off = stock Steam",
            ),
        )
        self.millennium_row.set_active(state.gaming_steam_millennium)
        sys_group.add(self.millennium_row)

        self.gaming_apps_rows = {}
        for attr, title_fr, title_en, default in (
            ("lutris", "Lutris", "Lutris", state.gaming_apps_lutris),
            ("heroic", "Heroic Games Launcher (Epic/GOG/Amazon)", "Heroic Games Launcher (Epic/GOG/Amazon)", state.gaming_apps_heroic),
            ("faugus", "Faugus Launcher", "Faugus Launcher", state.gaming_apps_faugus),
            ("prismlauncher", "Prism Launcher (Minecraft)", "Prism Launcher (Minecraft)", state.gaming_apps_prismlauncher),
            ("modrinth", "Modrinth App (alternative à Prism)", "Modrinth App (alternative to Prism)", state.gaming_apps_modrinth),
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

        self.rgb_note = rgb_note = Gtk.Label(
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

        self.branch_row = self._combo(
            L("Branche (installation + mises à jour)", "Branch (install + updates)"),
            _branches(), state.branch,
        )
        extra_group.add(self.branch_row)

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

        self.telegram_row = self._combo(
            "Telegram", _telegram(), state.telegram
        )
        extra_group.add(self.telegram_row)

        self.video_player_row = self._combo(
            L("Lecteur vidéo", "Video player"), _video_player(), state.video_player
        )
        extra_group.add(self.video_player_row)

        self.torrent_client_row = self._combo(
            L("Client torrent", "Torrent client"), _torrent_client(), state.torrent_client
        )
        extra_group.add(self.torrent_client_row)

        self.music_player_row = self._combo(
            L("Lecteur de musique", "Music player"), _music_player(), state.music_player
        )
        extra_group.add(self.music_player_row)

        self.mail_client_row = self._combo(
            L("Client mail", "Mail client"), _mail_client(), state.mail_client
        )
        extra_group.add(self.mail_client_row)

        self.password_manager_row = self._combo(
            L("Gestionnaire de mots de passe", "Password manager"), _password_manager(), state.password_manager
        )
        extra_group.add(self.password_manager_row)

        self.waydroid_row = Adw.SwitchRow(title="Waydroid (Android)")
        self.waydroid_row.set_active(state.waydroid_enable)
        extra_group.add(self.waydroid_row)
        box.append(extra_group)
        self._sync_autoupdate_row()
        self._sync_laptop_row()

        # ── Apps ──
        apps_group = Adw.PreferencesGroup(
            title="Apps",
            description=L(
                "Désactive celles que tu ne veux pas préinstallées.",
                "Turn off any you don't want preinstalled.",
            ),
        )
        self.app_gimp_row = Adw.SwitchRow(title="GIMP")
        self.app_gimp_row.set_active(state.app_gimp)
        apps_group.add(self.app_gimp_row)

        self.app_inkscape_row = Adw.SwitchRow(title="Inkscape")
        self.app_inkscape_row.set_active(state.app_inkscape)
        apps_group.add(self.app_inkscape_row)

        self.spicetify_theme_row = self._combo(
            L("Thème Spicetify", "Spicetify theme"), _spicetify_themes(), state.spicetify_theme
        )
        apps_group.add(self.spicetify_theme_row)

        self.spicetify_color_scheme_row = Adw.EntryRow(
            title=L(
                "Color scheme Spicetify (vide = défaut du thème)",
                "Spicetify color scheme (empty = theme default)",
            )
        )
        self.spicetify_color_scheme_row.set_text(state.spicetify_color_scheme)
        apps_group.add(self.spicetify_color_scheme_row)

        self.spicetify_adblock_row = Adw.SwitchRow(
            title=L("Extension Adblock (Spicetify)", "Adblock extension (Spicetify)")
        )
        self.spicetify_adblock_row.set_active(state.spicetify_adblock)
        apps_group.add(self.spicetify_adblock_row)

        self.spicetify_hide_podcasts_row = Adw.SwitchRow(
            title=L("Masquer les podcasts (Spicetify)", "Hide podcasts (Spicetify)")
        )
        self.spicetify_hide_podcasts_row.set_active(state.spicetify_hide_podcasts)
        apps_group.add(self.spicetify_hide_podcasts_row)

        self.spicetify_marketplace_row = Adw.SwitchRow(title="Spicetify Marketplace")
        self.spicetify_marketplace_row.set_active(state.spicetify_marketplace)
        apps_group.add(self.spicetify_marketplace_row)

        self.app_songrec_row = Adw.SwitchRow(title="SongRec")
        self.app_songrec_row.set_active(state.app_songrec)
        apps_group.add(self.app_songrec_row)

        self.app_easyeffects_row = Adw.SwitchRow(title="EasyEffects (+ rnnoise)")
        self.app_easyeffects_row.set_active(state.app_easyeffects)
        apps_group.add(self.app_easyeffects_row)

        self.app_signal_row = Adw.SwitchRow(
            title="Signal",
            subtitle=L("Messagerie chiffrée de bout en bout", "End-to-end encrypted messenger"),
        )
        self.app_signal_row.set_active(state.app_signal)
        apps_group.add(self.app_signal_row)

        self.app_zapzap_row = Adw.SwitchRow(
            title="ZapZap",
            subtitle=L("Client WhatsApp non-officiel", "Unofficial WhatsApp client"),
        )
        self.app_zapzap_row.set_active(state.app_zapzap)
        apps_group.add(self.app_zapzap_row)

        self.app_fluxer_row = Adw.SwitchRow(
            title="Fluxer",
            subtitle=L(
                "Alternative à Discord, auto-hébergeable (indépendant du choix Discord ci-dessus)",
                "Self-hostable Discord alternative (independent of the Discord choice above)",
            ),
        )
        self.app_fluxer_row.set_active(state.app_fluxer)
        apps_group.add(self.app_fluxer_row)

        box.append(apps_group)
        self._sync_spicetify_rows()

        # ── Content Creation ──
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

        # One switch per OBS plugin (like the gaming apps) — Aitum
        # Multistream replaces obs-multi-rtmp as the multistreaming
        # option (actively maintained successor from the Aitum team,
        # independent encoders/bitrate per platform).
        self.obs_plugin_rows = {}
        for attr, title_fr, title_en, default in (
            ("vkcapture", "VKCapture (capture jeux Vulkan/OpenGL)", "VKCapture (Vulkan/OpenGL game capture)", state.obs_plugin_vkcapture),
            ("pipewire_audio", "Pipewire Audio Capture (audio par application)", "Pipewire Audio Capture (per-app audio)", state.obs_plugin_pipewire_audio_capture),
            ("background_removal", "Background Removal (fond virtuel IA)", "Background Removal (AI virtual background)", state.obs_plugin_background_removal),
            ("move_transition", "Move Transition (animations de sources)", "Move Transition (source animations)", state.obs_plugin_move_transition),
            ("aitum_multistream", "Aitum Multistream (stream multi-plateformes)", "Aitum Multistream (multi-platform streaming)", state.obs_plugin_aitum_multistream),
            ("gstreamer", "GStreamer (sources/sorties supplémentaires)", "GStreamer (extra sources/outputs)", state.obs_plugin_gstreamer),
            ("composite_blur", "Composite Blur (flou/verre dépoli)", "Composite Blur (blur/glass filters)", state.obs_plugin_composite_blur),
            ("advanced_scene_switcher", "Advanced Scene Switcher (changement de scène auto)", "Advanced Scene Switcher (automated scene switching)", state.obs_plugin_advanced_scene_switcher),
            ("input_overlay", "Input Overlay (clavier/souris/manette à l'écran)", "Input Overlay (on-screen keyboard/mouse/gamepad)", state.obs_plugin_input_overlay),
            ("waveform", "Waveform (spectre/waveform audio)", "Waveform (audio waveform/spectrum)", state.obs_plugin_waveform),
        ):
            row = Adw.SwitchRow(title=L(title_fr, title_en))
            row.set_active(default)
            cc_group.add(row)
            self.obs_plugin_rows[attr] = row

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
        self.laptop_row.connect("notify::active", lambda *_: self._sync_laptop_row())
        self.gaming_row.connect("notify::active", lambda *_: self._sync_laptop_row())
        self.browser_row.connect("notify::selected", lambda *_: self._sync_brave_row())
        self.desktop_row.connect("notify::selected", lambda *_: self._sync_shell_row())
        self.desktop_row.connect("notify::selected", lambda *_: self._sync_latest_rows())
        self.shell_row.connect("notify::selected", lambda *_: self._sync_latest_rows())
        self.rgb_row.connect("notify::selected", lambda *_: self._sync_memory_rows())
        self.memory_rgb_row.connect("notify::active", lambda *_: self._sync_memory_rows())
        self.zen_row.connect("notify::active", lambda *_: self._sync_zen_rows())
        self.zen_sine_row.connect("notify::active", lambda *_: self._sync_zen_rows())
        self.music_player_row.connect("notify::selected", lambda *_: self._sync_spicetify_rows())
        self.content_creation_row.connect(
            "notify::active", lambda *_: self._sync_content_creation_rows()
        )
        self.gaming_row.connect("notify::active", lambda *_: self._sync_ananicy_row())
        self.autoupdate_row.connect(
            "notify::active", lambda *_: self._sync_autoupdate_row()
        )

        self._init_host_filter({
            "hw_group": hw_group, "browser_group": browser_group,
            "desktop_group": desktop_group, "sys_group": sys_group,
            "rgb_group": rgb_group, "extra_group": extra_group,
            "apps_group": apps_group, "cc_group": cc_group,
        })

        next_btn = Gtk.Button(
            label=L("Continuer", "Continue"),
            css_classes=["suggested-action", "pill"],
            halign=Gtk.Align.END,
            margin_top=12,
        )
        next_btn.connect("clicked", self._validate)
        box.append(next_btn)

        self.set_child(page_with_header(L("Options", "Options"), scroller))


    # ── per-host question filter (see host_profile.py) ───────────────────
    # row attribute -> nix option(s) it sets. A row is shown when any of
    # its options is listed in the host's local.nix.example.
    HOST_ROW_KEYS = {
        "gpu_row": ["hardware.myGpu"], "nvidia_laptop_row": ["hardware.nvidiaLaptop"],
        "laptop_row": ["roudix.laptop.enable"], "thinkpad_row": ["roudix.laptop.thinkpad"],
        "laptop_gaming_note": ["roudix.gaming.enable"],
        "undervolt_row": ["roudix.undervolt.only-amd.enable"], "cpu_row": ["hardware.myCpu"],
        "kernel_row": ["hardware.myKernel", "hardware.myKernelChaotic"],
        "browser_row": ["roudix.browsers"], "brave_variant_row": ["roudix.browsers"],
        "zen_row": ["roudix.zen.enable"], "zen_variant_row": ["roudix.zen.variant"],
        "zen_mods_row": ["roudix.zen.mods"], "zen_sine_row": ["roudix.zen.sine.enable"],
        "zen_sine_mods_row": ["roudix.zen.sine.mods"],
        "desktop_row": ["roudix.desktop.type"], "shell_row": ["roudix.desktop.shell"],
        "latest_de_row": ["roudix.desktop.latest.niri", "roudix.desktop.latest.mangowc", "roudix.desktop.latest.umbriel"],
        "latest_shell_row": ["roudix.desktop.latest.noctalia", "roudix.desktop.latest.dms", "roudix.desktop.latest.caelestia"],
        "latest_note": ["roudix.desktop.latest.niri", "roudix.desktop.latest.mangowc", "roudix.desktop.latest.umbriel", "roudix.desktop.latest.noctalia", "roudix.desktop.latest.dms", "roudix.desktop.latest.caelestia"],
        "default_shell_row": ["roudix.shell"], "terminal_row": ["roudix.terminal"],
        "file_manager_row": ["roudix.fileManager"], "editor_row": ["roudix.editor"],
        "desktop_integration_row": ["roudix.desktopIntegration"],
        "vm_guest_row": ["roudix.vmGuest.enable"], "gaming_row": ["roudix.gaming.enable"],
        "ananicy_row": ["roudix.gaming.ananicy.enable"],
        "millennium_row": ["roudix.gaming.steam.millennium.enable"],
        "mesa_git_row": ["roudix.mesa.useGit"], "timezone_row": ["time.timeZone"],
        "locale_row": ["i18n.defaultLocale"], "keymap_row": ["console.keyMap"],
        "gfx_keyboard_row": ["roudix.keyboardLayout"],
        "rgb_row": ["roudix.rgb"], "rgb_note": ["roudix.rgb"],
        "memory_rgb_row": ["roudix.memory.enable"], "memory_type_row": ["roudix.memory.type"],
        "memory_smbus_row": ["roudix.memory.smBus"], "memory_sku_row": ["roudix.memory.sku"],
        "gta_fix_row": ["roudix.hosts.gtaFix.enable"], "flatpak_row": ["roudix.flatpak.enable"],
        "virt_row": ["roudix.virtualization.enable"], "autoupdate_row": ["roudix.autoupdate.enable"],
        "autoupdate_interval_row": ["roudix.autoupdate.interval"],
        "branch_row": ["roudix.autoupdate.branch"], "bootloader_row": ["roudix.boot.bootloader"],
        "matrix_row": ["roudix.matrixClient"], "discord_row": ["roudix.discord"],
        "telegram_row": ["roudix.telegram"], "video_player_row": ["roudix.videoPlayer"],
        "torrent_client_row": ["roudix.torrentClient"], "music_player_row": ["roudix.musicPlayer"],
        "mail_client_row": ["roudix.mailClient"], "password_manager_row": ["roudix.passwordManager"],
        "waydroid_row": ["roudix.waydroid.enable"],
        "app_gimp_row": ["roudix.apps.gimp.enable"], "app_inkscape_row": ["roudix.apps.inkscape.enable"],
        "app_songrec_row": ["roudix.apps.songrec.enable"], "app_easyeffects_row": ["roudix.apps.easyeffects.enable"],
        "app_signal_row": ["roudix.apps.signal.enable"], "app_zapzap_row": ["roudix.apps.zapzap.enable"],
        "app_fluxer_row": ["roudix.apps.fluxer.enable"],
        "spicetify_theme_row": ["roudix.spicetify.theme"],
        "spicetify_color_scheme_row": ["roudix.spicetify.colorScheme"],
        "spicetify_adblock_row": ["roudix.spicetify.extensions.adblock.enable"],
        "spicetify_hide_podcasts_row": ["roudix.spicetify.extensions.hidePodcasts.enable"],
        "spicetify_marketplace_row": ["roudix.spicetify.marketplace.enable"],
        "content_creation_row": ["roudix.contentCreation.enable"], "obs_row": ["roudix.contentCreation.obs.enable"],
        "video_editor_row": ["roudix.contentCreation.videoEditor"],
        "virtual_camera_row": ["roudix.contentCreation.virtualCamera.enable"],
        "chatterino_row": ["roudix.contentCreation.streaming.chatterino.enable"],
    }
    # group -> rows it contains (a group with no visible row is hidden too)
    HOST_GROUP_ROWS = {
        "hw_group": ["gpu_row", "nvidia_laptop_row", "laptop_row", "thinkpad_row", "undervolt_row", "cpu_row", "kernel_row"],
        "browser_group": ["browser_row", "brave_variant_row", "zen_row", "zen_variant_row", "zen_mods_row", "zen_sine_row", "zen_sine_mods_row"],
        "desktop_group": ["desktop_row", "shell_row", "latest_de_row", "latest_shell_row", "latest_note", "default_shell_row", "terminal_row", "file_manager_row", "editor_row", "desktop_integration_row"],
        "sys_group": ["vm_guest_row", "gaming_row", "ananicy_row", "millennium_row", "mesa_git_row", "timezone_row", "locale_row", "keymap_row", "gfx_keyboard_row"],
        "rgb_group": ["rgb_row", "memory_rgb_row", "memory_type_row", "memory_smbus_row", "memory_sku_row"],
        "extra_group": ["gta_fix_row", "flatpak_row", "virt_row", "autoupdate_row", "autoupdate_interval_row", "branch_row", "bootloader_row", "matrix_row", "discord_row", "telegram_row", "video_player_row", "torrent_client_row", "music_player_row", "mail_client_row", "password_manager_row", "waydroid_row"],
        "apps_group": ["app_gimp_row", "app_inkscape_row", "spicetify_theme_row", "spicetify_color_scheme_row", "spicetify_adblock_row", "spicetify_hide_podcasts_row", "spicetify_marketplace_row", "app_songrec_row", "app_easyeffects_row", "app_signal_row", "app_zapzap_row", "app_fluxer_row"],
        "cc_group": ["content_creation_row", "obs_row", "video_editor_row", "virtual_camera_row", "chatterino_row"],
    }

    @staticmethod
    def _seed_allowed():
        """Values each row can actually show — an example value outside these
        is ignored (a combo would silently fall back to its first entry)."""
        def vals(pairs):
            return [v for v, _ in pairs]
        return {
            "gpu": ["amd", "amd-legacy", "nvidia", "intel"],
            "cpu": ["amd", "intel"],
            "kernel": vals(_kernels()),
            "kernel_chaotic": vals(_kernels_chaotic()),
            "browser": vals(_browsers()),
            "desktop": vals(_desktops()),
            "desktop_shell": lambda st: vals(_shells(st.desktop)),
            "default_shell": vals(_default_shells()),
            "terminal": vals(_terminals()),
            "file_manager": vals(_file_managers()),
            "editor": vals(_editors()),
            "desktop_integration": vals(_desktop_integrations()),
            "rgb": vals(_rgb_options()),
            "bootloader": vals(_bootloaders()),
            "branch": vals(_branches()),
            "matrix_client": vals(_matrix()),
            "discord": vals(_discord()),
            "telegram": vals(_telegram()),
            "video_player": vals(_video_player()),
            "torrent_client": vals(_torrent_client()),
            "music_player": vals(_music_player()),
            "mail_client": vals(_mail_client()),
            "password_manager": vals(_password_manager()),
            "spicetify_theme": vals(_spicetify_themes()),
            "timezone": vals(_timezones()),
            "locale": vals(_locales()),
            "keymap": vals(_keymaps()),
            "zen_variant": ["twilight", "beta"],
            "memory_type": ["ddr5", "ddr4"],
        }

    @staticmethod
    def _make_hideable(widget):
        """The _sync_* methods keep calling widget.set_visible(...) to show or
        hide rows depending on other answers; wrap it so a row hidden by the
        host profile stays hidden whatever they ask for."""
        if getattr(widget, "_host_hideable", False):
            return
        original = widget.set_visible
        widget._host_hidden = False
        widget._host_original_set_visible = original
        widget._host_hideable = True
        widget.set_visible = lambda visible, _w=widget, _o=original: _o(False if _w._host_hidden else visible)

    def _init_host_filter(self, groups):
        self._host_groups = groups
        self._host_widgets = []          # (widget, [option keys])
        for attr, keys in self.HOST_ROW_KEYS.items():
            w = getattr(self, attr, None)
            if w is not None:
                self._make_hideable(w)
                self._host_widgets.append((w, keys))
        # rows built in loops
        for attr, row in getattr(self, "gaming_apps_rows", {}).items():
            self._make_hideable(row)
            self._host_widgets.append((row, [f"roudix.gaming.apps.{attr}.enable"]))
        for row in getattr(self, "obs_plugin_rows", {}).values():
            self._make_hideable(row)
            self._host_widgets.append((row, ["roudix.contentCreation.obs.enable"]))
        self._on_hostname_changed()

    def _on_hostname_changed(self):
        # The host (hosts/<name>/, also networking.hostName) is chosen on the
        # Welcome page, before this page is built.
        listed = host_profile.listed_options(self.state.hostname or "roudix")
        for widget, keys in self._host_widgets:
            hidden = listed is not None and not any(k in listed for k in keys)
            widget._host_hidden = hidden
            widget._host_original_set_visible(not hidden)
        # let the existing sync methods recompute the dynamic rows
        for name in ("_sync_nvidia_row", "_sync_undervolt_row", "_sync_laptop_row", "_sync_kernel_row",
                     "_sync_brave_row", "_sync_shell_row", "_sync_latest_rows", "_sync_desktop_integration_row",
                     "_sync_file_manager_row", "_sync_memory_rows", "_sync_zen_rows",
                     "_sync_spicetify_rows", "_sync_ananicy_row", "_sync_content_creation_rows",
                     "_sync_autoupdate_row"):
            try:
                getattr(self, name)()
            except Exception:
                pass
        for gname, group in self._host_groups.items():
            rows = [getattr(self, r, None) for r in self.HOST_GROUP_ROWS[gname]]
            group.set_visible(any(r is not None and not getattr(r, "_host_hidden", False) for r in rows))

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

    def _sync_laptop_row(self):
        self.thinkpad_row.set_visible(self.laptop_row.get_active())
        self.laptop_gaming_note.set_visible(
            self.laptop_row.get_active() and self.gaming_row.get_active()
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
        self.shell_row.set_visible(desktop in ("niri", "hyprland", "mangowc", "umbriel"))

        pairs = _shells(desktop)
        values = [v for v, _ in pairs]
        labels = [l for _, l in pairs]
        # Keep whatever the user already had selected if it's still a valid
        # choice for this compositor (e.g. switching mangowc → niri keeps
        # "dms"); otherwise fall back to noctalia rather than leaving a
        # now-invalid selection (e.g. "caelestia" surviving a switch away
        # from hyprland, or anything but noctalia surviving a switch to
        # umbriel).
        try:
            current = self._selected_value(self.shell_row)
        except (KeyError, IndexError):
            current = self.state.desktop_shell
        self.shell_row.set_model(Gtk.StringList.new(labels))
        self.shell_row.set_selected(values.index(current) if current in values else 0)
        self._rows[id(self.shell_row)] = values

    def _sync_latest_rows(self):
        """Show the nixpkgs/latest switch of the selected compositor and of
        the selected shell, and only those (Hyprland has no flake version)."""
        desktop = self._selected_value(self.desktop_row)
        has_shell = desktop in ("niri", "hyprland", "mangowc", "umbriel")
        try:
            shell = self._selected_value(self.shell_row) if has_shell else None
        except (KeyError, IndexError):
            # shell_row's model is being rebuilt by _sync_shell_row: the
            # final call (after it finishes) will see a consistent state.
            shell = None

        de_visible = desktop in LATEST_DESKTOPS
        shell_visible = shell in LATEST_SHELLS
        self.latest_de_row.set_visible(de_visible)
        self.latest_shell_row.set_visible(shell_visible)
        if de_visible:
            self.latest_de_row.set_title(_latest_title(LATEST_DESKTOPS[desktop]))
            self.latest_de_row.set_active(getattr(self.state, f"latest_{desktop}", False))
        if shell_visible:
            self.latest_shell_row.set_title(_latest_title(LATEST_SHELLS[shell]))
            self.latest_shell_row.set_active(getattr(self.state, f"latest_{shell}", False))
        self.latest_note.set_visible(de_visible or shell_visible)

    def _sync_desktop_integration_row(self):
        # GNOME/KDE manage their own keyring/portal stack — this option
        # only matters for the "bare" compositors.
        desktop = self._selected_value(self.desktop_row)
        self.desktop_integration_row.set_visible(
            desktop in ("niri", "hyprland", "mangowc", "umbriel")
        )

    def _sync_file_manager_row(self):
        # GNOME/KDE have one obvious native file manager, so hide the
        # question entirely and lock the value to it — matches
        # roudix-installer.sh, which doesn't even ask on those desktops.
        # niri/hyprland/mangowc/umbriel don't ship an opinionated file manager, so
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

    def _sync_spicetify_rows(self):
        spotify_active = self._selected_value(self.music_player_row) == "spotify"
        for row in (
            self.spicetify_theme_row,
            self.spicetify_color_scheme_row,
            self.spicetify_adblock_row,
            self.spicetify_hide_podcasts_row,
            self.spicetify_marketplace_row,
        ):
            row.set_visible(spotify_active)

    def _sync_ananicy_row(self):
        self.ananicy_row.set_visible(self.gaming_row.get_active())
        self.millennium_row.set_visible(self.gaming_row.get_active())
        for row in self.gaming_apps_rows.values():
            row.set_visible(self.gaming_row.get_active())

    def _sync_content_creation_rows(self):
        active = self.content_creation_row.get_active()
        for row in (
            self.obs_row,
            self.video_editor_row,
            self.virtual_camera_row,
            self.chatterino_row,
        ):
            row.set_visible(active)
        for row in self.obs_plugin_rows.values():
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
        s.laptop = self.laptop_row.get_active()
        s.laptop_thinkpad = self.thinkpad_row.get_active()
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
        # nixpkgs (False) / latest-flake (True): only the compositor and the
        # shell actually chosen keep their switch; the others fall back to
        # the nixpkgs default so a stale answer is never written.
        for _name in ("niri", "mangowc", "umbriel", "noctalia", "dms", "caelestia"):
            setattr(s, f"latest_{_name}", False)
        if self.latest_de_row.get_visible() and s.desktop in LATEST_DESKTOPS:
            setattr(s, f"latest_{s.desktop}", self.latest_de_row.get_active())
        if self.latest_shell_row.get_visible() and s.desktop_shell in LATEST_SHELLS:
            setattr(s, f"latest_{s.desktop_shell}", self.latest_shell_row.get_active())
        s.default_shell = self._selected_value(self.default_shell_row)
        s.terminal = self._selected_value(self.terminal_row)
        s.file_manager = self._selected_value(self.file_manager_row)
        s.editor = self._selected_value(self.editor_row)
        s.desktop_integration = self._selected_value(self.desktop_integration_row)

        s.vm_guest = self.vm_guest_row.get_active()
        s.gaming = self.gaming_row.get_active()
        s.ananicy_enable = self.ananicy_row.get_active()
        s.gaming_steam_millennium = self.millennium_row.get_active()
        s.gaming_apps_lutris = self.gaming_apps_rows["lutris"].get_active()
        s.gaming_apps_heroic = self.gaming_apps_rows["heroic"].get_active()
        s.gaming_apps_faugus = self.gaming_apps_rows["faugus"].get_active()
        s.gaming_apps_prismlauncher = self.gaming_apps_rows["prismlauncher"].get_active()
        s.gaming_apps_modrinth = self.gaming_apps_rows["modrinth"].get_active()
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
        s.branch = self._selected_value(self.branch_row)
        s.bootloader = self._selected_value(self.bootloader_row)
        s.matrix_client = self._selected_value(self.matrix_row)
        s.discord = self._selected_value(self.discord_row)
        s.telegram = self._selected_value(self.telegram_row)
        s.video_player = self._selected_value(self.video_player_row)
        s.torrent_client = self._selected_value(self.torrent_client_row)
        s.music_player = self._selected_value(self.music_player_row)
        s.mail_client = self._selected_value(self.mail_client_row)
        s.password_manager = self._selected_value(self.password_manager_row)
        s.waydroid_enable = self.waydroid_row.get_active()
        s.app_gimp = self.app_gimp_row.get_active()
        s.app_inkscape = self.app_inkscape_row.get_active()
        s.spicetify_theme = self._selected_value(self.spicetify_theme_row)
        s.spicetify_color_scheme = self.spicetify_color_scheme_row.get_text().strip()
        s.spicetify_adblock = self.spicetify_adblock_row.get_active()
        s.spicetify_hide_podcasts = self.spicetify_hide_podcasts_row.get_active()
        s.spicetify_marketplace = self.spicetify_marketplace_row.get_active()
        s.app_songrec = self.app_songrec_row.get_active()
        s.app_easyeffects = self.app_easyeffects_row.get_active()
        s.app_signal = self.app_signal_row.get_active()
        s.app_zapzap = self.app_zapzap_row.get_active()
        s.app_fluxer = self.app_fluxer_row.get_active()

        s.content_creation_enable = self.content_creation_row.get_active()
        s.obs_enable = self.obs_row.get_active()
        s.obs_plugin_vkcapture = self.obs_plugin_rows["vkcapture"].get_active()
        s.obs_plugin_pipewire_audio_capture = self.obs_plugin_rows["pipewire_audio"].get_active()
        s.obs_plugin_background_removal = self.obs_plugin_rows["background_removal"].get_active()
        s.obs_plugin_move_transition = self.obs_plugin_rows["move_transition"].get_active()
        s.obs_plugin_aitum_multistream = self.obs_plugin_rows["aitum_multistream"].get_active()
        s.obs_plugin_gstreamer = self.obs_plugin_rows["gstreamer"].get_active()
        s.obs_plugin_composite_blur = self.obs_plugin_rows["composite_blur"].get_active()
        s.obs_plugin_advanced_scene_switcher = self.obs_plugin_rows["advanced_scene_switcher"].get_active()
        s.obs_plugin_input_overlay = self.obs_plugin_rows["input_overlay"].get_active()
        s.obs_plugin_waveform = self.obs_plugin_rows["waveform"].get_active()
        s.video_editor = self._selected_value(self.video_editor_row)
        s.virtual_camera_enable = self.virtual_camera_row.get_active()
        s.chatterino_enable = self.chatterino_row.get_active()

        self.on_next()
