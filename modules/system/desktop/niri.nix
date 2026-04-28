{ config, lib, pkgs, inputs, ... }:
let
  isNiri     = config.roudix.desktop.type == "niri";
  shellType  = config.roudix.desktop.shell or "noctalia";
  isDms      = shellType == "dms";
in
{
  imports = [ ./dankgreeter.nix ];

  config = lib.mkIf isNiri {
    programs.niri = {
      enable = true;
    };

    xdg.portal = {
      enable = true;
      extraPortals = with pkgs; [
        xdg-desktop-portal-gtk
        xdg-desktop-portal-gnome
      ];
      config.niri = {
        default = [ "gnome" "gtk" ];
        "org.freedesktop.impl.portal.ScreenCast" = [ "gnome" ];
        "org.freedesktop.impl.portal.RemoteDesktop" = [ "gnome" ];
      };
    };
    programs.dank-material-shell = lib.mkIf isDms {
      enable = true;
      systemd.enable = true;
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

    # GDM supprimé — dankgreeter.nix gère le display manager pour tous les shells
    services.gnome.gnome-keyring.enable = true;
    security.pam.services.dms-greeter.enableGnomeKeyring = true;

    programs.nautilus-open-any-terminal = {
      enable   = true;
      terminal = "ghostty";
    };

    environment.systemPackages = with pkgs; [ polkit_gnome ];
  };
}
