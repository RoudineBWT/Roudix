{ config, lib, pkgs, ... }:
{
  options.roudix.vmGuest.enable = lib.mkOption {
    description = "Enable Roudix VM guest configurations (DNS, QEMU agent, Spice)";
    type = lib.types.bool;
    default = false;
  };

  config = lib.mkIf config.roudix.vmGuest.enable {
    # ── DNS ────────────────────────────────────────────────────────────────
    # libvirt's dnsmasq is unreliable on NixOS, force public DNS instead
    networking.nameservers = [ "1.1.1.1" "8.8.8.8" ];

    # ── QEMU Guest Agent ───────────────────────────────────────────────────
    # Allows the host to communicate with the VM (clean shutdown, snapshots...)
    services.qemuGuest.enable = true;

    # ── Spice Agent ────────────────────────────────────────────────────────
    # Enables clipboard sharing and automatic window resizing in virt-manager
    services.spice-vdagentd.enable = true;

    systemd.user.services.spice-vdagent = {
      description = "SPICE vdagent — clipboard + display resize";
      wantedBy = [ "graphical-session.target" ];
      after = [ "graphical-session.target" ];
      serviceConfig = {
        Type       = "simple";
        ExecStart  = "${pkgs.spice-vdagent}/bin/spice-vdagent -x";
        Restart    = "on-failure";
      };
    };

    # ── Virtio disk optimizations ──────────────────────────────────────────
    services.fstrim.enable = true;

    # ── Useful packages inside the VM ─────────────────────────────────────
    environment.systemPackages = with pkgs; [
      spice-vdagent
      wlr-randr
    ];
  };
}
