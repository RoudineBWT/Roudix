{ config, lib, pkgs, ... }:
let
  isKde = config.roudix.desktop.type == "kde";

  wallpaperDark = "/run/current-system/sw/share/wallpapers/RoudixDark/contents/images/3840x2160.png";
in
lib.mkIf isKde {
  services.displayManager.defaultSession = "plasma";
  services.desktopManager.plasma6.enable = true;

  # ── Plasma Login Manager ──────────────────────────────────────────────────
  services.displayManager.plasma-manager = {
    enable    = true;
    wallpaper = wallpaperDark;
  };

  # ── Hardware ──────────────────────────────────────────────────────────────
  hardware.bluetooth.enable = true;

  # ── Portals ───────────────────────────────────────────────────────────────
  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [ kdePackages.xdg-desktop-portal-kde ];
    xdgOpenUsePortal = true;
    config.common.default = "kde";
  };

  # ── Thème sombre Breeze par défaut (système) ──────────────────────────────
  environment.etc."xdg/kdeglobals".text = ''
    [KDE]
    ColorScheme=BreezeDark
    LookAndFeelPackage=org.kde.breezedark.desktop

    [General]
    ColorScheme=BreezeDark

    [Icons]
    Theme=breeze-dark
  '';

  environment.etc."xdg/plasmarc".text = ''
    [Theme]
    name=breeze-dark
  '';

  # ── KDE Connect ───────────────────────────────────────────────────────────
  programs.kdeconnect.enable = true;
  documentation.nixos.enable = false;

  # ── Excluded packages ─────────────────────────────────────────────────────
  environment.plasma6.excludePackages = with pkgs; [
    kdePackages.discover
  ];

  # ── System packages ───────────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    kdePackages.partitionmanager
    kdePackages.kpmcore
    kdePackages.kcalc
    kdePackages.qtwebengine
    papirus-icon-theme
    vlc
    digikam
  ];
}
