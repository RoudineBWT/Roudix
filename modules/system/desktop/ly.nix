{ config, lib, pkgs, ... }:

let
  isHyprland = config.roudix.desktop.type == "hyprland";
in

lib.mkIf isHyprland {

  # Répertoire custom avec uniquement la session UWSM
  environment.etc."ly/wayland-sessions/hyprland-uwsm.desktop" = {
    source = "/run/current-system/sw/share/wayland-sessions/hyprland-uwsm.desktop";
  };

  services.displayManager.ly = {
    enable = true;

    settings = {
      waylandsessions     = "/etc/ly/wayland-sessions";
      xsessions           = "";
      xinitrcpath         = "";
      default_session     = "hyprland-uwsm";
      animate             = true;
      hide_borders        = false;
      hide_version_string = true;
      hide_key_hints      = true;
      initial_info_text   = "roudix";
    };
  };

  # UWSM gère lui-même graphical-session.target — le fake target de NixOS
  # le marque comme déjà actif avant le login, ce qui fait échouer UWSM.
  systemd.user.targets.nixos-fake-graphical-session = {
    enable = false;
    unitConfig.DefaultDependencies = "no";
    wantedBy = lib.mkForce [];
  };

  environment.sessionVariables = {
    XDG_SESSION_TYPE = "wayland";
  };
}
