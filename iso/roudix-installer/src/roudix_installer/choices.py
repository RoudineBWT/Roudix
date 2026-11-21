"""
Option lists of the installer, shared by every front-end (GTK pages, TUI).

Each function returns ``[(value, label), ...]``: ``value`` is what ends up in
InstallState / local.nix, ``label`` is the translated text shown to the user.
They are functions (not module constants) so the labels follow whichever
language was chosen on the first screen before the lists are built.

No GTK import here on purpose: the TUI must work on a machine (or a minimal
ISO) where PyGObject is not even installed.
"""
from roudix_installer.hardware_detect import detect_main_screen
from roudix_installer.i18n import tr, trc


def _kernels():
    return [
        (
            "cachyos-latest",
            tr("Standard latest CachyOS kernel"),
        ),
        (
            "cachyos-latest-v3",
            tr("x86_64-v3 optimized (recommended, recent CPUs)"),
        ),
        (
            "cachyos-latest-lto",
            tr("LTO build — better performance"),
        ),
        (
            "cachyos-latest-lto-v3",
            tr("LTO + x86_64-v3 (best performance, recent CPUs)"),
        ),
        ("cachyos-lts", tr("Long-term support")),
        ("cachyos-lts-v3", "LTS + x86_64-v3"),
        (
            "cachyos-lts-lto-v3",
            tr("LTS + LTO + x86_64-v3 (stable + fast)"),
        ),
        (
            "cachyos-rc",
            tr("Release candidate — bleeding edge"),
        ),
        ("zen", tr("linux-zen (nixpkgs) — outside the xddxdd overlay")),
        ("nixpkgs-lts", tr("nixpkgs default LTS — outside the xddxdd overlay")),
        ("nixpkgs-latest", tr("nixpkgs latest mainline — outside the xddxdd overlay")),
        ("nixpkgs-testing", tr("nixpkgs testing (RC/mainline) — outside the xddxdd overlay")),
        ("xanmod-lts", tr("XanMod LTS (nixpkgs) — outside the xddxdd overlay")),
        ("xanmod-latest", tr("XanMod main branch (nixpkgs) — outside the xddxdd overlay")),
    ]


def _kernels_chaotic():
    # Chaotic-Nyx — deliberately smaller set than xddxdd (no LTO here:
    # out-of-tree modules like nvidia are more fragile with it). Required
    # for nvidia_cachyos, the precompiled Nvidia driver matched to this kernel.
    return [
        ("cachyos", tr("Default — LTO + BORE")),
        ("cachyos-lts", tr("Long-term support")),
        ("cachyos-server", tr("Server optimized (no desktop tuning)")),
        ("cachyos-hardened", tr("Security hardened")),
        ("zen", tr("linux-zen (nixpkgs) — locally-rebuilt nvidia module")),
        ("nixpkgs-lts", tr("nixpkgs default LTS — locally-rebuilt nvidia module")),
        ("nixpkgs-latest", tr("nixpkgs latest mainline — locally-rebuilt nvidia module")),
        ("nixpkgs-testing", tr("nixpkgs testing (RC/mainline) — locally-rebuilt nvidia module")),
        ("xanmod-lts", tr("XanMod LTS (nixpkgs) — locally-rebuilt nvidia module")),
        ("xanmod-latest", tr("XanMod main branch (nixpkgs) — locally-rebuilt nvidia module")),
    ]


def _browsers():
    return [
        ("none", tr("None")),
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
        ("brave", tr("Stable (recommended)")),
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
        ("cinnamon", tr("Cinnamon (X11, older PCs)")),
        ("cosmic", tr("COSMIC (System76, Rust)")),
        ("hyprland", "Hyprland"),
        ("mangowc", "MangoWC"),
        ("umbriel", "Umbriel"),
    ]


def _mark_detected(pairs, detected_value):
    """Appends '(détecté)' to the label of the auto-detected entry, if any."""
    if not detected_value:
        return pairs
    return [
        (value, f"{label} " + tr("(detected)") if value == detected_value else label)
        for value, label in pairs
    ]


