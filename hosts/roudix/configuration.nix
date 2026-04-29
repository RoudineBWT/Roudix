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
    ../../modules/system/browser.nix
    ../../modules/system/boot.nix
    ../../modules/system/kernel.nix
    ../../modules/system/gaming.nix
    ../../modules/system/scx.nix
    ../../modules/system/flatpak.nix
    ../../modules/system/gpu.nix
    ../../modules/system/cpu.nix
    ../../modules/system/pipewire.nix
    ../../modules/system/fstrim.nix
    ../../modules/system/virtualization.nix
    ../../modules/system/vm-guest.nix
    ../../modules/system/update.nix
    ../../modules/system/hosts-gta.nix
     inputs.brave-previews.nixosModules.default
  ] ++ lib.optional (builtins.pathExists ./local.nix) ./local.nix;

  # ── Choose your favorite chromium base browser ───────────────────────────
  roudix.browsers = lib.mkDefault ["helium"]; # brave or helium or vivaldi

  # ── Hardware ────────────────────────────────────────────────────────────
  hardware.myGpu    = lib.mkDefault "amd";              # "amd", "nvidia" or "intel"
  hardware.myCpu    = lib.mkDefault "intel";            # "intel" or "amd"
  hardware.myKernel = lib.mkDefault "cachyos-lts-lto-v3"; # see README for all variants
  roudix.rgb        = lib.mkDefault "none";           # "openlinkhub" (full Corsair), "openrgb" (mixed/other brands) or "none"
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
}
