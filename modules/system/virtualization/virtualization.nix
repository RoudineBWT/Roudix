{ config, lib, pkgs, username, ... }:
{
  options.roudix.virtualization.enable = lib.mkOption {
    description = "Enable Roudix virtualization configurations (QEMU/KVM)";
    type = lib.types.bool;
    default = false;
  };

  options.roudix.virtualization.vmCurator.enable = lib.mkOption {
    description = ''
      Enable vm-curator, a Rust TUI alternative to virt-manager for
      managing desktop QEMU/KVM VMs (no libvirt, works directly on
      launch.sh scripts, 3D accel via virtio-vga-gl, GPU passthrough).
      Independent of `roudix.virtualization.enable`: can be used with
      or without the libvirt stack. Available as `pkgs.vm-curator` on
      nixos-unstable.
    '';
    type = lib.types.bool;
    default = false;
  };

  config = lib.mkMerge [
    (lib.mkIf config.roudix.virtualization.vmCurator.enable (lib.mkMerge [
      {
        environment.systemPackages = with pkgs; [
          vm-curator
        ] ++ lib.optionals (!config.roudix.virtualization.enable) [
          # vm-curator drives QEMU directly, it doesn't need libvirtd,
          # but it does need qemu/qemu-img itself present on the system.
          qemu_kvm
        ];
      }

      (lib.mkIf (!config.roudix.virtualization.enable) {
        # The libvirt branch below already covers all of this — only needed
        # when running vm-curator standalone, without the libvirt stack.

        # /dev/kvm access
        users.users.${username}.extraGroups = [ "kvm" ];

        # 3D acceleration for vm-curator's virtio-vga-gl para-virtualized display
        hardware.graphics.enable = true;
        hardware.graphics.extraPackages = with pkgs; [ virglrenderer ];
      })
    ]))

    (lib.mkIf config.roudix.virtualization.enable {
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
      # Allows virbr0 in the firewall
      networking.firewall.trustedInterfaces = [ "virbr0" "br0" ];

      # Enables the IP forwarding needed for VM NAT
      boot.kernel.sysctl."net.ipv4.ip_forward" = 1;

      # Creates the "default" network if it doesn't exist (NixOS doesn't create it automatically)
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
        #virtio-win
      ];
    })
  ];
}
