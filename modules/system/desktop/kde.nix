{ config, lib, pkgs, ... }:
let
  isKde = config.roudix.desktop.type == "kde";
in
lib.mkIf isKde {
  # ── Display Manager ────────────────────────────────────────────────────────
  services.displayManager.sddm = {
    enable         = true;
    wayland.enable = true;
  };
  services.displayManager.defaultSession = "plasma";
  services.desktopManager.plasma6.enable = true;

  # ── Hardware ───────────────────────────────────────────────────────────────
  hardware.bluetooth.enable = true;

  # ── Portals ────────────────────────────────────────────────────────────────
  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [ kdePackages.xdg-desktop-portal-kde ];
    xdgOpenUsePortal = true;
    config.common.default = "kde";
  };

  # ── Thème sombre Breeze par défaut (système) ──────────────────────────────
  # Sert de fallback système uniquement.
  # Le thème, wallpaper et icône Kickoff sont gérés de façon déclarative
  # par plasma-manager dans home/kde.nix.
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

  # ── Excluded packages ──────────────────────────────────────────────────────
  environment.plasma6.excludePackages = with pkgs; [
    kdePackages.discover
  ];

  # ── System packages ────────────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    kdePackages.partitionmanager
    kdePackages.kpmcore
    kdePackages.kcalc
    kdePackages.qtwebengine
    vlc
    digikam
  ];
}
