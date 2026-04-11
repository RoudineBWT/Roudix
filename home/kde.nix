{ config, lib, pkgs, roudixBranding, ... }:
let
  isKde = config.roudix.desktop.type == "kde";

  wallpaperDark = "/run/current-system/sw/share/wallpapers/RoudixDark/contents/images/3840x2160.png";
in
lib.mkIf isKde {
  services.displayManager.defaultSession = "plasma";
  services.desktopManager.plasma6.enable = true;

  # ── Plasma Login Manager ──────────────────────────────────────────────────
  services.displayManager.plasma-login-manager = {
    enable = true;
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

  # ── KDE Connect ───────────────────────────────────────────────────────────
  programs.kdeconnect.enable = true;
  documentation.nixos.enable = false;

  # ── Excluded packages ─────────────────────────────────────────────────────
  environment.plasma6.excludePackages = with pkgs; [
    kdePackages.discover
  ];

  # ── System packages ───────────────────────────────────────────────────────
  # lib.hiPrio sur roudix-branding pour que start-here-kde écrase Papirus
  environment.systemPackages = with pkgs; [
    (lib.hiPrio roudixBranding)
    kdePackages.partitionmanager
    kdePackages.kpmcore
    kdePackages.kcalc
    kdePackages.qtwebengine
    papirus-icon-theme
    vlc
    digikam
  ];
}