def _shells(desktop=None):
    # Umbriel only has Noctalia support so far; Caelestia's setup is
    # Hyprland-specific (its Quickshell config assumes Hyprland's IPC), so it
    # only makes sense to offer it there. Niri/MangoWC get Noctalia + DMS.
    if desktop == "umbriel":
        return [("noctalia", tr("Noctalia — default shell"))]

    base = [
        ("noctalia", tr("Noctalia — default shell")),
        ("dms", "Dux Shell — Material 3"),
    ]
    if desktop == "hyprland":
        base = base + [
            (
                "caelestia",
                tr("Caelestia — Quickshell setup"),
            )
        ]
    return base


# Compositors / shells that have a flake ("latest") version next to the
# nixpkgs one. Hyprland has no flake version in Roudix: no switch for it.
LATEST_DESKTOPS = {}  # niri / MangoWC / Umbriel: always the flake version
LATEST_SHELLS = {"noctalia": "Noctalia", "dms": "DMS", "caelestia": "Caelestia"}


def _latest_title(name):
    return tr("{name} — latest version (flake)").format(name=name)


def _default_shells():
    return [("fish", tr("Fish (recommended)")), ("bash", "Bash")]


def _terminals():
    return [
        ("ghostty", tr("Ghostty (recommended)")),
        ("kitty", "Kitty"),
        ("alacritty", "Alacritty"),
        ("foot", tr("Foot (native Wayland, lightweight)")),
        ("wezterm", "WezTerm"),
    ]


def _file_managers(shell=None):
    base = [
        ("nautilus", tr("Nautilus — GNOME Files (recommended)")),
        ("dolphin", tr("Dolphin — KDE")),
        ("thunar", tr("Thunar — XFCE, lightweight")),
        ("nemo", tr("Nemo — Cinnamon")),
    ]
    # Luciole is Noctalia's own file manager: only offered with the Noctalia
    # shell (the NixOS module asserts roudix.fileManager = "luciole" needs
    # roudix.desktop.shell = "noctalia").
    if shell == "noctalia":
        base = base + [("luciole", tr("Luciole — Noctalia, native Wayland"))]
    return base


def _editors():
    return [
        ("zed", tr("Zed — fast, modern (recommended)")),
        ("vscode", "Visual Studio Code"),
        ("neovim", "Neovim"),
        (
            "none",
            tr("None — I'll manage my own editor (AppImage, Flatpak...)"),
        ),
    ]


def _desktop_integrations():
    return [
        (
            "gnome",
            tr("GNOME keyring + xdg-desktop-portal-gtk/-gnome (recommended)"),
        ),
        (
            "kde",
            tr("KWallet + xdg-desktop-portal-kde (useful if you mainly run Qt/KDE apps)"),
        ),
    ]


def _rgb_options():
    return [
        ("openlinkhub", "OpenLinkHub — Corsair (iCUE Link, Commander...)"),
        (
            "openrgb",
            tr("OpenRGB — mixed brands (Razer, ASUS, MSI...)"),
        ),
        ("none", tr("No RGB control")),
    ]


def _bootloaders():
    return [
        ("limine", tr("Limine (recommended)")),
        ("systemd-boot", "systemd-boot"),
    ]


def _plymouth_themes():
    # roudix.boot.plymouth.theme — "none" is not a theme: it sets plymouth.enable = false.
    return [
        ("roudix", tr("Roudix — logo, gentle pulse (default)")),
        ("roudix-spin", tr("Roudix Spin — logo turning slowly")),
        ("roudix-gradient", tr("Roudix Gradient — warm gradient, glow behind the logo")),
        ("roudix-ember", tr("Roudix Ember — rising embers, progress ring")),
        ("roudix-panda", tr("Pandoudix — the mascot")),
        ("none", tr("No splash — plain text boot")),
    ]


def _eac_vendors():
    # roudix.boot.eac.vendor — whose signed kernel the "NixOS EAC" entry boots.
    return [
        ("fedora", tr("Fedora kernel (nothing to enroll)")),
        ("bazzite", tr("Bazzite OGC kernel (Universal Blue's key to enroll after the install)")),
    ]


