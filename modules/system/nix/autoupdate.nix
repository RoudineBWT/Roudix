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
    DBUS_ADDR=$(cat /proc/$(${pkgs.procps}/bin/pgrep -u ${username} -x "dbus-daemon" | head -1)/environ 2>/dev/null \
      | tr '\0' '\n' | grep DBUS_SESSION_BUS_ADDRESS | cut -d= -f2-)

    if [ -z "$DBUS_ADDR" ]; then
      # Fallback: try via systemd user session
      DBUS_ADDR="unix:path=/run/user/$USER_ID/bus"
    fi

    ${pkgs.util-linux}/bin/runuser -u ${username} -- \
      ${pkgs.coreutils}/bin/env \
        DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" \
        XDG_RUNTIME_DIR="/run/user/$USER_ID" \
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
      onFailure   = [ "roudix-autoupdate-notify-failure.service" ];
      after       = [ "network-online.target" ];
      wants       = [ "network-online.target" ];
      # Only triggered by the timer, never started at activation time
      wantedBy    = lib.mkForce [];
      # systemd services get a minimal PATH: nh shells out to `nix` (and nix
      # to git for some fetchers), so both must be provided explicitly.
      path        = [ config.nix.package pkgs.git pkgs.nh ];
      serviceConfig = {
        # /var/lib/roudix-autoupdate: remembers a revision whose build failed
        StateDirectory   = "roudix-autoupdate";
        Type             = "oneshot";
        User             = "root";
        WorkingDirectory = cfg.configPath;
        # Prevent the service from hanging forever — but a rebuild (new
        # kernel, uncached package) easily takes more than 2 minutes, and a
        # timeout kills the run before `_fail` can notify anyone.
        TimeoutStartSec  = "2h";
      };
      script = ''
        set -uo pipefail

        # Run git as the repo owner: the service runs as root, and git refuses
        # ("dubious ownership") to touch a repo owned by someone else. Running
        # as the owner also avoids leaving root-owned files inside .git.
        GIT="${pkgs.util-linux}/bin/runuser -u ${username} -- ${pkgs.coreutils}/bin/env HOME=/home/${username} ${pkgs.git}/bin/git"

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
        # catch-up, touching the same clone at the same time).
        # The lock is held on the config directory itself, which is also what
        # `roudix-update` locks: it runs as the normal user and cannot create
        # a lock file in /run/lock, so a file there could never be shared.
        cd ${cfg.configPath} || _fail "config directory missing"
        exec 9<.
        if ! ${pkgs.util-linux}/bin/flock --nonblock 9; then
          echo "[roudix-autoupdate] Another run is already in progress, skipping."
          exit 0
        fi

        # ── Disk space check ──────────────────────────────────────────────
        AVAILABLE_GB=$(( $(${pkgs.coreutils}/bin/df /nix/store | ${pkgs.gawk}/bin/awk 'NR==2 {print $4}') / 1024 / 1024 ))
        if [ "$AVAILABLE_GB" -lt "${toString cfg.minFreeSpaceGB}" ]; then
          _fail "only ''${AVAILABLE_GB}GB free on /nix/store, need ${toString cfg.minFreeSpaceGB}GB"
        fi

        echo "[roudix-autoupdate] Fetching origin..."
        $GIT fetch origin ${cfg.branch} || _fail "git fetch failed (network?)"

        LOCAL=$($GIT rev-parse HEAD)
        REMOTE=$($GIT rev-parse origin/${cfg.branch})

        PENDING=/var/lib/roudix-autoupdate/pending
        NEED_MERGE=1

        if [ "$LOCAL" = "$REMOTE" ]; then
          # The repo can already be on $REMOTE while its build failed on a
          # previous run (merge succeeded, build did not). Retry in that case
          # instead of reporting "up to date" forever.
          if [ -f "$PENDING" ] && [ "$(cat "$PENDING")" = "$LOCAL" ]; then
            echo "[roudix-autoupdate] Revision $LOCAL was never built successfully — retrying build."
            NEED_MERGE=0
          else
            echo "[roudix-autoupdate] Already up to date ($LOCAL)."
            exit 0
          fi
        fi

        if [ "$NEED_MERGE" = 1 ]; then
          # ── Never discard local work ──────────────────────────────────────
          # Only fast-forward. If this machine is ahead of origin (unpushed
          # commits — e.g. the maintainer's own machine) there is nothing to
          # pull; if it has diverged, refuse instead of overwriting. Nobody
          # force-pushes these branches (the sync workflows only merge), so a
          # plain fast-forward is always possible on a normal user machine.
          if $GIT merge-base --is-ancestor "$REMOTE" "$LOCAL"; then
            echo "[roudix-autoupdate] Local is ahead of origin/${cfg.branch} (unpushed commits) — nothing to pull."
            exit 0
          fi
          if ! $GIT merge-base --is-ancestor "$LOCAL" "$REMOTE"; then
            _fail "local history has diverged from origin/${cfg.branch} — refusing to overwrite local commits, resolve manually"
          fi

          echo "[roudix-autoupdate] Changes detected — updating..."
          echo "  local:  $LOCAL"
          echo "  remote: $REMOTE"

          # Notify: update detected
          ${notify} \
            "Roudix — Update detected" \
            "New changes found on ${cfg.branch}. Updating and scheduling rebuild..." \
            "software-update-available"

          # Fast-forward only (no `reset --hard`): it can never throw away a
          # local commit, and it aborts if a tracked local modification would be
          # overwritten. Untracked/ignored files (local.nix, username.nix,
          # hardware-configuration.nix...) are left exactly as they are.
          $GIT merge --ff-only "origin/${cfg.branch}" \
            || _fail "git merge --ff-only failed (local modifications in the way?)"
        fi

        echo "[roudix-autoupdate] Scheduling rebuild for next reboot..."
        # No '#<attr>' here: nh (like nixos-rebuild) picks the
        # nixosConfigurations attribute matching this machine's own
        # hostname automatically — same convention modules/home/shell's
        # roudix-update/roudix-switch already rely on. This is
        # why every host's networking.hostName MUST equal its
        # hosts/<name>/ directory name.
        if ! ${pkgs.nh}/bin/nh os boot path:${cfg.configPath}; then
          echo "$REMOTE" > "$PENDING"
          _fail "build failed for revision $REMOTE — repo is on the new commit but the next boot was NOT scheduled; the current generation is untouched"
        fi

        rm -f "$PENDING"
        echo "[roudix-autoupdate] Done — reboot to apply the new config."

        # Notify: rebuild scheduled
        ${notify} \
          "Roudix — Rebuild scheduled" \
          "Configuration updated successfully. Reboot to apply the new config." \
          "system-reboot"
      '';
    };

    # Covers what `_fail` cannot: timeout, kill, crash. A plain `exit 1`
    # from `_fail` has already notified, so it is skipped here (needs the
    # MONITOR_* variables systemd passes to OnFailure= units; without them the
    # worst case is a duplicate notification).
    systemd.services.roudix-autoupdate-notify-failure = {
      description = "Roudix — notify when roudix-autoupdate stopped unexpectedly";
      serviceConfig.Type = "oneshot";
      script = ''
        if [ "''${MONITOR_SERVICE_RESULT:-}" = "exit-code" ] && [ "''${MONITOR_EXIT_STATUS:-}" = "1" ]; then
          exit 0
        fi
        ${notify} \
          "Roudix — Mise à jour interrompue" \
          "La mise à jour automatique s'est arrêtée de façon inattendue (''${MONITOR_SERVICE_RESULT:-inconnu}). Voir : journalctl -u roudix-autoupdate" \
          "dialog-error"
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
