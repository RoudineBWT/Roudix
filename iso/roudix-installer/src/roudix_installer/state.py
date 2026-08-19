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
    zen_sine_enable: bool = False    # roudix.zen.sine.enable
    zen_mods: list = field(default_factory=list)       # roudix.zen.mods
    zen_sine_mods: list = field(default_factory=list)  # roudix.zen.sine.mods

    # ── Desktop ───────────────────────────────────────────────────────────
    desktop: str = "niri"            # niri | gnome | kde | hyprland | mangowc
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
    waydroid_enable: bool = False
    terminal: str = "ghostty"        # ghostty | kitty | alacritty | foot | wezterm
    file_manager: str = "nautilus"   # roudix.fileManager — dolphin | thunar | nautilus | nemo
    ananicy_enable: bool = False     # roudix.gaming.ananicy.enable — opt-in, only meaningful if gaming.enable
    mesa_use_git: bool = False       # roudix.mesa.useGit — false = mesa stable
