{ config, lib, pkgs, ... }:
let
  isHyprland = config.roudix.desktop.type == "hyprland";
in
lib.mkIf isHyprland {
  programs.hyprland = {
    enable = true;
    withUWSM = true;
    xwayland.enable = true;
  };

  programs.uwsm = {
    enable = true;
    waylandCompositors.hyprland = {
      prettyName = "Hyprland";
      comment     = "Hyprland dynamic tiling compositor";
      binPath     = "/run/current-system/sw/bin/hyprland";
    };
  };

  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [
      xdg-desktop-portal-hyprland
      xdg-desktop-portal-gtk
    ];
    config.common.default = "*";
  };

  # ── Polkit agent — hyprpolkitagent requires systemd user session (uwsm)
  #    fallback to polkit-gnome for plain hyprland sessions
  systemd.user.services.hyprpolkitagent = lib.mkIf config.programs.hyprland.withUWSM {
    description = "Hyprland Polkit agent";
    wantedBy = [ "graphical-session.target" ];
    after    = [ "graphical-session.target" ];
    partOf   = [ "graphical-session.target" ];
    serviceConfig = {
      Type       = "simple";
      ExecStart  = "${pkgs.hyprpolkitagent}/libexec/hyprpolkitagent";
      Restart    = "on-failure";
      RestartSec = "1s";
    };
  };

  systemd.user.services.polkit-gnome-agent = lib.mkIf (!config.programs.hyprland.withUWSM) {
    description = "Polkit GNOME agent (fallback without uwsm)";
    wantedBy = [ "graphical-session.target" ];
    after    = [ "graphical-session.target" ];
    partOf   = [ "graphical-session.target" ];
    serviceConfig = {
      Type      = "simple";
      ExecStart = "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
      Restart    = "on-failure";
      RestartSec = "1s";
    };
  };

  # ── Greeter & keyring ───────────────────────────────────────────────────
  services.displayManager.gdm.enable = true;
  services.gnome.gnome-keyring.enable = true;
  security.pam.services.gdm.enableGnomeKeyring = true;


  programs.nautilus-open-any-terminal = {
    enable = true;
    terminal = "ghostty";
  };

  environment.systemPackages = with pkgs; [
    hyprpolkitagent
    polkit_gnome
    awww
    grimblast
    playerctl
  ];
}
