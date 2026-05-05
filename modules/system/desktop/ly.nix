{ config, lib, pkgs, ... }:

let
  isHyprland = config.roudix.desktop.type == "hyprland";
  isMango    = config.roudix.desktop.type == "mangowc";
  useLy      = isHyprland || isMango;
in

lib.mkIf useLy {

  # Sessions exposées à Ly — une par compositeur activé
  environment.etc = lib.mkMerge [
    (lib.mkIf isHyprland {
      "ly/wayland-sessions/hyprland-uwsm.desktop".source =
        "/run/current-system/sw/share/wayland-sessions/hyprland-uwsm.desktop";
    })
    (lib.mkIf isMango {
      "ly/wayland-sessions/mangowc.desktop".text = ''
        [Desktop Entry]
        Name=MangoWC
        Exec=mango
        Type=Application
      '';
    })
  ];

  services.displayManager.ly = {
    enable = true;

    settings = {
      waylandsessions     = "/etc/ly/wayland-sessions";
      xsessions           = "";
      xinitrcpath         = "";
      default_session     = if isMango then "mangowc" else "hyprland-uwsm";
      animate             = true;
      hide_borders        = false;
      hide_version_string = true;
      hide_key_hints      = true;
      initial_info_text   = "roudix";
    };
  };

  # UWSM gère lui-même graphical-session.target — le fake target de NixOS
  # le marque comme déjà actif avant le login, ce qui fait échouer UWSM.
  systemd.user.targets.nixos-fake-graphical-session = lib.mkIf isHyprland {
    enable = false;
    unitConfig.DefaultDependencies = "no";
    wantedBy = lib.mkForce [];
  };

  environment.sessionVariables = {
    XDG_SESSION_TYPE = "wayland";
  };
}
