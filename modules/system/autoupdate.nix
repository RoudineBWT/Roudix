# modules/autoupdate.nix
# Automatically pulls the Roudix config from GitHub and rebuilds
# on next reboot if changes are detected. local.nix is never touched.
{ config, lib, pkgs, username, ... }:

let
  cfg = config.roudix.autoupdate;
in {
  options.roudix.autoupdate = {
    enable = lib.mkEnableOption "Automatic git pull + nh os boot on config changes";

    configPath = lib.mkOption {
      type = lib.types.str;
      default = "/home/${username}/.config/roudix";
      description = "Path to the Roudix config repository";
    };

    branch = lib.mkOption {
      type = lib.types.str;
      default = "main";
      description = "Git branch to track";
    };

    onBootDelay = lib.mkOption {
      type = lib.types.str;
      default = "5min";
      description = "Delay after boot before the first check";
    };

    interval = lib.mkOption {
      type = lib.types.str;
      default = "1h";
      description = "How often to check for updates";
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.services.roudix-autoupdate = {
      description = "Roudix — auto pull config and schedule rebuild";
      after       = [ "network-online.target" ];
      wants       = [ "network-online.target" ];
      # Only triggered by the timer, never started at activation time
      wantedBy    = lib.mkForce [];
      serviceConfig = {
        Type             = "oneshot";
        User             = username;
        WorkingDirectory = cfg.configPath;
        # Prevent the service from hanging forever
        TimeoutStartSec  = "120";
      };
      script = ''
        set -euo pipefail

        cd ${cfg.configPath}

        echo "[roudix-autoupdate] Fetching origin..."
        ${pkgs.git}/bin/git fetch origin ${cfg.branch}

        LOCAL=$(${pkgs.git}/bin/git rev-parse HEAD)
        REMOTE=$(${pkgs.git}/bin/git rev-parse origin/${cfg.branch})

        if [ "$LOCAL" = "$REMOTE" ]; then
          echo "[roudix-autoupdate] Already up to date ($LOCAL)."
          exit 0
        fi

        echo "[roudix-autoupdate] Changes detected — pulling..."
        echo "  local:  $LOCAL"
        echo "  remote: $REMOTE"

        # Stash only dotfiles/ local changes so the pull doesn't fail
        STASHED=$(${pkgs.git}/bin/git stash push --include-untracked -- dotfiles/)

        ${pkgs.git}/bin/git pull --rebase origin ${cfg.branch}

        # Restore dotfiles if anything was stashed
        if echo "$STASHED" | grep -q "Saved working directory"; then
          echo "[roudix-autoupdate] Restoring dotfiles local changes..."
          ${pkgs.git}/bin/git stash pop || true
        fi

        echo "[roudix-autoupdate] Scheduling rebuild for next reboot..."
        ${pkgs.nh}/bin/nh os boot path:${cfg.configPath}#roudix

        echo "[roudix-autoupdate] Done — reboot to apply the new config."
      '';
    };

    systemd.timers.roudix-autoupdate = {
      description  = "Roudix — periodic config update check";
      wantedBy     = [ "timers.target" ];
      timerConfig  = {
        OnBootSec       = cfg.onBootDelay;
        OnUnitActiveSec = cfg.interval;
        Persistent      = true; # catch up on missed checks after suspend
      };
    };
  };
}
