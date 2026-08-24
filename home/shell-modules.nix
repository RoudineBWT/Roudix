{ inputs, ... }:
{
  # Imported only once here to avoid double declaration conflicts
  # when both niri.nix and hyprland.nix are loaded by home manager.
  # noctalia.homeModules.default retiré : home-manager fournit désormais
  # programs.noctalia nativement (modules/programs/noctalia.nix) — importer
  # les deux provoquait un conflit "option already declared".
  imports = [
    inputs.caelestia-shell.homeManagerModules.default
    inputs.dms.homeModules.dank-material-shell
  ];
}
