{ pkgs, config, lib, ... }:
{
options.roudix.flatpak.enable = lib.mkOption {
  description = "Enable Roudix flatpak configurations";
  type = lib.types.bool;
  default = false;
};
config = lib.mkIf config.roudix.flatpak.enable {
  # ── Enable flatpak service ────────────────────────────────────────────────────────────
  services.flatpak = {
        enable = true;
        remotes = [
          {
            name = "flathub";
            location = "https://dl.flathub.org/repo/flathub.flatpakrepo";
          }
        ];
        # Put your flatpak here or you just use terminal to install them
        packages = [];
      };

  # ── Flatpak auto-update ──────────────────────────────────────────────────
  systemd.services.flatpak-update = {
        description = "Update Flatpak apps";
        after = [ "network-online.target" ];
        wants = [ "network-online.target" ];
        serviceConfig = {
          Type = "oneshot";
          ExecStart = "${pkgs.flatpak}/bin/flatpak update --noninteractive";
        };
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
