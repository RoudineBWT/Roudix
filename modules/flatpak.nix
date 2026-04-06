{ pkgs, config, lib, ... }:
{
options.roudix.flatpak.enable = lib.mkOption {
  description = "Enable Roudix flatpak configurations";
  type = lib.types.bool;
  default = false;
};
config = lib.mkIf config.roudix.flatpak.enable {
  # ── Enable flatpak service ────────────────────────────────────────────────────────────
  services.flatpak.enable = true;

  # ── Flatpak auto-update ──────────────────────────────────────────────────
  systemd.services.flatpak-update = {
    description = "Update Flatpak apps";
    serviceConfig.ExecStart = "${pkgs.flatpak}/bin/flatpak update --noninteractive";
    wantedBy = [ "multi-user.target" ];
  };

  systemd.timers.flatpak-update = {
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "daily";
      Persistent = true;
      };
    };
  };
}
