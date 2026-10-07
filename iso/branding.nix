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
    type = lib.types.enum [ "niri" "gnome" "kde" "cinnamon" "hyprland" "mangowc" "umbriel" ];
    default = "gnome";
  };

  # Minimal stand-ins for options gnome.nix reads (favorite apps in the
  # dash) but that are declared in modules/system/apps/*, which the ISO
  # doesn't import. Without them the ISO fails to evaluate with
  # "attribute 'browsers' missing". Defaults only: keep the types aligned
  # with the real declarations (apps/browser/browser.nix, apps/utilities/
  # terminal.nix); the live session doesn't use the values for anything else.
  options.roudix.browsers = lib.mkOption {
    type = lib.types.listOf lib.types.str;
    default = [ ];
  };
  options.roudix.zen = {
    enable = lib.mkOption { type = lib.types.bool; default = false; };
    variant = lib.mkOption {
      type = lib.types.enum [ "beta" "twilight" ];
      default = "twilight";
    };
  };
  options.roudix.terminal = lib.mkOption {
    type = lib.types.str;
    default = "ghostty";
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
