"""
Turns a DiskChoice into a disko.nix, or returns the user-supplied one
in advanced mode. This replaces KPMCore entirely: disko takes a plain
Nix description of the layout and does parted/mkfs/mount itself when
`disko-install` runs, which is exactly the kind of thing your
roudix-installer.sh already assumed would "just work" before Calamares
started fighting it.
"""
from pathlib import Path

from roudix_installer.state import DiskChoice

SIMPLE_TEMPLATE = """\
{{
  disko.devices = {{
    disk = {{
      main = {{
        type = "disk";
        device = "{device}";
        content = {{
          type = "gpt";
          partitions = {{
            ESP = {{
              size = "512M";
              type = "EF00";
              content = {{
                type = "filesystem";
                format = "vfat";
                mountpoint = "/boot";
                mountOptions = [ "umask=0077" ];
              }};
            }};
            swap = {{
              size = "{swap_size}G";
              content = {{
                type = "swap";
                randomEncryption = true;
              }};
            }};
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


def generate(disk: DiskChoice) -> str:
    """Returns the disko.nix *contents* as a string, ready to write to disk."""
    if disk.mode == "advanced":
        return Path(disk.advanced_disko_path).read_text()

    if not disk.device:
        raise ValueError("Aucun disque sélectionné")

    return SIMPLE_TEMPLATE.format(device=disk.device, swap_size=disk.swap_size_gb)
