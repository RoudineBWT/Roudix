# scx.nix — SCX scheduler support for NixOS
#
# This module handles everything related to SCX schedulers:
#   - scxctl (binary + scx_loader) from roudix-caches
#   - scx.full (scx_bpfland, scx_lavd, etc. binaries)
#   - scx-switch: pkexec wrapper that does everything in one root call
#       scx-switch set <scheduler> [mode]  → stop ananicy, start scx-loader, start scheduler
#       scx-switch unset                   → stop scheduler, stop scx-loader, start ananicy
#   - D-Bus policy so scx_loader can register on the system bus
#   - Polkit policy so scx_loader can manage schedulers
#   - Polkit rule so pkexec scx-switch doesn't prompt for a password (wheel group)
#   - scx-loader systemd service (does NOT start at boot)
#
# NOTE: after a reboot, ananicy-cpp restarts automatically and SCX is not active.
#       Use roudix-kernel-switcher to re-enable the desired scheduler.

{ pkgs, inputs, roudix-scheduler-switcher, ... }:
let
  scxctl = inputs.roudix-caches.packages.x86_64-linux.scxctl;

  # File where scx-switch keeps the last manually chosen scheduler,
  # only used when ananicy-cpp is disabled (roudix.gaming.ananicy.enable = false).
  scxStateFile = "/var/lib/scx-switch/last-scheduler";

  # ── D-Bus policy ───────────────────────────────────────────────────────────
  # Lets scx_loader register as org.scx.Loader on the system bus
  scx-dbus-policy = pkgs.writeTextDir "share/dbus-1/system.d/org.scx.Loader.conf" ''
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
      "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
    <busconfig>
      <policy user="root">
        <allow own="org.scx.Loader"/>
        <allow send_destination="org.scx.Loader"/>
        <allow receive_sender="org.scx.Loader"/>
      </policy>
      <policy context="default">
        <allow send_destination="org.scx.Loader"/>
        <allow receive_sender="org.scx.Loader"/>
      </policy>
    </busconfig>
  '';

  # ── Polkit action policy ───────────────────────────────────────────────────
  # Registers the org.scx.loader.manage-schedulers action with polkit
  scx-polkit-policy = pkgs.writeTextDir "share/polkit-1/actions/org.scx.loader.policy" ''
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE policyconfig PUBLIC
      "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
      "http://www.freedesktop.org/standards/PolicyKit/1.0/policyconfig.dtd">
    <policyconfig>
      <action id="org.scx.loader.manage-schedulers">
        <description>Manage SCX schedulers</description>
        <message>Authentication is required to manage SCX schedulers</message>
        <defaults>
          <allow_any>auth_admin</allow_any>
          <allow_inactive>auth_admin</allow_inactive>
          <allow_active>auth_admin</allow_active>
        </defaults>
      </action>
    </policyconfig>
  '';

  # ── scx-switch ─────────────────────────────────────────────────────────────
  # Wrapper called via pkexec — a single password prompt per switch.
  # Handles ananicy-cpp + scx-loader + scxctl in a single root call.
  scx-switch = pkgs.writeShellScriptBin "scx-switch" ''
    set -euo pipefail

    STATE_FILE="${scxStateFile}"
    CMD="''${1:-}"

    # Waits until scx_loader is actually reachable on D-Bus.
    # systemctl is-active turns true before D-Bus is ready,
    # so we ping the D-Bus name directly instead.
    _wait_for_scx_loader() {
      local i=0
      while [ $i -lt 25 ]; do
        if ${pkgs.dbus}/bin/dbus-send \
            --system --print-reply \
            --dest=org.scx.Loader \
            /org/scx/Loader \
            org.freedesktop.DBus.Peer.Ping 2>/dev/null; then
          return 0
        fi
        sleep 0.2
        i=$((i + 1))
      done
      echo "scx-loader failed to register on D-Bus in time" >&2
      return 1
    }

    # ananicy-cpp isn't even installed if roudix.gaming.ananicy.enable = false
    _ananicy_enabled() {
      ${pkgs.systemd}/bin/systemctl is-enabled ananicy-cpp.service &>/dev/null
    }

    case "$CMD" in
      set)
        SCHEDULER="''${2:-}"
        MODE="''${3:-}"
        # extra flags, passed as a single "--foo --bar baz" string
        # (no support for nested quoting — simple use case only)
        EXTRA="''${4:-}"

        if [ -z "$SCHEDULER" ]; then
          echo "Usage: scx-switch set <scheduler> [mode] [extra-flags]" >&2
          exit 1
        fi

        if _ananicy_enabled; then
          echo "Stopping ananicy-cpp..."
          ${pkgs.systemd}/bin/systemctl stop ananicy-cpp 2>/dev/null || true
        fi

        echo "Starting scx-loader..."
        ${pkgs.systemd}/bin/systemctl start scx-loader
        _wait_for_scx_loader

        # IMPORTANT: never use `scxctl switch` to go from one scheduler
        # to another — the hot-switch doesn't fully unload the previous
        # scheduler's struct_ops/BPF kptrs before the new one inits,
        # which triggers a kernel-side "kptr already had cpumask" error
        # (seen notably coming out of scx_rusty). Always do a clean stop,
        # then a fresh start.
        echo "Stopping any currently running scheduler..."
        ${scxctl}/bin/scxctl stop 2>/dev/null || true
        # Lets the kernel finish tearing down the previous struct_ops before
        # loading a new BPF program.
        sleep 0.3

        echo "Starting scx_''${SCHEDULER}..."
        # NOTE: --sched expects the bare name (e.g. "bpfland"), NOT "scx_bpfland" —
        # scxctl prefixes it itself internally.
        CMD_ARGS=(start --sched "''${SCHEDULER}")
        if [ -n "$EXTRA" ]; then
          # scxctl expects extra flags as a single CSV string
          # (e.g. --args="-c,75,-m,0-15"), not command-line style — passing
          # them as raw arguments would collide the scheduler's own short
          # flags (e.g. bpfland "-m performance") with scxctl's (-s/-m/-a).
          # shellcheck disable=SC2206
          EXTRA_ARR=($EXTRA)
          EXTRA_CSV=$(IFS=,; echo "''${EXTRA_ARR[*]}")
          # `=` is required, otherwise clap treats "-m,..." as an unknown
          # flag right after --args and errors with "a value is required
          # for '--args'".
          #
          # --mode and --args are mutually exclusive in scxctl; our
          # per-profile default flags already encode the mode, so --args
          # replaces --mode here instead of adding to it.
          CMD_ARGS+=("--args=''${EXTRA_CSV}")
        elif [ -n "$MODE" ]; then
          CMD_ARGS+=(--mode "''${MODE}")
        fi
        ${scxctl}/bin/scxctl "''${CMD_ARGS[@]}"

        if _ananicy_enabled; then
          # ananicy will take back over by itself on the next boot,
          # no need to persist anything
          rm -f "''${STATE_FILE}"
        else
          # no ananicy → remember the choice so it survives a reboot
          # (3 lines: scheduler / mode / extra-flags)
          mkdir -p "$(dirname "''${STATE_FILE}")"
          {
            echo "''${SCHEDULER}"
            echo "''${MODE}"
            echo "''${EXTRA}"
          } > "''${STATE_FILE}"
        fi
        ;;

      unset)
        echo "Stopping scxctl..."
        ${scxctl}/bin/scxctl stop 2>/dev/null || true

        echo "Stopping scx-loader..."
        ${pkgs.systemd}/bin/systemctl stop scx-loader 2>/dev/null || true

        if _ananicy_enabled; then
          echo "Restarting ananicy-cpp..."
          ${pkgs.systemd}/bin/systemctl start ananicy-cpp
        fi

        rm -f "''${STATE_FILE}"
        ;;

      *)
        echo "Usage: scx-switch set <scheduler> [mode] | scx-switch unset" >&2
        exit 1
        ;;
    esac
  '';

  # Re-reads the state file at boot and restarts the remembered scheduler.
  # No-op if the file doesn't exist (ananicy enabled, or "none" selected).
  scx-restore = pkgs.writeShellScriptBin "scx-restore-default" ''
    set -euo pipefail
    STATE_FILE="${scxStateFile}"

    [ -f "''${STATE_FILE}" ] || exit 0
    # 3-line format: scheduler / mode / extra-flags (mode and extra can be empty)
    { read -r SCHEDULER || true; read -r MODE || true; read -r EXTRA || true; } < "''${STATE_FILE}"
    [ -n "''${SCHEDULER:-}" ] || exit 0

    ${pkgs.systemd}/bin/systemctl start scx-loader

    i=0
    while [ $i -lt 25 ]; do
      if ${pkgs.dbus}/bin/dbus-send --system --print-reply \
          --dest=org.scx.Loader /org/scx/Loader \
          org.freedesktop.DBus.Peer.Ping 2>/dev/null; then
        break
      fi
      sleep 0.2
      i=$((i + 1))
    done

    # No switch here either (see comment in scx-switch): at boot
    # nothing is normally running yet, but we stop anyway as a safety net
    # in case scx-loader already auto-loaded a default scheduler.
    ${scxctl}/bin/scxctl stop 2>/dev/null || true
    sleep 0.3

    # NOTE: --sched expects the bare name (e.g. "bpfland"), NOT "scx_bpfland".
    CMD_ARGS=(start --sched "''${SCHEDULER}")
    if [ -n "''${EXTRA:-}" ]; then
      # see comment in scx-switch: CSV format expected by scxctl,
      # not command-line style. --mode and --args are mutually
      # exclusive on scxctl's side, so --args wins here if set.
      # shellcheck disable=SC2206
      EXTRA_ARR=($EXTRA)
      EXTRA_CSV=$(IFS=,; echo "''${EXTRA_ARR[*]}")
      CMD_ARGS+=("--args=''${EXTRA_CSV}")
    elif [ -n "''${MODE:-}" ] && [ "''${MODE}" != "None" ]; then
      CMD_ARGS+=(--mode "''${MODE}")
    fi
    ${scxctl}/bin/scxctl "''${CMD_ARGS[@]}"
  '';
