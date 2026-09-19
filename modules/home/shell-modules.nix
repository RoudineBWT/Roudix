{ inputs, ... }:
{
  # Imported only once here to avoid double declaration conflicts
  # when both niri.nix and hyprland.nix are loaded by home manager.
  # noctalia.homeModules.default removed: home-manager now provides
  # programs.noctalia nativement (modules/programs/noctalia.nix) — importer
  # having both caused an "option already declared" conflict.
  imports = [
    inputs.caelestia-shell.homeManagerModules.default
    inputs.dms.homeModules.dank-material-shell
  ];
}
