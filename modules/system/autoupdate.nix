# modules/autoupdate.nix
# Automatically pulls the Roudix config from GitHub and rebuilds
# on next reboot if changes are detected. local.nix is never touched.
{ config, lib, pkgs, username, ... }:

let
  cfg = config.roudix.autoupdate;

  # Helper: send a notification to the user's graphical session
  notify = pkgs.writeShellScript "roudix-notify" ''
    SUMMARY="$1"
    BODY="$2"
    ICON="$3"

    # Find the user's D-Bus session address
    USER_ID=$(id -u ${username})
    DBUS_ADDR=$(cat /proc/$(pgrep -u ${username} -x "dbus-daemon" | head -1)/environ 2>/dev/null \
      | tr '\0' '\n' | grep DBUS_SESSION_BUS_ADDRESS | cut -d= -f2-)

    if [ -z "$DBUS_ADDR" ]; then
      # Fallback: try via systemd user session
      DBUS_ADDR="unix:path=/run/user/$USER_ID/bus"
    fi

    DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" \
    XDG_RUNTIME_DIR="/run/user/$USER_ID" \
    sudo -u ${username} \
      ${pkgs.libnotify}/bin/notify-send \
        --app-name="Roudix" \
        --icon="$ICON" \
        --urgency=normal \
        "$SUMMARY" "$BODY" 2>/dev/null || true
  '';
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
    environment.systemPackages = [ pkgs.libnotify ];

    systemd.services.roudix-autoupdate = {
      description = "Roudix — auto pull config and schedule rebuild";
      after       = [ "network-online.target" ];
      wants       = [ "network-online.target" ];
      # Only triggered by the timer, never started at activation time
      wantedBy    = lib.mkForce [];
      serviceConfig = {
        Type             = "oneshot";
        User             = "root";
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

        # Notify: update detected
        ${notify} \
          "Roudix — Update detected" \
          "New changes found on ${cfg.branch}. Pulling and scheduling rebuild..." \
          "software-update-available"

        sudo -u ${username} ${pkgs.git}/bin/git pull --rebase origin ${cfg.branch}

        echo "[roudix-autoupdate] Scheduling rebuild for next reboot..."
        ${pkgs.nh}/bin/nh os boot path:${cfg.configPath}#roudix

        echo "[roudix-autoupdate] Done — reboot to apply the new config."

        # Notify: rebuild scheduled
        ${notify} \
          "Roudix — Rebuild scheduled" \
          "Configuration updated successfully. Reboot to apply the new config." \
          "system-reboot"
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
