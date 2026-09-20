"""
Single source of truth for everything the wizard collects.
Field names/values map 1:1 onto what roudix-installer.sh already
asks for and sed-writes into hosts/roudix/local.nix — same options,
same defaults, just fed by GUI state instead of `read -p`.

Deliberately NOT covered yet (same as the TODO list in the installer
README): EFI multi-boot NVRAM detection and btrfs subvolume auto-patch
of hardware-configuration.nix. These stay manual/skipped for now —
flagged, not silently dropped.

RAM RGB SMBus/SKU are no longer auto-detect TODOs: local.nix.example
now ships explicit roudix.memory.smBus / roudix.memory.sku keys, so
they're tracked here as plain (still manually-entered) string fields.
"""
from dataclasses import dataclass, field


@dataclass
class DiskChoice:
    device: str = ""                # e.g. /dev/vda — used in "simple" mode
    mode: str = "simple"             # "simple" | "advanced" | "manual"
    filesystem: str = "ext4"         # "ext4" | "btrfs" — only used in "simple" mode
    boot_size_gb: int = 4            # CachyOS + several Limine generations
                                      # quickly fill a 512M /boot — 4G recommended, 2G minimum
    enable_swap: bool = False        # off by default: zram already covers this role
    swap_size_gb: int = 8            # only used if enable_swap
    advanced_disko_path: str = ""    # path to a custom disko.nix if mode == advanced
    # mode == "manual": partitions the user made themselves in GParted,
    # mapped to mountpoints. e.g. {"/dev/vda1": "/boot", "/dev/vda2": "swap", "/dev/vda3": "/"}
    manual_partitions: dict = field(default_factory=dict)