def _boot_aspects():
    # roudix.boot.wallpaperAspect — one Limine wallpaper per screen ratio; it is
    # stretched to the screen, so it has to match the MAIN screen's ratio.
    return [
        ("16x9", "16:9 — 1920x1080, 2560x1440, 4K"),
        ("16x10", "16:10 — 1920x1200, 2560x1600"),
        ("21x9", "21:9 — 2560x1080, 3440x1440 (ultrawide)"),
        ("4x3", "4:3 — 1024x768, 1280x1024"),
    ]


def _boot_resolutions(main_res):
    # roudix.boot.menuResolution — "auto" lets Limine pick; with several screens it
    # can end up on the smaller one, so the MAIN screen's resolution can be forced.
    pairs = [("auto", tr("Automatic (Limine decides)"))]
    if main_res:
        pairs.append((main_res, tr("Main screen: {res}").format(res=main_res)))
    return pairs


def _branches():
    return [
        ("main", tr("main — stable, ~every 2 weeks (recommended)")),
        ("testing", tr("testing — ~every 2 days, may occasionally break")),
        ("dev", tr("dev — latest changes, least stable")),
    ]


def _matrix():
    return [
        ("none", tr("None")),
        ("element", "Element Desktop"),
        ("cinny", tr("Cinny (lightweight, web)")),
    ]


def _discord():
    return [
        ("vencord", tr("Vencord (pre-installed)")),
        ("vanilla", tr("Vanilla (no patch)")),
        ("vesktop", tr("Vesktop (standalone Vencord)")),
        ("none", tr("None")),
    ]


def _telegram():
    return [
        ("none", tr("None")),
        ("telegram", tr("Telegram (official client)")),
        ("ayugram", tr("AyuGram (fork: ghost mode, anti-recall...)")),
    ]


def _video_player():
    return [
        ("vlc", tr("VLC (widest format support)")),
        ("clapper", tr("Clapper (modern GTK4)")),
        ("mpv", tr("mpv (+ yt-dlp)")),
        ("celluloid", tr("Celluloid (GTK front-end for mpv)")),
        ("none", tr("None")),
    ]


def _torrent_client():
    return [
        ("none", tr("None")),
        ("qbittorrent", "qBittorrent"),
        ("fragments", tr("Fragments (minimal GNOME client)")),
        ("deluge", "Deluge"),
    ]


def _music_player():
    return [
        ("spotify", tr("Spotify + Spicetify")),
        ("ytmdesktop", "YouTube Music Desktop"),
        ("sonora", "Sonora (Spotify / YouTube Music)"),
        ("none", tr("None")),
    ]


def _fluxer_channel():
    return [
        ("stable", tr("Stable")),
        ("canary", tr("Canary (fresher, may break)")),
    ]


def _mail_client():
    return [
        ("none", tr("None")),
        ("thunderbird", tr("Thunderbird (full-featured)")),
        (
            "betterbird",
            tr("Betterbird (Thunderbird fork)"),
        ),
        ("geary", tr("Geary (lightweight, GNOME)")),
    ]


def _password_manager():
    return [
        ("none", tr("None")),
        ("bitwarden", tr("Bitwarden (cloud-synced vault)")),
        ("keepassxc", tr("KeePassXC (local, offline vault)")),
        ("protonpass", tr("Proton Pass (cloud-synced vault)")),
    ]


def _office():
    return [
        ("none", tr("None")),
        ("libreoffice", tr("LibreOffice (Writer, Calc, Impress)")),
        ("onlyoffice", tr("ONLYOFFICE (Word-style editors, .docx / .xlsx / .pptx)")),
    ]


def _spicetify_themes():
    return [
        ("colorful", tr("Colorful (default)")),
        ("comfy", "Comfy"),
    ]


