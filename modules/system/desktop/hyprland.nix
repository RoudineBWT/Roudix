{ config, lib, pkgs, ... }:
let
  isHyprland  = config.roudix.desktop.type == "hyprland";
  shellType   = config.roudix.desktop.shell or "noctalia";
  needsPolkit = shellType != "dms";
in
{
imports = [ ./greetd.nix ];
config =lib.mkIf isHyprland {


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

  # ── Polkit agent ────────────────────────────────────────────────────────
  # DMS a son propre agent polkit intégré.
  # Noctalia et Caelestia n'en ont pas — on lance hyprpolkitagent.
  systemd.user.services.hyprpolkitagent = lib.mkIf needsPolkit {
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

  programs.nautilus-open-any-terminal = {
    enable = true;
    terminal = "ghostty";
  };

  environment.systemPackages = with pkgs; [
    awww
    grimblast
    playerctl
    capitaine-cursors
  ] ++ lib.optionals needsPolkit [ hyprpolkitagent ];
 };
}
