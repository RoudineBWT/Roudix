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

    # Sans ça, même avec roudixBranding dans systemPackages (fait par
    # gnome.nix), rien de son share/ n'est symlinké dans
    # /run/current-system/sw/ — logo GDM et fond d'écran resteraient
    # introuvables au runtime. Repris de ton vrai branding.nix racine.
    environment.pathsToLink = [
      "/share/icons" "/share/backgrounds" "/share/wallpapers" "/share/gnome-background-properties"
    ];

    environment.etc."roudix/branding".source = roudixBranding;

    # Fond d'écran "Roudix Cosmos". Attention au nom de fichier réel généré
    # par pkgs/roudix-branding/default.nix : c'est ".svg.png" (double
    # extension, coquille dans le script de build), pas juste ".png" comme
    # les autres wallpapers du même fichier.
    #
    # IMPORTANT : ceci NE DOIT PAS être un environment.etc."dconf/db/..."
    # manuel. Dès que programs.dconf.profiles.* est utilisé (cf. profil
    # "gdm" plus bas), le module nixpkgs programs/dconf.nix prend le
    # contrôle de *tout* /etc/dconf via un seul environment.etc.dconf.source
    # (symlinkJoin en lecture seule dans le store). Un environment.etc
    # séparé qui essaie d'écrire un fichier sous ce même sous-arbre fait
    # planer le builder etc.drv avec un "mkdir: Permission denied" (c'est
    # l'erreur du run CI Roudix-Installer-de). On passe donc par un profil
    # "user" au lieu d'un fichier etc à la main, pour que tout transite par
    # le même mécanisme géré.
    programs.dconf.profiles.user.databases = [{
      settings = {
        "org/gnome/desktop/background" = {
          picture-uri = "file:///run/current-system/sw/share/backgrounds/roudix/roudix_wallpaper_cosmos.svg.png";
          picture-uri-dark = "file:///run/current-system/sw/share/backgrounds/roudix/roudix_wallpaper_cosmos.svg.png";
          picture-options = "zoom";
        };
      };
    }];
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