def _timezones():
    return [
        ("Europe/Brussels", tr("Belgium")),
        ("Europe/Paris", "France"),
        ("Europe/London", tr("United Kingdom")),
        ("Europe/Amsterdam", tr("Netherlands")),
        ("Europe/Berlin", tr("Germany")),
        ("Europe/Vienna", tr("Austria")),
        ("Europe/Zurich", tr("Switzerland")),
        ("Europe/Luxembourg", "Luxembourg"),
        ("Europe/Madrid", tr("Spain")),
        ("Europe/Lisbon", "Portugal"),
        ("Europe/Rome", tr("Italy")),
        ("Europe/Warsaw", tr("Poland")),
        ("Europe/Prague", tr("Czech Republic")),
        ("Europe/Bratislava", tr("Slovakia")),
        ("Europe/Budapest", tr("Hungary")),
        ("Europe/Bucharest", tr("Romania")),
        ("Europe/Sofia", tr("Bulgaria")),
        ("Europe/Athens", tr("Greece")),
        ("Europe/Helsinki", tr("Finland")),
        ("Europe/Stockholm", tr("Sweden")),
        ("Europe/Oslo", tr("Norway")),
        ("Europe/Copenhagen", tr("Denmark")),
        ("Europe/Tallinn", tr("Estonia")),
        ("Europe/Riga", tr("Latvia")),
        ("Europe/Vilnius", tr("Lithuania")),
        ("Europe/Kiev", "Ukraine"),
        ("Europe/Moscow", tr("Russia (Moscow)")),
        ("Europe/Istanbul", tr("Turkey")),
        ("Atlantic/Reykjavik", tr("Iceland")),
        ("Africa/Casablanca", tr("Morocco")),
        ("Africa/Algiers", tr("Algeria")),
        ("Africa/Tunis", tr("Tunisia")),
        ("Africa/Cairo", tr("Egypt")),
        ("Africa/Johannesburg", tr("South Africa")),
        ("Africa/Lagos", tr("Nigeria")),
        ("Africa/Nairobi", "Kenya"),
        ("America/New_York", tr("United States (East)")),
        ("America/Chicago", tr("United States (Central)")),
        ("America/Denver", tr("United States (Mountain)")),
        ("America/Los_Angeles", tr("United States (West)")),
        ("America/Anchorage", tr("United States (Alaska)")),
        ("Pacific/Honolulu", tr("United States (Hawaii)")),
        ("America/Toronto", tr("Canada (East)")),
        ("America/Vancouver", tr("Canada (West)")),
        ("America/Mexico_City", tr("Mexico")),
        ("America/Bogota", tr("Colombia")),
        ("America/Lima", tr("Peru")),
        ("America/Santiago", tr("Chile")),
        ("America/Buenos_Aires", tr("Argentina")),
        ("America/Sao_Paulo", tr("Brazil (São Paulo)")),
        ("America/Caracas", "Venezuela"),
        ("Asia/Dubai", tr("United Arab Emirates")),
        ("Asia/Riyadh", tr("Saudi Arabia")),
        ("Asia/Jerusalem", tr("Israel")),
        ("Asia/Beirut", tr("Lebanon")),
        ("Asia/Baghdad", tr("Iraq")),
        ("Asia/Tehran", "Iran"),
        ("Asia/Karachi", "Pakistan"),
        ("Asia/Kolkata", tr("India")),
        ("Asia/Dhaka", "Bangladesh"),
        ("Asia/Colombo", "Sri Lanka"),
        ("Asia/Kathmandu", tr("Nepal")),
        ("Asia/Almaty", "Kazakhstan"),
        ("Asia/Tashkent", tr("Uzbekistan")),
        ("Asia/Bangkok", tr("Thailand")),
        ("Asia/Ho_Chi_Minh", "Vietnam"),
        ("Asia/Jakarta", tr("Indonesia (West)")),
        ("Asia/Singapore", tr("Singapore")),
        ("Asia/Kuala_Lumpur", tr("Malaysia")),
        ("Asia/Manila", "Philippines"),
        ("Asia/Shanghai", tr("China")),
        ("Asia/Hong_Kong", "Hong Kong"),
        ("Asia/Taipei", tr("Taiwan")),
        ("Asia/Seoul", tr("South Korea")),
        ("Asia/Tokyo", tr("Japan")),
        ("Australia/Perth", tr("Australia (West)")),
        ("Australia/Adelaide", tr("Australia (Central)")),
        ("Australia/Sydney", tr("Australia (East)")),
        ("Pacific/Auckland", tr("New Zealand")),
        ("Pacific/Fiji", tr("Fiji")),
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
        ("C.UTF-8", tr("C (minimal POSIX)")),
    ]


