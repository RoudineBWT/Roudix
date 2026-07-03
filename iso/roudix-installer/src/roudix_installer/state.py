"""
Single source of truth for everything the wizard collects.
Mirrors the variables your roudix-installer.sh script already
prompts for — nothing new invented, just given a GUI face.
"""
from dataclasses import dataclass, field


@dataclass
class DiskChoice:
    device: str = ""              # e.g. /dev/nvme0n1
    mode: str = "simple"          # "simple" | "advanced"
    swap_size_gb: int = 8
    advanced_disko_path: str = "" # path to a custom disko.nix if mode == advanced


@dataclass
class InstallState:
    hostname: str = "roudix"
    username: str = "roudine"
    password_hash: str = ""

    disk: DiskChoice = field(default_factory=DiskChoice)

    desktop: str = "niri"          # niri | hyprland | gnome | plasma
    shell: str = "noctalia"        # noctalia | dms | caelestia | none
    kernel: str = "cachyos-auto"   # matches your microarch auto-detect option
    bootloader: str = "limine"     # limine | systemd-boot
    browser: str = "brave"

    matrix_client: str = "none"    # element | cinny | none
    waydroid_enable: bool = False

    def as_nix_options(self) -> dict:
        """
        Maps GUI selections directly onto roudix.* module options,
        the same ones roudix-installer.sh already writes today.
        """
        return {
            "networking.hostName": self.hostname,
            "roudix.desktop": self.desktop,
            "roudix.shell": self.shell,
            "roudix.kernel": self.kernel,
            "roudix.boot.bootloader": self.bootloader,
            "roudix.browser": self.browser,
            "roudix.matrixClient": self.matrix_client,
            "roudix.waydroid.enable": self.waydroid_enable,
        }
