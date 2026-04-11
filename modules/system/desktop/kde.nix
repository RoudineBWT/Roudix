{ config, lib, pkgs, ... }:
let
  isKde = config.roudix.desktop.type == "kde";
  cfg   = config.roudix.kde;

  wallpaperDark = "/run/current-system/sw/share/wallpapers/RoudixDark/contents/images/3840x2160.png";
in
lib.mkIf isKde {
  # ── Option loginManager ────────────────────────────────────────────────────
  # Permet de basculer entre SDDM et Plasma Login Manager facilement.
  # PLM sera disponible dans nixpkgs unstable avec Plasma 6.6.
  # Pour passer à PLM quand il sera dispo :
  #   roudix.kde.loginManager = "plasma-login-manager";
  options.roudix.kde.loginManager = lib.mkOption {
    type    = lib.types.enum [ "sddm" "plasma-login-manager" ];
    default = "sddm";
    description = "Display manager à utiliser pour KDE.";
  };

  # ── Display Manager ────────────────────────────────────────────────────────
  config = {
    services.displayManager.defaultSession = "plasma";
    services.desktopManager.plasma6.enable = true;

    # SDDM (défaut)
    services.displayManager.sddm = lib.mkIf (cfg.loginManager == "sddm") {
      enable         = true;
      wayland.enable = true;

      # Wallpaper Roudix Dark sur l'écran de login
      settings.Theme.Background = wallpaperDark;
    };

    # Plasma Login Manager (futur remplacement de SDDM)
    # Décommenter quand PLM sera dans nixpkgs unstable (Plasma 6.6)
    # services.displayManager.plasma-login-manager = lib.mkIf (cfg.loginManager == "plasma-login-manager") {
    #   enable = true;
    # };

    # ── Hardware ─────────────────────────────────────────────────────────────
    hardware.bluetooth.enable = true;

    # ── Portals ───────────────────────────────────────────────────────────────
    xdg.portal = {
      enable = true;
      extraPortals = with pkgs; [ kdePackages.xdg-desktop-portal-kde ];
      xdgOpenUsePortal = true;
      config.common.default = "kde";
    };

    # ── Thème sombre Breeze par défaut (système) ──────────────────────────────
    # Sert de fallback système uniquement.
    # Le thème, wallpaper et icône Kickoff sont gérés par plasma-manager
    # dans home/kde.nix.
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

    # ── KDE Connect ──────────────────────────────────────────────────────────
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
      vlc
      digikam
    ];
  };
}
