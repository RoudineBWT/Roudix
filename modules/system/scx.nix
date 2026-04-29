# scx.nix — SCX scheduler support for NixOS
#
# Ce module gère tout ce qui touche aux schedulers SCX :
#   - scxctl (binaire + scx_loader) depuis roudix-caches
#   - scx.full (binaires scx_bpfland, scx_lavd, etc.)
#   - scx-switch : wrapper pkexec qui fait tout en un seul appel root
#       scx-switch set <scheduler> [mode]  → stop ananicy, start scx-loader, start scheduler
#       scx-switch unset                   → stop scheduler, stop scx-loader, start ananicy
#   - D-Bus policy pour que scx_loader puisse s'enregistrer sur le system bus
#   - Polkit policy pour que scx_loader puisse gérer les schedulers
#   - Polkit rule pour que pkexec scx-switch ne demande pas de mot de passe (groupe wheel)
#   - Service systemd scx-loader (ne démarre PAS au boot)
#
# NOTE: après un reboot, ananicy-cpp redémarre automatiquement et SCX n'est pas actif.
#       Utiliser roudix-kernel-switcher pour réactiver le scheduler souhaité.

{ pkgs, inputs, ... }:
let
  scxctl = inputs.roudix-caches.packages.x86_64-linux.scxctl;

  # ── D-Bus policy ───────────────────────────────────────────────────────────
  # Permet à scx_loader de s'enregistrer sous org.scx.Loader sur le system bus
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
  # Enregistre l'action org.scx.loader.manage-schedulers auprès de polkit
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
  # Wrapper appelé via pkexec — un seul prompt de mot de passe par switch.
  # Gère ananicy-cpp + scx-loader + scxctl en un seul appel root.
  scx-switch = pkgs.writeShellScriptBin "scx-switch" ''
    set -euo pipefail

    CMD="''${1:-}"

    # Attend que scx_loader soit vraiment joignable sur D-Bus.
    # systemctl is-active devient true avant que D-Bus soit prêt,
    # donc on ping directement le nom D-Bus à la place.
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

    case "$CMD" in
      set)
        SCHEDULER="''${2:-}"
        MODE="''${3:-}"

        if [ -z "$SCHEDULER" ]; then
          echo "Usage: scx-switch set <scheduler> [mode]" >&2
          exit 1
        fi

        echo "Stopping ananicy-cpp..."
        ${pkgs.systemd}/bin/systemctl stop ananicy-cpp 2>/dev/null || true

        echo "Starting scx-loader..."
        ${pkgs.systemd}/bin/systemctl start scx-loader
        _wait_for_scx_loader

        echo "Starting scx_''${SCHEDULER}..."
        if [ -n "$MODE" ]; then
          ${scxctl}/bin/scxctl start --sched "scx_''${SCHEDULER}" --mode "''${MODE}"
        else
          ${scxctl}/bin/scxctl start --sched "scx_''${SCHEDULER}"
        fi
        ;;

      unset)
        echo "Stopping scxctl..."
        ${scxctl}/bin/scxctl stop 2>/dev/null || true

        echo "Stopping scx-loader..."
        ${pkgs.systemd}/bin/systemctl stop scx-loader 2>/dev/null || true

        echo "Restarting ananicy-cpp..."
        ${pkgs.systemd}/bin/systemctl start ananicy-cpp
        ;;

      *)
        echo "Usage: scx-switch set <scheduler> [mode] | scx-switch unset" >&2
        exit 1
        ;;
    esac
  '';
in
{
  # ── D-Bus policy ───────────────────────────────────────────────────────────
  services.dbus.packages = [ scx-dbus-policy ];

  # ── Polkit action + rule ───────────────────────────────────────────────────
  # Action : enregistre org.scx.loader.manage-schedulers
  # Rule   : pkexec scx-switch sans mot de passe pour le groupe wheel,
  #          quel que soit le DE (KDE, GNOME, sway, etc.)
  environment.pathsToLink = [ "/share/polkit-1" ];
  environment.systemPackages = [
    scx-polkit-policy
    scxctl
    pkgs.scx.full   # scx_bpfland, scx_lavd, scx_flash, etc.
    scx-switch
  ];

  security.polkit.extraConfig = ''
    polkit.addRule(function(action, subject) {
      if (action.id === "org.freedesktop.policykit.exec" &&
          action.lookup("program") === "${scx-switch}/bin/scx-switch" &&
          subject.isInGroup("wheel")) {
        return polkit.Result.YES;
      }
    });
  '';

  # ── Service scx-loader ─────────────────────────────────────────────────────
  # Ne démarre PAS au boot (wantedBy = []).
  # Restart = "no" — le switcher a le contrôle total.
  # PATH explicite pour que scx_loader trouve les binaires scx_* de scx.full.
  systemd.services.scx-loader = {
    description = "SCX Scheduler Loader";
    wantedBy = [];
    after = [ "dbus.service" ];
    requires = [ "dbus.service" ];
    path = [ pkgs.scx.full ];  # ← ajoute scx.full au PATH sans conflit
    serviceConfig = {
      Type = "simple";
      ExecStart = "${scxctl}/bin/scx_loader";
      Restart = "no";
    };
  };
}
