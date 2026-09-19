{ config, lib, pkgs, ... }:

let
  isHyprland = config.roudix.desktop.type == "hyprland";
  isMango    = config.roudix.desktop.type == "mangowc";
  shellType  = config.roudix.desktop.shell or "noctalia";
  isNoctalia = shellType == "noctalia";
  useLy      = isHyprland || (isMango && !isNoctalia);
in

lib.mkIf useLy {

  # Sessions exposed to Ly — one per enabled compositor
  environment.etc = lib.mkMerge [
    (lib.mkIf isHyprland {
      "ly/wayland-sessions/hyprland-uwsm-fixed.desktop".source =
        "/run/current-system/sw/share/wayland-sessions/hyprland-uwsm-fixed.desktop";
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
      default_session     = if isMango then "mangowc" else "hyprland-uwsm-fixed";
      animate             = true;
      hide_borders        = false;
      hide_version_string = true;
      hide_key_hints      = true;
      initial_info_text   = "roudix";
    };
  };

  # UWSM manages graphical-session.target itself — NixOS's fake target
  # marks it as already active before login, which makes UWSM fail.
  systemd.user.targets.nixos-fake-graphical-session = lib.mkIf isHyprland {
    enable = false;
    unitConfig.DefaultDependencies = "no";
    wantedBy = lib.mkForce [];
  };

  environment.sessionVariables = {
    XDG_SESSION_TYPE = "wayland";
  };
}