def _keymaps():
    return [
        ("us", "English (US) QWERTY"),
        ("us-acentos", tr("English (US) International (dead keys)")),
        ("uk", "English (UK) QWERTY"),
        ("be-latin1", tr("Belgian AZERTY")),
        ("fr", tr("French AZERTY")),
        ("fr-latin9", tr("French AZERTY (latin9)")),
        ("fr_CH", trc("console keymap list", "Swiss French QWERTZ")),
        ("de", tr("German QWERTZ")),
        ("de-latin1", tr("German QWERTZ (latin1)")),
        ("at", tr("Austrian QWERTZ")),
        ("ch", tr("Swiss QWERTZ")),
        ("nl", tr("Dutch QWERTY")),
        ("es", tr("Spanish QWERTY")),
        ("es-cp850", tr("Spanish QWERTY (cp850)")),
        ("pt-latin1", tr("Portuguese QWERTY (latin1)")),
        ("br-abnt2", tr("Brazilian Portuguese ABNT2")),
        ("it", tr("Italian QWERTY")),
        ("it-latin1", tr("Italian QWERTY (latin1)")),
        ("pl2", tr("Polish QWERTY")),
        ("ru", tr("Russian")),
        ("ua", tr("Ukrainian")),
        ("cz-lat2", tr("Czech QWERTY (latin2)")),
        ("sk-qwerty", tr("Slovak QWERTY")),
        ("hu", tr("Hungarian QWERTY")),
        ("ro", tr("Romanian QWERTY")),
        ("trq", tr("Turkish Q")),
        ("trf", tr("Turkish F")),
        ("jp106", tr("Japanese 106-key")),
        ("sv-latin1", tr("Swedish QWERTY (latin1)")),
        ("no-latin1", tr("Norwegian QWERTY (latin1)")),
        ("dk-latin1", tr("Danish QWERTY (latin1)")),
        ("fi-latin1", tr("Finnish QWERTY (latin1)")),
        ("gr", tr("Greek")),
        ("il", tr("Hebrew")),
        ("arabic", tr("Arabic")),
        ("dvorak", "Dvorak (US)"),
        ("dvorak-l", tr("Dvorak left")),
        ("dvorak-r", tr("Dvorak right")),
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
        ("us:intl", tr("US International (dead keys, recommended)")),
        ("us:", tr("US Basic QWERTY (no variant)")),
        ("gb:", tr("British QWERTY")),
        ("be:", tr("Belgian AZERTY")),
        ("fr:", tr("French AZERTY")),
        ("fr:bepo", tr("French BÉPO")),
        ("de:", tr("German QWERTZ")),
        ("ch:fr", trc("graphical keyboard layout list", "Swiss French QWERTZ")),
        ("ch:de", tr("Swiss German QWERTZ")),
        ("nl:", tr("Dutch QWERTY")),
        ("es:", tr("Spanish QWERTY")),
        ("it:", tr("Italian QWERTY")),
        ("pt:", tr("Portuguese QWERTY")),
        ("pl:", tr("Polish QWERTY")),
        ("ru:", tr("Russian")),
        ("ua:", tr("Ukrainian")),
        ("jp:", tr("Japanese")),
        ("us:dvorak", tr("Dvorak (US)")),
        ("us:colemak", tr("Colemak (US)")),
    ]


# ── Short lists that used to be written inline in the GTK options page ─────

def _gpus():
    return [
        ("amd", "AMD — RDNA / GCN 3+"),
        ("amd-igpu", tr("AMD integrated (Ryzen APU)")),
        ("amd-legacy", tr("AMD legacy — GCN 1.x/2.x")),
        ("nvidia", "NVIDIA"),
        ("intel", tr("Intel (integrated / Arc)")),
    ]


def _cpus():
    return [("amd", "AMD"), ("intel", "Intel")]


def _laptop_backends():
    return [
        ("tlp", tr("TLP — best battery life")),
        ("tuned", tr("tuned — gaming laptop (keeps game-performance)")),
    ]


