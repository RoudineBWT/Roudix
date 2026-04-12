{ inputs, ... }:
{
  # Imported only once here to avoid double declaration conflicts
  # when both niri.nix and hyprland.nix are loaded by home manager.
  imports = [
    inputs.noctalia.homeModules.default
    inputs.caelestia-shell.homeManagerModules.default
    inputs.dms.homeModules.dank-material-shell
  ];
}
