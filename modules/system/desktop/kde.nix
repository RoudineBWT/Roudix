{ config, lib, pkgs, roudixBranding, ... }:
let
  isKde = config.roudix.desktop.type == "kde";

  wallpaperDark = "${roudixBranding}/share/wallpapers/RoudixDark/contents/images/3840x2160.png";
in
lib.mkIf isKde {
  services.displayManager.defaultSession = "plasma";
  services.desktopManager.plasma6.enable = true;

  # ── Plasma Login Manager ──────────────────────────────────────────────────
  services.displayManager.plasma-login-manager = {
    enable = true;
  };

  # ── Plasma Login Manager wallpaper ────────────────────────────────────────
  # The KCM reads the wallpaper from /var/lib/plasmalogin/wallpapers/
  # and references it via /etc/plasmalogin.conf with a file:// prefix
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

  # ── Polkit agent ──────────────────────────────────────────────────────────
  # PLM (Plasma Login Manager) doesn't always trigger the autostart that
  # normally launches polkit-kde-authentication-agent-1 (unlike SDDM).
  # Forced via a systemd user service tied to the graphical session.
  systemd.user.services.polkit-kde-agent = {
    description = "PolicyKit KDE Authentication Agent";
    wantedBy = [ "graphical-session.target" ];
    partOf = [ "graphical-session.target" ];
    serviceConfig = {
      ExecStart = "${pkgs.kdePackages.polkit-kde-agent-1}/libexec/polkit-kde-authentication-agent-1";
      Restart = "on-failure";
    };
  };

  # ── Excluded packages ─────────────────────────────────────────────────────
  environment.plasma6.excludePackages = with pkgs; [
    kdePackages.discover
  ];

  # ── System packages ───────────────────────────────────────────────────────
  # lib.hiPrio on roudix-branding so start-here-kde overrides Papirus
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
