{ config, lib, pkgs, ... }:
let
  isKde = config.roudix.desktop.type == "kde";

  wallpaperDark  = "/run/current-system/sw/share/wallpapers/RoudixDark/contents/images/roudix-dark.svg";
  wallpaperLight = "/run/current-system/sw/share/wallpapers/RoudixLight/contents/images/roudix-light.svg";

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

  # ── Roudix KDE branding — defaults pour fresh install ─────────────────────
  #
  # Ces fichiers sont lus par KDE comme valeurs système par défaut.
  # Ils s'appliquent uniquement si l'utilisateur n'a pas encore de config
  # dans ~/.config/ (= fresh install).
  # Un utilisateur existant qui change son thème/wallpaper depuis les
  # paramètres KDE ne sera jamais écrasé.

  # Thème sombre Breeze par défaut
  environment.etc."xdg/kdeglobals".text = ''
    [KDE]
    ColorScheme=BreezeDark
    LookAndFeelPackage=org.kde.breezedark.desktop

    [General]
    ColorScheme=BreezeDark

    [Icons]
    Theme=breeze-dark
  '';

  # Icône Kickoff + wallpaper par défaut
  environment.etc."xdg/plasma-org.kde.plasma.desktop-appletsrc".text = ''
    [Containments][2][Applets][3][Configuration][General]
    icon=roudix-logo

    [Containments][2][Wallpaper][org.kde.image][General]
    Image=${wallpaperDark}
    SlidePaths=/run/current-system/sw/share/wallpapers
  '';

  # Switcher dynamique jour/nuit (optionnel, respecte le choix utilisateur)
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
