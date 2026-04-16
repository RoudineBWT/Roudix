{ config, lib, pkgs, ... }:
let
  isMango = config.roudix.desktop.type == "mangowc";
  shellType  = config.roudix.desktop.shell or "noctalia";
  isDms      = shellType == "dms";
in
{
  imports = [ ./ly.nix ./dankgreeter.nix ];

config = lib.mkIf isMango {
  programs.mangowc.enable = true;

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

  # ── Greeter & keyring ──────────────────────────────────────────────────────
  # Ly est géré centralement dans ly.nix (partagé avec hyprland)
  services.gnome.gnome-keyring.enable = true;
  security.pam.services.ly.enableGnomeKeyring = true;

  # ── Open Ghostty in Nautilus ───────────────────────────────────────────────
  programs.nautilus-open-any-terminal = {
    enable = true;
    terminal = "ghostty";
  };

  environment.systemPackages = with pkgs; [
    polkit_gnome
  ];
  };
}