in
{
  # ── D-Bus policy ───────────────────────────────────────────────────────────
  services.dbus.packages = [ scx-dbus-policy ];

  # ── Polkit action + rule ───────────────────────────────────────────────────
  # Action: registers org.scx.loader.manage-schedulers
  # Rule:   pkexec scx-switch without a password for the wheel group,
  #         regardless of DE (KDE, GNOME, sway, etc.)
  environment.pathsToLink = [ "/share/polkit-1" ];
  environment.systemPackages = [
    scx-polkit-policy
    scxctl
    inputs.roudix-caches.packages.x86_64-linux.scx.full   # scx_bpfland, scx_lavd, scx_flash, etc.
    scx-switch
    scx-restore
    roudix-scheduler-switcher
  ];

  # Folder for the state file (last chosen scheduler, outside of ananicy)
  systemd.tmpfiles.rules = [
    "d /var/lib/scx-switch 0755 root root -"
  ];

  # Restarts the remembered scheduler at boot — only relevant when
  # roudix.gaming.ananicy.enable = false (otherwise the state file stays empty).
  # No mkIf on the option here: the service is a harmless no-op
  # as long as scx-switch hasn't written anything to the state file.
  systemd.services.scx-restore-default = {
    description = "Restore last selected SCX scheduler at boot (used when ananicy-cpp is off)";
    after = [ "dbus.service" ];
    wants = [ "dbus.service" ];
    wantedBy = [ "multi-user.target" ];
    path = [ pkgs.scx.full ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = "${scx-restore}/bin/scx-restore-default";
    };
  };

  security.polkit.extraConfig = ''
    polkit.addRule(function(action, subject) {
      if (action.id === "org.freedesktop.policykit.exec" &&
          action.lookup("program") === "${scx-switch}/bin/scx-switch" &&
          subject.isInGroup("wheel")) {
        return polkit.Result.YES;
      }
    });
  '';

  # ── scx-loader service ─────────────────────────────────────────────────────
  # Does NOT start at boot (wantedBy = []).
  # Restart = "no" — the switcher is in full control.
  # Explicit PATH so scx_loader finds the scx_* binaries from scx.full.
  systemd.services.scx-loader = {
    description = "SCX Scheduler Loader";
    wantedBy = [];
    after = [ "dbus.service" ];
    requires = [ "dbus.service" ];
    path = [ pkgs.scx.full ];  # ← adds scx.full to PATH without conflict
    serviceConfig = {
      Type = "simple";
      ExecStart = "${scxctl}/bin/scx_loader";
      Restart = "no";
    };
  };
}
