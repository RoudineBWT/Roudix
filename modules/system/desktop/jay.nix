{ config, lib, pkgs, inputs, username, ... }:
let
  isJay  = config.roudix.desktop.type == "jay";
  shellType   = config.roudix.desktop.shell or "noctalia";
  needsPolkit = shellType != "dms";
in
{
config = lib.mkIf isJay {

  # ── Greeter Noctalia (si shell == noctalia) ──────────────────────────────
  programs.noctalia-greeter = {
    enable = true;
    greeter-args = "--session jay";
    settings = {
      keyboard = {
        layout  = "us";
        variant = "intl";
      };
    };
  };

  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [
      xdg-desktop-portal-gtk
    ];
    config.common.default = "*";
  };

  # ── Polkit agent ────────────────────────────────────────────────────────
  # DMS a son propre agent polkit intégré.
  # Noctalia et Caelestia n'en ont pas — on lance polkit-gnome.
  systemd.user.services.polkit-gnome = lib.mkIf needsPolkit {
    description = "Polkit GNOME agent";
    wantedBy = [ "graphical-session.target" ];
    after    = [ "graphical-session.target" ];
    partOf   = [ "graphical-session.target" ];
    serviceConfig = {
      Type      = "simple";
      ExecStart = "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
      Restart    = "on-failure";
      RestartSec = "1s";
    };
  };

  programs.nautilus-open-any-terminal = {
    enable = true;
    terminal = "ghostty";
  };

  # ── Keyring ───────────────────────────────────────────────────────────
  services.gnome.gnome-keyring.enable = true;
  security.pam.services.greetd.enableGnomeKeyring = true;
  security.polkit.enable = true;

  environment.systemPackages = with pkgs; [
    awww
    jay
    grimblast
    playerctl
  ] ++ lib.optionals needsPolkit [ polkit_gnome ];
 };
}
