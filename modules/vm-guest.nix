{ config, lib, pkgs, ... }:
{
  options.roudix.vmGuest.enable = lib.mkOption {
    description = "Enable Roudix VM guest configurations (DNS, QEMU agent, Spice)";
    type = lib.types.bool;
    default = false;
  };

  config = lib.mkIf config.roudix.vmGuest.enable {
    # ── DNS ────────────────────────────────────────────────────────────────
    # dnsmasq de libvirt n'est pas fiable sur NixOS, on force des DNS publics
    networking.nameservers = [ "1.1.1.1" "8.8.8.8" ];

    # ── QEMU Guest Agent ───────────────────────────────────────────────────
    # Permet à l'hôte de communiquer avec la VM (shutdown propre, snapshots, etc.)
    services.qemuGuest.enable = true;

    # ── Spice Agent ────────────────────────────────────────────────────────
    # Copier/coller et redimensionnement automatique de la fenêtre virt-manager
    services.spice-vdagentd.enable = true;

    # ── Optimisations disque virtio ────────────────────────────────────────
    services.fstrim.enable = true;

    # ── Packages utiles en VM ──────────────────────────────────────────────
    environment.systemPackages = with pkgs; [
      spice-vdagent
    ];
  };
}
