{ pkgs, ... }:
{
  # ── Niri + UWSM ─────────────────────────────────────────────────────────
  programs.niri = {
    enable = true;
    # Config is managed by home-manager (xdg.configFile."niri/config.kdl")
  };

  programs.uwsm = {
    enable = true;
    waylandCompositors.niri = {
      prettyName = "Niri";
      comment     = "Niri scrollable tiling compositor";
      binPath     = "/run/current-system/sw/bin/niri";
    };
  };

  # ── Portals ─────────────────────────────────────────────────────────────
  xdg.portal = {
    enable = true;
    extraPortals = [
      pkgs.xdg-desktop-portal-gnome
      pkgs.xdg-desktop-portal-gtk
    ];
    config.common.default = "*";
  };

  # ── Polkit agent for Niri (no GNOME to handle it) ───────────────────────
  systemd.user.services.polkit-gnome = {
    description = "GNOME Polkit authentication agent";
    wantedBy = [ "graphical-session.target" ];
    after = [ "graphical-session.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
      Restart = "on-failure";
    };
  };

  environment.systemPackages = with pkgs; [
    polkit_gnome
  ];
}
