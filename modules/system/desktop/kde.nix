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

  # ── Plasma Login Manager wallpaper ────────────────────────────────────────
  # Le KCM lit le wallpaper depuis /var/lib/plasmalogin/wallpapers/
  # et le référence via /etc/plasmalogin.conf avec le préfixe file://
  environment.etc."plasmalogin.conf".text = ''
    [Greeter][Wallpaper][org.kde.image][General]
    Image=file:///var/lib/plasmalogin/wallpapers/RoudixDark
  '';

  system.activationScripts.plasmaLoginWallpaper = {
    deps = [ "users" "groups" ];
    text = ''
      install -d -o plasmalogin -g plasmalogin /var/lib/plasmalogin/wallpapers/RoudixDark/contents/images
      cp ${wallpaperDark} /var/lib/plasmalogin/wallpapers/RoudixDark/contents/images/3840x2160.png
      cp ${roudixBranding}/share/wallpapers/RoudixDark/metadata.json /var/lib/plasmalogin/wallpapers/RoudixDark/metadata.json
      chown -R plasmalogin:plasmalogin /var/lib/plasmalogin/wallpapers/
    '';
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
    capitaine-cursors
    vlc
    digikam
  ];
}
