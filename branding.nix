{ pkgs, lib, ... }:
{
  environment.systemPackages = [
    (pkgs.callPackage ./pkgs/roudix-branding/default.nix {})
  ];

  environment.pathsToLink = [ "/share/icons" ];

  programs.dconf.profiles.gdm.databases = [{
    settings = {
      "org/gnome/login-screen" = {
        logo = "/run/current-system/sw/share/icons/hicolor/scalable/apps/roudix-logo.svg";
      };
    };
  }];
}