@dataclass
class InstallState:
    username: str = "roudine"
    password: str = ""  # plaintext, in-memory only — only the hash is ever written to disk

    disk: DiskChoice = field(default_factory=DiskChoice)

    # ── Hardware ──────────────────────────────────────────────────────────
    gpu: str = "amd"                 # amd | amd-legacy | nvidia | intel
    nvidia_laptop: bool = False
    undervolt_enable: bool = False   # roudix.undervolt.only-amd.enable — AMD/AMD-legacy only (lact)
    cpu: str = "amd"                 # amd | intel
    kernel: str = "cachyos-latest-v3"        # hardware.myKernel (xddxdd) — used when gpu != "nvidia"
    kernel_chaotic: str = "cachyos"          # hardware.myKernelChaotic (Chaotic-Nyx) — used when gpu == "nvidia"
                                              # (ships nvidia_cachyos precompiled, no local module rebuild).
                                              # NOTE: local.nix.example currently only has a hardware.myKernel
                                              # line — the myKernelChaotic key exists in the module system and
                                              # is actively sed-patched by roudix-installer.sh, but has no
                                              # placeholder line in this particular example file to substitute
                                              # into. Worth checking upstream / adding the line back.

    # ── Browser ───────────────────────────────────────────────────────────
    browser: str = "brave"           # none | brave(-beta/-nightly/-origin-*) | helium | vivaldi
                                      # | firefox | librewolf | google-chrome | microsoft-edge
                                      # | ungoogled-chromium | chromium
    zen_browser: bool = False
    zen_variant: str = "twilight"    # roudix.zen.variant — twilight | beta
    zen_sine_enable: bool = False    # roudix.zen.sine.enable
    zen_mods: list = field(default_factory=list)       # roudix.zen.mods
    zen_sine_mods: list = field(default_factory=list)  # roudix.zen.sine.mods

    # ── Desktop ───────────────────────────────────────────────────────────
    desktop: str = "niri"            # niri | gnome | kde | hyprland | mangowc
    desktop_shell: str = "noctalia"  # noctalia | dms | caelestia (only for niri/hyprland)
    default_shell: str = "fish"      # fish | bash
    editor: str = "zed"              # roudix.editor — vscode | zed | neovim | none
    desktop_integration: str = "gnome"  # roudix.desktopIntegration — gnome | kde
                                         # only meaningful for niri/hyprland/mangowc
                                         # (gnome/kde manage their own keyring/portal)

    # ── System behaviour ─────────────────────────────────────────────────
    vm_guest: bool = False
    gaming: bool = True
    gaming_apps_lutris: bool = True         # roudix.gaming.apps.lutris.enable
    gaming_apps_heroic: bool = True         # roudix.gaming.apps.heroic.enable
    gaming_apps_faugus: bool = True         # roudix.gaming.apps.faugus.enable
    gaming_apps_prismlauncher: bool = True  # roudix.gaming.apps.prismlauncher.enable
    gaming_apps_modrinth: bool = False      # roudix.gaming.apps.modrinth.enable — alt. to Prism, off by default
    gaming_apps_vintagestory: bool = True   # roudix.gaming.apps.vintagestory.enable
    gaming_apps_mangohud: bool = True       # roudix.gaming.apps.mangohud.enable
    timezone: str = "Europe/Brussels"
    locale: str = "fr_BE.UTF-8"
    keymap: str = "be-latin1"         # console.keyMap — TTY only, before the graphical session
    keyboard_layout: str = "us"       # roudix.keyboardLayout — XKB layout for the graphical
                                       # (Wayland) session: niri/hyprland/mangowc/umbriel.
                                       # Distinct from `keymap` above (console/TTY-only).
                                       # No effect on gnome/kde.
    keyboard_variant: str = "intl"    # roudix.keyboardVariant — XKB variant ("", "intl",
                                       # "nodeadkeys", "bepo", "dvorak", "colemak"...)

    # ── RGB ───────────────────────────────────────────────────────────────
    rgb: str = "none"                # openlinkhub | openrgb | none
    memory_rgb_enable: bool = False
    memory_type: str = "ddr5"        # ddr5 | ddr4
    memory_smbus: str = ""           # roudix.memory.smBus — find via: i2cdetect -l
    memory_sku: str = ""             # roudix.memory.sku — find via: sudo dmidecode -t memory | grep 'Part Number'

    # ── Extras ────────────────────────────────────────────────────────────
    gta_fix: bool = False
    flatpak: bool = False
    virtualization: bool = False
    autoupdate: bool = True
    autoupdate_interval: str = "1h"
    bootloader: str = "limine"       # limine | systemd-boot
    matrix_client: str = "none"      # none | element | cinny
    discord: str = "vencord"         # roudix.discord — vencord | vanilla | none
    telegram: str = "none"           # roudix.telegram — none | telegram | ayugram
    video_player: str = "vlc"        # roudix.videoPlayer — vlc | clapper | mpv | celluloid | none
    torrent_client: str = "none"     # roudix.torrentClient — none | qbittorrent | fragments | deluge
    waydroid_enable: bool = False

    # ── Optional common apps (roudix.apps.*, all true by default) ──────────
    app_gimp: bool = True
    app_inkscape: bool = True
    app_spotify: bool = True         # Spotify + Spicetify (Comfy theme)
    app_songrec: bool = True
    app_easyeffects: bool = True     # + rnnoise-plugin

    # ── Spicetify (only meaningful if app_spotify) ──────────────────────────
    spicetify_theme: str = "colorful"        # roudix.spicetify.theme — colorful | comfy
    spicetify_color_scheme: str = ""         # roudix.spicetify.colorScheme — "" = theme default (null)
    spicetify_adblock: bool = True
    spicetify_hide_podcasts: bool = True
    spicetify_marketplace: bool = True

    terminal: str = "ghostty"        # ghostty | kitty | alacritty | foot | wezterm
    file_manager: str = "nautilus"   # roudix.fileManager — dolphin | thunar | nautilus | nemo
    ananicy_enable: bool = False     # roudix.gaming.ananicy.enable — opt-in, only meaningful if gaming.enable
    mesa_use_git: bool = False       # roudix.mesa.useGit — false = mesa stable

    # ── Content creation ─────────────────────────────────────────────────
    content_creation_enable: bool = True   # roudix.contentCreation.enable
    obs_enable: bool = True                # roudix.contentCreation.obs.enable
    # roudix.contentCreation.obs.plugins.<id>.enable — one boolean per plugin.
    # Aitum Multistream replaces obs-multi-rtmp (multistreaming plugin
    # maintained by the Aitum team, independent encoders/bitrate per platform).
    obs_plugin_vkcapture: bool = True
    obs_plugin_pipewire_audio_capture: bool = True
    obs_plugin_background_removal: bool = False
    obs_plugin_move_transition: bool = False
    obs_plugin_aitum_multistream: bool = False
    obs_plugin_gstreamer: bool = False
    obs_plugin_composite_blur: bool = False
    obs_plugin_advanced_scene_switcher: bool = False
    obs_plugin_input_overlay: bool = False
    obs_plugin_waveform: bool = False
    video_editor: str = "kdenlive"         # roudix.contentCreation.videoEditor —
                                            # kdenlive | davinci-resolve | davinci-resolve-studio | shotcut | none
    virtual_camera_enable: bool = True     # roudix.contentCreation.virtualCamera.enable
    chatterino_enable: bool = False        # roudix.contentCreation.streaming.chatterino.enable
