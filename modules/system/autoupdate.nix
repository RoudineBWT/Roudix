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

    minFreeSpaceGB = lib.mkOption {
      type = lib.types.int;
      default = 5;
      description = "Minimum free space on /nix/store required to attempt an update";
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
        set -uo pipefail

        # ── Failure notification ─────────────────────────────────────────
        # set -e is deliberately NOT used: on any error we want to notify
        # before exiting, not die silently mid-script with only journalctl
        # as a trace (which nobody in the family will ever check).
        _fail() {
          local reason="$1"
          echo "[roudix-autoupdate] FAILED: $reason" >&2
          ${notify} \
            "Roudix — Échec de la mise à jour" \
            "La mise à jour automatique a échoué ($reason). Voir : journalctl -u roudix-autoupdate" \
            "dialog-error"
          exit 1
        }

        # ── Avoid overlapping runs ────────────────────────────────────────
        # (manual `update` command + timer, or two timers after a suspend
        # catch-up, touching the same clone at the same time)
        exec 9>/run/lock/roudix-autoupdate.lock
        if ! ${pkgs.util-linux}/bin/flock --nonblock 9; then
          echo "[roudix-autoupdate] Another run is already in progress, skipping."
          exit 0
        fi

        cd ${cfg.configPath} || _fail "config directory missing"

        # ── Disk space check ──────────────────────────────────────────────
        AVAILABLE_GB=$(( $(${pkgs.coreutils}/bin/df /nix/store | ${pkgs.gawk}/bin/awk 'NR==2 {print $4}') / 1024 / 1024 ))
        if [ "$AVAILABLE_GB" -lt "${toString cfg.minFreeSpaceGB}" ]; then
          _fail "only ''${AVAILABLE_GB}GB free on /nix/store, need ${toString cfg.minFreeSpaceGB}GB"
        fi

        echo "[roudix-autoupdate] Fetching origin..."
        ${pkgs.git}/bin/git fetch origin ${cfg.branch} || _fail "git fetch failed (network?)"

        LOCAL=$(${pkgs.git}/bin/git rev-parse HEAD)
        REMOTE=$(${pkgs.git}/bin/git rev-parse origin/${cfg.branch})

        if [ "$LOCAL" = "$REMOTE" ]; then
          echo "[roudix-autoupdate] Already up to date ($LOCAL)."
          exit 0
        fi

        echo "[roudix-autoupdate] Changes detected — updating..."
        echo "  local:  $LOCAL"
        echo "  remote: $REMOTE"

        # Notify: update detected
        ${notify} \
          "Roudix — Update detected" \
          "New changes found on ${cfg.branch}. Updating and scheduling rebuild..." \
          "software-update-available"

        # `reset --hard` instead of `pull --rebase`: nobody but the maintainer
        # commits locally on a Roudix machine, so there is nothing to rebase —
        # only something that can conflict if upstream history was rewritten
        # (force-push). A hard reset to the fetched ref can't conflict, and
        # it only touches git-tracked files: local.nix, username.nix,
        # hardware-configuration.nix and everything else in .gitignore are
        # left exactly as they are.
        sudo -u ${username} ${pkgs.git}/bin/git reset --hard "origin/${cfg.branch}" \
          || _fail "git reset --hard failed"

        echo "[roudix-autoupdate] Scheduling rebuild for next reboot..."
        if ! ${pkgs.nh}/bin/nh os boot path:${cfg.configPath}#roudix; then
          _fail "build failed for revision $REMOTE — repo is on the new commit but the next boot was NOT scheduled; the current generation is untouched"
        fi

        echo "[roudix-autoupdate] Done — reboot to apply the new config."

        # Notify: rebuild scheduled
        ${notify} \
          "Roudix — Rebuild scheduled" \
          "Configuration updated successfully. Reboot to apply the new config." \
          "system-reboot"
      '';
    };

    systemd.timers.roudix-autoupdate = {
      description = "Roudix — periodic config update check";
      wantedBy    = [ "timers.target" ];
      timerConfig = {
        OnBootSec       = cfg.onBootDelay;
        OnUnitActiveSec = cfg.interval;
        Persistent      = true; # catch up on missed checks after suspend
      };
    };
  };
}
