{ config, lib, pkgs, ... }:
let
  isNiri     = config.roudix.desktop.type == "niri";
  shellType  = config.roudix.desktop.shell or "noctalia";
  isDms      = shellType == "dms";
  isNoctalia = shellType == "noctalia";
in
{
  imports = [ ./dankgreeter.nix ];

  config = lib.mkIf isNiri {
    programs.niri.enable = true;

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
        Type       = "simple";
        ExecStart  = "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
        Restart    = "on-failure";
        RestartSec = "1s";
      };
    };

    services.displayManager.gdm.enable = isNoctalia;
    services.gnome.gnome-keyring.enable = true;
    security.pam.services = lib.mkMerge [
      (lib.mkIf isNoctalia { gdm.enableGnomeKeyring         = true; })
      (lib.mkIf isDms      { greeter.enableGnomeKeyring = true; })
    ];

    programs.nautilus-open-any-terminal = {
      enable   = true;
      terminal = "ghostty";
    };

    environment.systemPackages = with pkgs; [ polkit_gnome ];
  };
}
