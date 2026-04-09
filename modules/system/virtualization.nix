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
    # Autorise virbr0 dans le firewall
    networking.firewall.trustedInterfaces = [ "virbr0" "br0" ];

    # Active le forwarding IP nécessaire pour le NAT des VMs
    boot.kernel.sysctl."net.ipv4.ip_forward" = 1;

    # Crée le réseau "default" s'il n'existe pas (NixOS ne le crée pas automatiquement)
    systemd.services.libvirtd.postStart = lib.mkForce ''
      sleep 2
      if ! ${pkgs.libvirt}/bin/virsh net-info default &>/dev/null; then
        ${pkgs.libvirt}/bin/virsh net-define ${pkgs.writeText "libvirt-default-network.xml" ''
          <network>
            <name>default</name>
            <forward mode="nat"/>
            <bridge name="virbr0" stp="on" delay="0"/>
            <ip address="192.168.122.1" netmask="255.255.255.0">
              <dhcp>
                <range start="192.168.122.2" end="192.168.122.254"/>
              </dhcp>
            </ip>
          </network>
        ''}
        ${pkgs.libvirt}/bin/virsh net-autostart default
        ${pkgs.libvirt}/bin/virsh net-start default
      fi
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
