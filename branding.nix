{ pkgs, lib, config, roudixBranding. ... }:
let
  roudix-branding = pkgs.callPackage ./pkgs/roudix-branding {};
in
{
  environment.systemPackages = with pkgs; [
    (lib.hiPrio roudixBranding)
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
}
