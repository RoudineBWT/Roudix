"""
Single source of truth for everything the wizard collects.
Field names/values map 1:1 onto what roudix-installer.sh already
asks for and sed-writes into hosts/roudix/local.nix — same options,
same defaults, just fed by GUI state instead of `read -p`.

Deliberately NOT covered yet (same as the TODO list in the installer
README): EFI multi-boot NVRAM detection, btrfs subvolume auto-patch
of hardware-configuration.nix, and RAM RGB SMBus/SKU auto-detect.
These stay manual/skipped for now — flagged, not silently dropped.
"""
from dataclasses import dataclass, field


@dataclass
class DiskChoice:
    device: str = ""                # e.g. /dev/vda — used in "simple" mode
    mode: str = "simple"             # "simple" | "advanced" | "manual"
    filesystem: str = "ext4"         # "ext4" | "btrfs" — only used in "simple" mode
    boot_size_gb: int = 4            # CachyOS + plusieurs générations Limine remplissent
                                      # vite un /boot de 512M — 4G recommandé, 2G minimum
    enable_swap: bool = False        # off par défaut : zram couvre déjà ce rôle
    swap_size_gb: int = 8            # utilisé seulement si enable_swap
    advanced_disko_path: str = ""    # path to a custom disko.nix if mode == advanced
    # mode == "manual": partitions the user made themselves in GParted,
    # mapped to mountpoints. e.g. {"/dev/vda1": "/boot", "/dev/vda2": "swap", "/dev/vda3": "/"}
    manual_partitions: dict = field(default_factory=dict)


@dataclass
class InstallState:
    username: str = "roudine"

    disk: DiskChoice = field(default_factory=DiskChoice)

    # ── Hardware ──────────────────────────────────────────────────────────
    gpu: str = "amd"                 # amd | amd-legacy | nvidia | intel
    nvidia_laptop: bool = False
    cpu: str = "amd"                 # amd | intel
    kernel: str = "cachyos-latest-v3"

    # ── Browser ───────────────────────────────────────────────────────────
    browser: str = "brave"           # none | brave(-beta/-nightly/-origin-*) | helium | vivaldi
                                      # | firefox | librewolf | google-chrome | microsoft-edge
                                      # | ungoogled-chromium | chromium
    zen_browser: bool = False

    # ── Desktop ───────────────────────────────────────────────────────────
    desktop: str = "niri"            # niri | gnome | kde | hyprland
    desktop_shell: str = "noctalia"  # noctalia | dms | caelestia (only for niri/hyprland)
    default_shell: str = "fish"      # fish | bash

    # ── System behaviour ─────────────────────────────────────────────────
    vm_guest: bool = False
    gaming: bool = True
    timezone: str = "Europe/Brussels"
    locale: str = "fr_BE.UTF-8"
    keymap: str = "be-latin1"

    # ── RGB ───────────────────────────────────────────────────────────────
    rgb: str = "none"                # openlinkhub | openrgb | none
    memory_rgb_enable: bool = False
    memory_type: str = "ddr5"        # ddr5 | ddr4

    # ── Extras ────────────────────────────────────────────────────────────
    gta_fix: bool = False
    flatpak: bool = False
    virtualization: bool = False
    autoupdate: bool = True
    autoupdate_interval: str = "1h"
    bootloader: str = "limine"       # limine | systemd-boot
    matrix_client: str = "none"      # none | element | cinny
    waydroid_enable: bool = False
