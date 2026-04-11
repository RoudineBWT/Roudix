{ pkgs, lib, config, ... }:
let
  roudix-branding = pkgs.callPackage ./pkgs/roudix-branding {};
in
{
  environment.systemPackages = with pkgs; [
    roudix-branding
  ];

  environment.pathsToLink = [ "/share/icons" "/share/backgrounds" "/share/wallpapers" "/share/gnome-background-properties" ];

  # Logo GDM
  programs.dconf.profiles.gdm.databases = [{
    settings = {
      "org/gnome/login-screen" = {
        logo = "/run/current-system/sw/share/icons/hicolor/256x256/apps/roudix-logo.png";
      };
    };
  }];

  # Wallpaper par défaut GNOME
  programs.dconf.profiles.user.databases = [{
    settings = {
      "org/gnome/desktop/background" = {
        picture-uri       = "file:///run/current-system/sw/share/backgrounds/roudix/roudix-light.svg";
        picture-uri-dark  = "file:///run/current-system/sw/share/backgrounds/roudix/roudix-dark.svg";
        picture-options   = "zoom";
      };
      "org/gnome/desktop/screensaver" = {
        picture-uri = "file:///run/current-system/sw/share/backgrounds/roudix/roudix-dark.svg";
      };
    };
  }];

  # Le branding KDE (thème sombre + wallpaper + icône Kickoff) est géré
  # de façon déclarative par plasma-manager dans home/kde.nix.
  # Le fallback thème système reste dans modules/system/kde.nix.
}
