{ config, lib, pkgs, inputs, username, ... }:
let
  isNiri    = config.roudix.desktop.type == "niri";
  shellType = config.roudix.desktop.shell or "noctalia";
  isDms     = shellType == "dms";
in
{
  config = lib.mkIf isNiri {
    programs.niri.enable = true;

    # ── Greeter ───────────────────────────────────────────────────────────
    programs.dank-material-shell = lib.mkMerge [
      {
        greeter = {
          enable = true;
          compositor.name = "niri";
          configHome = "/home/${username}";
          logs = {
            save = true;
            path = "/tmp/dms-greeter.log";
          };
        };
      }

      # ── DMS ───────────────────────────────────────────────────────────
      (lib.mkIf isDms {
        enable = true;
        systemd.enable = true;
      })
    ];

    # ── Portals ───────────────────────────────────────────────────────────
    xdg.portal = {
      enable = true;
      extraPortals = with pkgs; [
        xdg-desktop-portal-gtk
        xdg-desktop-portal-gnome
      ];
      config.niri = {
        default = [ "gnome" "gtk" ];
        "org.freedesktop.impl.portal.ScreenCast"    = [ "gnome" ];
        "org.freedesktop.impl.portal.RemoteDesktop" = [ "gnome" ];
      };
    };

    # ── Polkit ────────────────────────────────────────────────────────────
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

    # ── Keyring ───────────────────────────────────────────────────────────
    services.gnome.gnome-keyring.enable = true;
    security.pam.services.greetd.enableGnomeKeyring = true;

    programs.nautilus-open-any-terminal = {
      enable   = true;
      terminal = "ghostty";
    };

    environment.systemPackages = with pkgs; [ polkit_gnome ];
  };
}