def _nvidia_kernel_sources():
    return [("chaotic", "Chaotic-Nyx"), ("xddxdd", "xddxdd")]


def _nvidia_driver_sources():
    return [("chaotic", "Chaotic-Nyx"), ("nixpkgs", "nixpkgs")]


def _mesa_git_sources():
    return [("chaotic", "Chaotic-Nyx"), ("gaming-edge", "nix-gaming-edge")]


def _zen_variants():
    return [("twilight", tr("Twilight (default)")), ("beta", "Beta")]


def _memory_types():
    return [("ddr5", "DDR5"), ("ddr4", "DDR4")]


def _video_editors():
    return [
        ("kdenlive", "Kdenlive"),
        ("davinci-resolve", tr("DaVinci Resolve (free)")),
        ("davinci-resolve-studio", tr("DaVinci Resolve Studio (paid)")),
        ("shotcut", "Shotcut"),
        ("none", tr("None")),
    ]


# ── Welcome screen texts ────────────────────────────────────────────────────

def host_label(name: str) -> str:
    return {
        "roudix": tr("roudix — full desktop, every option"),
        "nixie": tr("nixie — light laptop, few questions"),
    }.get(name, name)


def welcome_text(existing: bool) -> str:
    if existing:
        return tr("This machine already runs NixOS. Roudix is built next to your current system: "
                  "nothing is wiped, /etc/nixos is backed up first, and your previous system stays "
                  "in the boot menu. Two steps: options, then off we go.")
    return tr("We're about to install Roudix on this machine. Three steps: disk, options, then off we go.")


def host_note(name: str) -> str:
    from roudix_installer import host_profile
    if host_profile.find_example(name) is None:
        return tr("Warning: this profile can't be found in this ISO — every question will be asked.")
    if host_profile.listed_options(name) is None:
        return tr("Every question will be asked.")
    return tr("Only the questions relevant to this profile will be asked.")


# ── Values the profile example may pre-fill (host_defaults.seed_state) ─────

def seed_allowed():
    """Values each question can actually offer — an example value outside these
    is ignored (a menu would silently fall back to its first entry)."""
    def vals(pairs):
        return [v for v, _ in pairs]
    return {
        "gpu": vals(_gpus()),
        "cpu": vals(_cpus()),
        "kernel": vals(_kernels()),
        "kernel_chaotic": vals(_kernels_chaotic()),
        "nvidia_kernel_source": vals(_nvidia_kernel_sources()),
        "nvidia_driver_source": vals(_nvidia_driver_sources()),
        "mesa_git_source": vals(_mesa_git_sources()),
        "browser": vals(_browsers()),
        "desktop": vals(_desktops()),
        "desktop_shell": lambda st: vals(_shells(st.desktop)),
        "default_shell": vals(_default_shells()),
        "terminal": vals(_terminals()),
        "file_manager": lambda st: vals(_file_managers(st.desktop_shell)),
        "editor": vals(_editors()),
        "desktop_integration": vals(_desktop_integrations()),
        "rgb": vals(_rgb_options()),
        "bootloader": vals(_bootloaders()),
        "boot_aspect": vals(_boot_aspects()),
        "eac_vendor": vals(_eac_vendors()),
        "plymouth_theme": vals(_plymouth_themes()),
        "boot_resolution": lambda st: [v for v, _ in _boot_resolutions(detect_main_screen()[0])],
        "branch": vals(_branches()),
        "matrix_client": vals(_matrix()),
        "discord": vals(_discord()),
        "telegram": vals(_telegram()),
        "video_player": vals(_video_player()),
        "torrent_client": vals(_torrent_client()),
        "music_player": vals(_music_player()),
        "mail_client": vals(_mail_client()),
        "app_fluxer_channel": vals(_fluxer_channel()),
        "password_manager": vals(_password_manager()),
        "office": vals(_office()),
        "spicetify_theme": vals(_spicetify_themes()),
        "timezone": vals(_timezones()),
        "locale": vals(_locales()),
        "keymap": vals(_keymaps()),
        "zen_variant": vals(_zen_variants()),
        "memory_type": vals(_memory_types()),
    }
