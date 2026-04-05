{ lib, ... }:
{
  imports = [
    ./niri.nix
    ./gnome.nix
    ./kde.nix
  ];

  # ── Desktop environment option ───────────────────────────────────────────
  options.roudix.desktop.type = lib.mkOption {
    description = "Desktop environment selection. Use 'roudix-switch <de>' to change.";
    type = lib.types.enum [ "niri" "gnome" "kde" ];
    default = "niri";
  };
}
