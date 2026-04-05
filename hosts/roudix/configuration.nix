{ pkgs, inputs, config, lib, username, ... }:
{
  imports = [
    ./hardware-configuration.nix
    ../../modules/common.nix
    ../../modules/desktop.nix
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

  # ── Desktop environment ──────────────────────────────────────────────────
  # Use 'roudix-switch <de>' to change — available: niri, gnome, kde
  roudix.desktop.type = "niri";

  # ── Hardware ────────────────────────────────────────────────────────────
  hardware.myGpu    = "amd";                   # "amd", "nvidia" or "intel"
  hardware.nvidiaOpen = false;                 # false for GTX 10xx/16xx, true for RTX 20xx+
  hardware.myCpu    = "intel";                 # "intel" or "amd"
  hardware.myKernel = "cachyos-latest-lto-v3"; # see README for all variants

  # ── Features ────────────────────────────────────────────────────────────
  roudix.gaming.enable        = true;
  roudix.fstrim.enable        = true;
  roudix.pipewire.enable      = true;
  roudix.virtualization.enable = true;
  roudix.vmGuest.enable       = true; # enable only inside a VM
  roudix.boot.enable          = true;
  roudix.hosts.gtaFix.enable  = true;

  # ── Network ─────────────────────────────────────────────────────────────
  networking.hostName = "roudix";

  # ── Disk configuration ───────────────────────────────────────────────────
  fileSystems."/mnt/gaming" = {
    device = "/dev/disk/by-uuid/b1f03b7d-59fc-4d29-aeb7-efbeae507860";
    fsType = "btrfs";
    options = [ "defaults" "nofail" ];
  };
}
