{ config, lib, pkgs, ... }:
let
  isMango    = config.roudix.desktop.type == "mangowc";
  shellType  = config.roudix.desktop.shell or "noctalia";
  isDms      = shellType == "dms";
  needsPolkit = !isDms;
in
{
  # ly.nix retiré — dankgreeter.nix gère le display manager
  imports = [ ./dankgreeter.nix ];

  config = lib.mkIf isMango {
    programs.mangowc.enable = true;

    xdg.portal = {
      enable = true;
      extraPortals = with pkgs; [ xdg-desktop-portal-gtk ];
      config.common.default = "*";
    };

    programs.dank-material-shell = lib.mkIf isDms {
      enable = true;
      systemd.enable = true;
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
    security.pam.services.dms-greeter.enableGnomeKeyring = true;

    programs.nautilus-open-any-terminal = {
      enable   = true;
      terminal = "ghostty";
    };

    environment.systemPackages = lib.optionals needsPolkit [ pkgs.polkit_gnome ];
  };
}
