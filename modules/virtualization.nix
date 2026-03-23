{ config, lib, pkgs, username, ... }:
{
  options.roudix.virtualization.enable = lib.mkOption {
    description = "Enable Roudix virtualization configurations (QEMU/KVM)";
    type = lib.types.bool;
    default = false;
  };

  config = lib.mkIf config.roudix.virtualization.enable {
    # ── QEMU / KVM ───────────────────────────────────────────────────────────
    virtualisation.libvirtd = {
      enable = true;
      qemu = {
        package = pkgs.qemu_kvm;
        runAsRoot = false;
        swtpm.enable = true;
        verbatimConfig = ''
          user = "${username}"
          group = "users"
        '';
      };
    };

    # ── Server Spice ─────────────────────────────────────────────────────────
    virtualisation.spiceUSBRedirection.enable = true;
    hardware.graphics.enable = true;
    hardware.graphics.extraPackages = with pkgs; [ virglrenderer ];

    # ── Virt-Manager ─────────────────────────────────────────────────────────
    programs.virt-manager.enable = true;

    # ── Virtual Network ───────────────────────────────────────────────────────
    networking.firewall.trustedInterfaces = [ "virbr0" ];
    systemd.services.libvirtd.postStart = ''
      sleep 1
      ${pkgs.libvirt}/bin/virsh net-autostart default
      ${pkgs.libvirt}/bin/virsh net-start default || true
    '';

    # ── User groups ──────────────────────────────────────────────────────────
    users.users.${username}.extraGroups = [ "libvirtd" "kvm" ];

    # ── Packages ─────────────────────────────────────────────────────────────
    environment.systemPackages = with pkgs; [
      virt-viewer
      spice-gtk
      virtio-win
    ];
  };
}
