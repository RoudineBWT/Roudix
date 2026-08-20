{ config, lib, pkgs, ... }:
let
  isMango     = config.roudix.desktop.type == "mangowc";
  shellType   = config.roudix.desktop.shell or "noctalia";
  isDms       = shellType == "dms";
  isNoctalia  = shellType == "noctalia";
  needsPolkit = !isDms;
in
{
  imports = [ ./ly.nix ];

  config = lib.mkIf isMango {
    programs.mangowc.enable = true;

    xdg.portal = {
      enable = true;
      extraPortals = with pkgs; [ xdg-desktop-portal-gtk xdg-desktop-portal-wlr ];
      config.common.default = [ "wlr" "gtk" ];
    };

    programs.dank-material-shell = lib.mkIf isDms {
      enable = true;
      systemd.enable = true;
    };

    # ── Greeter Noctalia (remplace ly quand shell == noctalia) ────────────
    programs.noctalia-greeter = lib.mkIf isNoctalia {
      enable = true;
      greeter-args = "--session mangowc";
      settings = {
        keyboard = {
          layout  = "us";
          variant = "intl";
        };
      };
    };

    systemd.user.services.polkit-gnome = lib.mkIf needsPolkit {
      description = "GNOME Polkit authentication agent";
      wantedBy = [ "graphical-session.target" ];
      after    = [ "graphical-session.target" ];
      partOf   = [ "graphical-session.target" ];
      serviceConfig = {
        Type       = "simple";
        ExecStart  = "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
        Restart    = "on-failure";
        RestartSec = "1s";
      };
    };

    services.gnome.gnome-keyring.enable = true;
    security.pam.services.ly.enableGnomeKeyring     = lib.mkIf (!isNoctalia) true;
    security.pam.services.greetd.enableGnomeKeyring = lib.mkIf isNoctalia true;

    environment.systemPackages = lib.optionals needsPolkit [ pkgs.polkit_gnome ];
  };
}
