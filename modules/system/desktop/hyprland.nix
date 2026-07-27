{ config, lib, pkgs, inputs, username, ... }:
let
  isHyprland  = config.roudix.desktop.type == "hyprland";
  shellType   = config.roudix.desktop.shell or "noctalia";
  needsPolkit = shellType != "dms";
  isDms       = shellType == "dms";
  isNoctalia  = shellType == "noctalia";
in
{
config = lib.mkIf isHyprland {

  # ── Greeter DMS (si shell == dms ou caelestia, donc !isNoctalia) ─────────
  programs.dms-greeter = lib.mkIf (!isNoctalia) {
    enable = true;
    compositor.name = "hyprland";
    configHome = "/home/${username}";
  };

  # ── DMS (shell) ─────────────────────────────────────────────────────────
  programs.dank-material-shell = lib.mkIf isDms {
    enable = true;
    systemd.enable = true;
  };

  # ── Greeter Noctalia (si shell == noctalia) ──────────────────────────────
  programs.noctalia-greeter = lib.mkIf isNoctalia {
    enable = true;
    greeter-args = "--session hyprland";
    settings = {
      keyboard = {
        layout  = "us";
        variant = "intl";
      };
    };
  };

  programs.hyprland = {
    enable = true;
    withUWSM = true;
    xwayland.enable = true;
  };

  programs.uwsm.enable = true;

  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [
      xdg-desktop-portal-hyprland
      xdg-desktop-portal-gtk
    ];
    config.common.default = "*";
  };

  # ── Polkit agent ────────────────────────────────────────────────────────
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

  programs.nautilus-open-any-terminal = {
    enable = true;
    terminal = "ghostty";
  };

  # ── Keyring ───────────────────────────────────────────────────────────
  services.gnome.gnome-keyring.enable = true;
  security.pam.services.greetd.enableGnomeKeyring = true;


  environment.systemPackages = with pkgs; [
    awww
    grimblast
    playerctl
  ] ++ lib.optionals needsPolkit [ hyprpolkitagent ];
 };
}
