{ pkgs, inputs, config, lib, username, ... }:
{
  imports = [
    ../roudix/hardware-configuration.nix  # same machine, same hardware
    ../../modules/common.nix
    ../../modules/desktop-gnome.nix
    ../../modules/boot.nix
    ../../modules/kernel.nix
    ../../modules/gaming.nix
    ../../modules/gpu.nix
    ../../modules/cpu.nix
    ../../modules/pipewire.nix
    ../../modules/fstrim.nix
    ../../modules/virtualization.nix
    ../../modules/vm-guest.nix
    ../../modules/update.nix
    ../../modules/hosts-gta.nix
  ];

  # ── Hardware ────────────────────────────────────────────────────────────
  hardware.myGpu = "amd";          # "nvidia" or "intel" or "amd"
  hardware.nvidiaOpen = false;     # false for GTX 10xx/16xx, true for RTX 20xx+
  hardware.myCpu = "intel";        # "intel" or "amd"
  hardware.myKernel = "cachyos-latest-v3"; # "cachyos-latest", "cachyos-latest-v3", "cachyos-latest-lto", "cachyos-latest-lto-v3" "cachyos-rc"

  # ── Features ────────────────────────────────────────────────────────────
  roudix.gaming.enable = true;
  roudix.fstrim.enable = true;
  roudix.pipewire.enable = true;
  roudix.virtualization.enable = true;
  roudix.vmGuest.enable = true;
  roudix.boot.enable = true;
  roudix.hosts.gtaFix.enable = true;

  # ── Network ─────────────────────────────────────────────────────────────
  networking.hostName = "roudix";

  # ── Disk configuration ───────────────────────────────────────────────────
  fileSystems."/mnt/gaming" = {
    device = "/dev/disk/by-uuid/b1f03b7d-59fc-4d29-aeb7-efbeae507860";
    fsType = "btrfs";
    options = [ "defaults" "nofail" ];
  };

  #── Gnome excluded packages  ───────────────────────────────────────────────────
  gnome.excludePackages = with pkgs; [
          tali
          iagno
          hitori
          atomix
          yelp
          geary
          xterm
          totem

          epiphany
          packagekit

          gnome-tour
          gnome-software
          gnome-contacts
          gnome-user-docs
          gnome-packagekit
          gnome-font-viewer
          gnome-music

        ];
      };


}
