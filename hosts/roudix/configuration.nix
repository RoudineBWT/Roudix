{ pkgs, inputs, config, lib, username, ... }:
{
  imports = [
    ./hardware-configuration.nix
    (if builtins.pathExists ./local.nix then ./local.nix else { })
    ../../modules/binary-caches.nix
    ../../modules/autoupdate.nix
    ../../modules/common.nix
    ../../modules/desktop
    ../../modules/environment.nix
    ../../modules/chromium.nix
    ../../modules/boot.nix
    ../../modules/kernel.nix
    ../../modules/gaming.nix
    ../../modules/flatpak.nix
    ../../modules/gpu.nix
    ../../modules/cpu.nix
    ../../modules/pipewire.nix
    ../../modules/fstrim.nix
    ../../modules/virtualization.nix
    ../../modules/vm-guest.nix
    ../../modules/update.nix
    ../../modules/hosts-gta.nix
  ];

  # ── Choose your favorite chromium base browser ──────────────────────────────────────────────────
  roudix.chromium = lib.mkDefault "helium"; # brave or helium or vivaldi

  # ── Hardware ────────────────────────────────────────────────────────────
  hardware.myGpu    = lib.mkDefault "amd";                   # "amd", "nvidia" or "intel"
  hardware.myCpu    = lib.mkDefault "intel";                 # "intel" or "amd"
  hardware.myKernel = lib.mkDefault "cachyos-lts-lto-v3"; # see README for all variants

  # ── Features ────────────────────────────────────────────────────────────
  roudix.gaming.enable        = lib.mkDefault true;
  roudix.flatpak.enable       = lib.mkDefault false;
  roudix.fstrim.enable        = lib.mkDefault true;
  roudix.virtualization.enable = lib.mkDefault false;
  roudix.vmGuest.enable       = lib.mkDefault false; # enable only inside a VM
  roudix.hosts.gtaFix.enable  = lib.mkDefault false;
  roudix.autoupdate.enable = lib.mkDefault true;

  # ── Network ─────────────────────────────────────────────────────────────
  networking.hostName = "roudix";

  # ── Disk configuration ───────────────────────────────────────────────────
  fileSystems."/mnt/gaming" = {
    device = "/dev/disk/by-uuid/b1f03b7d-59fc-4d29-aeb7-efbeae507860";
    fsType = "btrfs";
    options = [ "defaults" "nofail" ];
  };
}
