{ config, lib, pkgs, inputs, roudixBranding, ... }:
let
  isGnome = config.roudix.desktop.type == "gnome";
  cfg = config.roudix.gnome;
in
{
  # ── User-facing options ────────────────────────────────────────────────
  options.roudix.gnome = {
    extraExtensions = lib.mkOption {
      type    = lib.types.listOf lib.types.package;
      default = [];
      description = "Additional GNOME extensions to install and enable.";
    };
    disabledExtensions = lib.mkOption {
      type    = lib.types.listOf lib.types.str;
      default = [];
      description = "UUIDs of default extensions to disable.";
    };
  };

  config = lib.mkIf isGnome {
    # ── Greeter & keyring ──────────────────────────────────────────────
    services.displayManager.gdm.enable = true;
    services.gnome.gnome-keyring.enable = true;
    security.pam.services.gdm.enableGnomeKeyring = true;
    services.desktopManager.gnome.enable = true;

    xdg.portal = {
      enable = true;
      extraPortals = with pkgs; [
        xdg-desktop-portal-gnome
        xdg-desktop-portal-gtk
      ];
      config.common.default = "gnome";
    };

    programs.nautilus-open-any-terminal = {
      enable = true;
      terminal = "ghostty";
    };

    environment.systemPackages = with pkgs; [
      (lib.hiPrio roudixBranding)
      gnome-tweaks
      gnome-extension-manager
      gtk3
      gsettings-desktop-schemas
      adw-gtk3
    ] ++ cfg.extraExtensions;

    environment.gnome.excludePackages = with pkgs; [
      tali iagno hitori atomix yelp geary xterm totem
      epiphany gnome-tour gnome-software gnome-contacts
      gnome-user-docs gnome-font-viewer gnome-music
      gnome-backgrounds
    ];
  };
}
