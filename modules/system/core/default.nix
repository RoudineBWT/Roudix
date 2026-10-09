{ ... }:
{
  # Base system-wide settings too small to deserve their own folder each:
  # default shell, SSD/NVMe TRIM, the roudixSwitcher polkit policy, and the
  # CachyOS-Settings-style system tuning.
  imports = [
    ./shell.nix
    ./fstrim.nix
    ./environment.nix
    ./tuning.nix
  ];
}
