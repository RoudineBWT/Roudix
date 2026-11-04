"""
Turns a DiskChoice into a disko.nix, or returns the user-supplied one
in advanced mode. This replaces KPMCore entirely: disko takes a plain
Nix description of the layout and does parted/mkfs/mount itself when
`disko --mode disko` runs.

Two presets in "simple" mode:
  - ext4: straightforward single-partition root, no subvolumes.
  - btrfs: @ / @home / @nix / @log subvolumes, zstd compression,
    noatime. No swapfile handling — see swap note below.

/boot defaults to 4G (min. 2G): CachyOS kernels are large, and Limine
keeps multiple generations bootable, so the classic 512M ESP fills up
fast. No swap partition by default — zram already covers that role;
enable_swap exists for people who want one anyway (e.g. hibernation).
"""
from pathlib import Path

from roudix_installer.state import DiskChoice


def _bios_boot_block() -> str:
    # 1 MiB BIOS boot partition (EF02): where Limine's stage 1.5 lives on a
    # GPT disk. Must come first so GPT-on-BIOS boots on picky firmware.
    return """\
            boot = {
              size = "1M";
              type = "EF02";
              priority = 1;
            };
"""


def _esp_block(boot_size_gb: int, bios: bool = False) -> str:
    # In BIOS mode this is still the /boot partition (FAT, readable by
    # Limine), it just is not a real ESP, so no EF00 type.
    ptype = "8300" if bios else "EF00"
    bios_part = _bios_boot_block() if bios else ""
    return f"""\
{bios_part}            ESP = {{
              size = "{boot_size_gb}G";
              type = "{ptype}";
              content = {{
                type = "filesystem";
                format = "vfat";
                mountpoint = "/boot";
                mountOptions = [ "umask=0077" ];
              }};
            }};"""


def _swap_block(swap_size_gb: int) -> str:
    return f"""\
            swap = {{
              size = "{swap_size_gb}G";
              content = {{
                type = "swap";
                randomEncryption = true;
              }};
            }};"""


def _ext4_template(disk: DiskChoice) -> str:
    swap = f"\n{_swap_block(disk.swap_size_gb)}" if disk.enable_swap else ""
    return f"""\
{{
  disko.devices = {{
    disk = {{
      main = {{
        type = "disk";
        device = "{disk.device}";
        content = {{
          type = "gpt";
          partitions = {{
{_esp_block(disk.boot_size_gb, disk.bios)}{swap}
            root = {{
              size = "100%";
              content = {{
                type = "filesystem";
                format = "ext4";
                mountpoint = "/";
              }};
            }};
          }};
        }};
      }};
    }};
  }};
}}
"""


def _btrfs_template(disk: DiskChoice) -> str:
    # No swapfile/swap subvolume here on purpose: a proper btrfs swapfile
    # needs a nodatacow subvolume of its own and disko's story for that is
    # fiddly. Since swap is opt-in and zram is the recommended default,
    # enable_swap on btrfs still gets a plain swap *partition* alongside —
    # simpler and avoids the nodatacow gotcha entirely.
    swap = f"\n{_swap_block(disk.swap_size_gb)}" if disk.enable_swap else ""
    return f"""\
{{
  disko.devices = {{
    disk = {{
      main = {{
        type = "disk";
        device = "{disk.device}";
        content = {{
          type = "gpt";
          partitions = {{
{_esp_block(disk.boot_size_gb, disk.bios)}{swap}
            root = {{
              size = "100%";
              content = {{
                type = "btrfs";
                extraArgs = [ "-f" ];
                subvolumes = {{
                  "@" = {{
                    mountpoint = "/";
                    mountOptions = [ "compress=zstd:1" "noatime" ];
                  }};
                  "@home" = {{
                    mountpoint = "/home";
                    mountOptions = [ "compress=zstd:1" "noatime" ];
                  }};
                  "@nix" = {{
                    mountpoint = "/nix";
                    mountOptions = [ "compress=zstd:1" "noatime" ];
                  }};
                  "@log" = {{
                    mountpoint = "/var/log";
                    mountOptions = [ "compress=zstd:1" "noatime" ];
                  }};
                }};
              }};
            }};
          }};
        }};
      }};
    }};
  }};
}}
"""


def generate(disk: DiskChoice) -> str:
    """Returns the disko.nix *contents* as a string, ready to write to disk."""
    if disk.mode == "advanced":
        return Path(disk.advanced_disko_path).read_text()

    if not disk.device:
        raise ValueError("Aucun disque sélectionné")

    if disk.filesystem == "btrfs":
        return _btrfs_template(disk)
    return _ext4_template(disk)
