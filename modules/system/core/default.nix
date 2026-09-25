{ ... }:
{
  # Base system-wide settings too small to deserve their own folder each:
  # default shell, SSD/NVMe TRIM, and the roudixSwitcher polkit policy.
  imports = [
    ./shell.nix
    ./fstrim.nix
    ./environment.nix
  ];
}
