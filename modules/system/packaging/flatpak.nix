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
          {
            name = "flathub-beta";
            location = "https://flathub.org/beta-repo/flathub-beta.flatpakrepo";
          }
        ];
        # Put your flatpak here or you just use terminal to install them
        packages = [];
      };

  # ── AppStream refresh on activation ──────────────────────────────────────
  # Runs `flatpak update --appstream` once flatpak is enabled: right after
  # nix-flatpak has added the remotes (flatpak-managed-install), so software
  # centers and roudix-store see the Flathub catalog (names, icons,
  # categories) without waiting for the first daily update. Oneshot +
  # RemainAfterExit: it runs at boot and whenever this unit changes (i.e.
  # the first switch that enables flatpak), not on every rebuild.
  # The leading "-" keeps the unit from failing if there's no network yet.
  systemd.services.flatpak-appstream-update = {
    description = "Refresh Flatpak AppStream metadata";
    wantedBy = [ "multi-user.target" ];
    after = [ "network-online.target" "flatpak-managed-install.service" ];
    wants = [ "network-online.target" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = "-${pkgs.flatpak}/bin/flatpak update --appstream --noninteractive";
    };
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
