{ pkgs, inputs, config, lib, username, ... }:
{
  imports = [
    ./hardware-configuration.nix
    ../../modules/system/binary-caches.nix
    ../../modules/system/shell.nix
    ../../modules/system/autoupdate.nix
    ../../modules/system/common.nix
    ../../modules/system/desktop
    ../../modules/system/environment.nix
    ../../modules/system/chromium.nix
    ../../modules/system/boot.nix
    ../../modules/system/kernel.nix
    ../../modules/system/gaming.nix
    ../../modules/system/flatpak.nix
    ../../modules/system/gpu.nix
    ../../modules/system/cpu.nix
    ../../modules/system/pipewire.nix
    ../../modules/system/fstrim.nix
    ../../modules/system/virtualization.nix
    ../../modules/system/vm-guest.nix
    ../../modules/system/update.nix
    ../../modules/system/hosts-gta.nix
  ] ++ lib.optional (builtins.pathExists ./local.nix) ./local.nix;

  # ── Choose your favorite chromium base browser ───────────────────────────
  roudix.chromium = lib.mkDefault "helium"; # brave or helium or vivaldi

  # ── Hardware ────────────────────────────────────────────────────────────
  hardware.myGpu    = lib.mkDefault "amd";              # "amd", "nvidia" or "intel"
  hardware.myCpu    = lib.mkDefault "intel";            # "intel" or "amd"
  hardware.myKernel = lib.mkDefault "cachyos-lts-lto-v3"; # see README for all variants

  # ── Features ────────────────────────────────────────────────────────────
  roudix.gaming.enable         = lib.mkDefault true;
  roudix.flatpak.enable        = lib.mkDefault false;
  roudix.fstrim.enable         = lib.mkDefault true;
  roudix.virtualization.enable = lib.mkDefault false;
  roudix.vmGuest.enable        = lib.mkDefault false; # enable only inside a VM
  roudix.hosts.gtaFix.enable   = lib.mkDefault false;
  roudix.autoupdate.enable     = lib.mkDefault true;

  # ── Network ─────────────────────────────────────────────────────────────
  networking.hostName = "roudix";

  # ── Disk configuration ───────────────────────────────────────────────────
  fileSystems."/mnt/gaming" = {
    device = "/dev/disk/by-uuid/b1f03b7d-59fc-4d29-aeb7-efbeae507860";
    fsType = "btrfs";
    options = [ "defaults" "nofail" ];
  };
}
