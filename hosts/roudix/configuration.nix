{ pkgs, inputs, config, lib, username, ... }:
{
  imports = [
    ./hardware-configuration.nix
    (if builtins.pathExists ./local.nix then ./local.nix else { })
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

  # ── Desktop environment ──────────────────────────────────────────────────
  # Use 'roudix-switch <de>' to change — available: niri, gnome, kde
  roudix.desktop.type = "niri";

  # ── Choose your favorite chromium base browser ──────────────────────────────────────────────────
  roudix.chromium = "helium"; # brave or helium or vivaldi

  # ── Hardware ────────────────────────────────────────────────────────────
  hardware.myGpu    = "amd";                   # "amd", "nvidia" or "intel"
  hardware.myCpu    = "intel";                 # "intel" or "amd"
  hardware.myKernel = "cachyos-lts-lto-v3"; # see README for all variants

  # ── Features ────────────────────────────────────────────────────────────
  roudix.gaming.enable        = true;
  roudix.flatpak.enable       = true;
  roudix.fstrim.enable        = true;
  roudix.virtualization.enable = true;
  roudix.vmGuest.enable       = true; # enable only inside a VM
  roudix.hosts.gtaFix.enable  = true;
  roudix.autoupdate.enable = true;

  # ── Network ─────────────────────────────────────────────────────────────
  networking.hostName = "roudix";

  # ── Disk configuration ───────────────────────────────────────────────────
  fileSystems."/mnt/gaming" = {
    device = "/dev/disk/by-uuid/b1f03b7d-59fc-4d29-aeb7-efbeae507860";
    fsType = "btrfs";
    options = [ "defaults" "nofail" ];
  };
}
