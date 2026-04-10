{ config, lib, pkgs, ... }:
let
  isNiri = config.roudix.desktop.type == "niri";
in
lib.mkIf isNiri {
  programs.niri.enable = true;

  programs.uwsm = {
    enable = true;
    waylandCompositors.niri = {
      prettyName = "Niri";
      comment     = "Niri scrollable tiling compositor";
      binPath     = "/run/current-system/sw/bin/niri";
    };
  };

  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [ xdg-desktop-portal-gtk ];
    config.common.default = "*";
  };

  systemd.user.services.polkit-gnome = {
    description = "GNOME Polkit authentication agent";
    wantedBy = [ "graphical-session.target" ];
    after    = [ "graphical-session.target" ];
    partOf   = [ "graphical-session.target" ];
    serviceConfig = {
      Type      = "simple";
      ExecStart = "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
      Restart   = "on-failure";
      RestartSec = "1s";
    };
  };
  # ── Greeter & keyring ───────────────────────────────────────────────────
  services.displayManager.gdm.enable = true;
  services.gnome.gnome-keyring.enable = true;
  security.pam.services.gdm.enableGnomeKeyring = true;


  # ── Open ghossty in nautilus ─────────────────────────────────────────────────────────────
  programs.nautilus-open-any-terminal = {
    enable = true;
    terminal = "ghostty";
  };

  environment.systemPackages = with pkgs; [
    polkit_gnome
  ];
}
