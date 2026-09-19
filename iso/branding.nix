{ pkgs, lib, roudixBranding, ... }:

{
  # The real GNOME module (modules/system/desktop/gnome.nix), pulled in via
  # roudix-cfg — enables GDM, xdg-portal, gnome-tweaks/extension-manager,
  # adw-gtk3, package exclusions, exactly like on a normal install.
  imports = [ ./roudix-cfg/modules/system/desktop/gnome.nix ];

  # Duplicated from modules/system/desktop/default.nix instead of importing
  # it directly, to avoid pulling in niri.nix/hyprland.nix/kde.nix/mangowc.nix,
  # which reference flake inputs the ISO's flake doesn't have.
  options.roudix.desktop.type = lib.mkOption {
    type = lib.types.enum [ "niri" "gnome" "kde" "hyprland" "mangowc" ];
    default = "gnome";
  };

  # A module with an "options" at the root level must put everything else
  # under an explicit "config" — Nix refuses to mix the two.
  config = {
    roudix.desktop.type = "gnome";

    # Without this, roudixBranding's share/ files (added to systemPackages
    # by gnome.nix) never get symlinked into /run/current-system/sw/ —
    # the GDM logo and wallpaper stay unfindable at runtime.
    environment.pathsToLink = [
      "/share/icons" "/share/backgrounds" "/share/wallpapers" "/share/gnome-background-properties"
    ];

    environment.etc."roudix/branding".source = roudixBranding;

    # "Roudix Cosmos" wallpaper. The generated filename from
    # pkgs/roudix-branding/default.nix is ".svg.png" (double extension,
    # a build-script typo), not plain ".png" like the other wallpapers.
    #
    # IMPORTANT: this must go through programs.dconf.profiles.user, never a
    # manual environment.etc."dconf/db/...". As soon as programs.dconf.
    # profiles.* is used anywhere (see the "gdm" profile below), the
    # nixpkgs dconf module owns all of /etc/dconf as one read-only
    # symlinkJoin, and a manual environment.etc under that path crashes
    # the build with "mkdir: Permission denied".
    programs.dconf.profiles.user.databases = [{
      settings = {
        "org/gnome/desktop/background" = {
          picture-uri = "file:///run/current-system/sw/share/backgrounds/roudix/roudix-dark.png";
          picture-uri-dark = "file:///run/current-system/sw/share/backgrounds/roudix/roudix-dark.png";
          picture-options = "zoom";
        };
      };
    }];
    programs.dconf.enable = true;

    # GDM logo — same mechanism as the root branding.nix.
    programs.dconf.profiles.gdm.databases = [{
      settings = {
        "org/gnome/login-screen" = {
          logo = "/run/current-system/sw/share/icons/hicolor/256x256/apps/roudix-logo.png";
        };
      };
    }];
  };
}
