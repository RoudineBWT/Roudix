{ config, lib, osConfig, roudixConfig, ... }:

with lib;

let
  cfg = config.roudix.configApp;
in
{
  options.roudix.configApp.enable = mkOption {
    type = types.bool;
    # The app configures the compositor selected by roudix.desktop.type and only
    # knows the ones listed here; on GNOME / KDE / Cinnamon it would just say
    # "non disponible", so it isn't installed there by default.
    default = builtins.elem osConfig.roudix.desktop.type [ "umbriel" "niri" "mangowc" ];
    description = ''
      Installe Roudix Config (GUI `roudix-config`, version terminal
      `roudix-config-tui`) : une interface pour ajouter des règles de fenêtres,
      régler les écrans et les raccourcis de Umbriel, Niri ou MangoWC sans écrire
      de Nix. Elle écrit dans un bloc balisé de modules/home/<compositeur>-custom.nix,
      dans le dépôt (par défaut ~/.config/roudix, ou ROUDIX_DIR).
    '';
  };

  config = mkIf cfg.enable {
    home.packages = [ roudixConfig ];
  };
}
