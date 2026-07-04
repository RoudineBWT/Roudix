{ pkgs, lib, roudixBranding, ... }:

# Même logique que le branding.nix racine du repo — juste dupliqué ici
# plutôt qu'importé directement, parce que le module principal (celui
# à la racine, "./branding.nix" dans le flake.nix principal) attend un
# arbre NixOS différent (config utilisateur, home-manager...) que l'ISO
# n'a pas. Si les deux divergent avec le temps, penser à les resynchro.

{
  environment.systemPackages = with pkgs; [
    (lib.hiPrio roudixBranding)
  ];

  environment.pathsToLink = [
    "/share/icons" "/share/backgrounds" "/share/wallpapers" "/share/gnome-background-properties"
  ];

  # Logo GDM — identique au mécanisme de la config principale
  programs.dconf.profiles.gdm.databases = [{
    settings = {
      "org/gnome/login-screen" = {
        logo = "/run/current-system/sw/share/icons/hicolor/256x256/apps/roudix-logo.png";
      };
    };
  }];
}
