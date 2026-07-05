{ pkgs, lib, roudixBranding, ... }:

{
  # Ton vrai module GNOME (modules/system/desktop/gnome.nix), embarqué via
  # roudix-cfg — active GDM, xdg-portal, gnome-tweaks/extension-manager,
  # adw-gtk3, exclusion de paquets, exactement comme sur une install normale.
  imports = [ ./roudix-cfg/modules/system/desktop/gnome.nix ];

  # Dupliqué depuis modules/system/desktop/default.nix — on n'importe pas
  # ce fichier tel quel pour éviter de tirer niri.nix/hyprland.nix/kde.nix/
  # mangowc.nix, qui référencent probablement des inputs de flake (niri,
  # hyprland...) qu'on n'a pas dans le flake de l'ISO.
  options.roudix.desktop.type = lib.mkOption {
    type = lib.types.enum [ "niri" "gnome" "kde" "hyprland" "mangowc" ];
    default = "gnome";
  };

  # Un module avec un "options" au niveau racine doit mettre tout le reste
  # sous "config" explicite — sinon Nix refuse de mélanger les deux.
  config = {
    roudix.desktop.type = "gnome";

    environment.etc."roudix/branding".source = roudixBranding;

    # Fond d'écran "Roudix Cosmos" (celui du screenshot violet/trou noir),
    # chemin confirmé dans pkgs/roudix-branding/default.nix.
    environment.etc."dconf/db/local.d/00-roudix-wallpaper".text = ''
      [org/gnome/desktop/background]
      picture-uri='file:///run/current-system/sw/share/backgrounds/roudix/roudix_wallpaper_cosmos.png'
      picture-uri-dark='file:///run/current-system/sw/share/backgrounds/roudix/roudix_wallpaper_cosmos.png'
      picture-options='zoom'
    '';
    programs.dconf.enable = true;

    # Logo GDM — même mécanisme que ton branding.nix racine.
    programs.dconf.profiles.gdm.databases = [{
      settings = {
        "org/gnome/login-screen" = {
          logo = "/run/current-system/sw/share/icons/hicolor/256x256/apps/roudix-logo.png";
        };
      };
    }];
  };
}
