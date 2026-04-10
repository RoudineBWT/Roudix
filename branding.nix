{ pkgs, lib, config, ... }:
let
  roudix-branding = pkgs.callPackage ./pkgs/roudix-branding {};
in

{
  environment.systemPackages = with pkgs; [
    roudix-branding
  ];

  environment.pathsToLink = [ "/share/icons" ];

  programs.dconf.profiles.gdm.databases = [{
    settings = {
      "org/gnome/login-screen" = {
        logo = "/run/current-system/sw/share/icons/hicolor/256x256/apps/roudix-logo.png";
      };
    };
  }];
}
