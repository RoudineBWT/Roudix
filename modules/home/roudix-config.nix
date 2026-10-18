{ config, lib, osConfig, roudixConfig, ... }:

with lib;

let
  cfg = config.roudix.configApp;
in
{
  options.roudix.configApp.enable = mkOption {
    type = types.bool;
    # The app only knows how to configure the compositors it supports (today:
    # Umbriel); on anything else it would just say "non disponible", so it is
    # not installed by default there. Add more types here as they get support.
    default = osConfig.roudix.desktop.type == "umbriel";
    description = ''
      Installe Roudix Config (GUI `roudix-config`, version terminal
      `roudix-config-tui`) : une interface pour ajouter des règles de fenêtres,
      régler écrans/workspaces et raccourcis sans écrire de Nix. Elle écrit
      dans un bloc balisé de modules/home/<compositeur>-custom.nix, dans le
      dépôt (par défaut ~/.config/roudix, ou ROUDIX_DIR).
    '';
  };

  config = mkIf cfg.enable {
    home.packages = [ roudixConfig ];
  };
}
