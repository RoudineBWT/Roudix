{ pkgs, inputs, config, lib, username, ... }:
{
  imports = [
    ./hardware-configuration.nix
    ../../modules/system/core
    ../../modules/system/nix
    ../../modules/system/desktop
    ../../modules/system/boot
    ../../modules/system/apps
    ../../modules/system/packaging
    ../../modules/system/gpu
    ../../modules/system/power
    ../../modules/system/audio
    # Deliberately NOT imported on this host (family laptop, not a gaming
    # box, no RGB, no VMs — keeps the closure smaller and avoids modules
    # that need attention no one on this machine will give them):
    ../../modules/system/gaming
    #   ../../modules/system/rgb
    #   ../../modules/system/virtualization
    inputs.brave-previews.nixosModules.default
  ] ++ lib.optional (builtins.pathExists ./local.nix) ./local.nix;

  # ── Browser ────────────────────────────────────────────────────────────
  roudix.browsers = lib.mkDefault ["helium"];

  # ── Hardware — ThinkPad L380: Intel-only (i3/i5-8250U, UHD 620) ────────
  hardware.myGpu    = lib.mkDefault "intel";
  hardware.myCpu    = lib.mkDefault "intel";
  hardware.myKernel = lib.mkDefault "cachyos-lts-lto-v3";

  # ── Features ─────────────────────────────────────────────────────────────
  # NOTE: gaming/, rgb/ and virtualization/ modules are not imported above,
  # so their options (roudix.gaming.*, roudix.virtualization.*, roudix.podman,
  # roudix.distrobox, roudix.vmGuest, roudix.waydroid, roudix.hosts.gtaFix,
  # roudix.rgb) don't exist in this config at all — nothing to set to false,
  # the features are simply absent.
  roudix.boot.bootloader       = lib.mkDefault "systemd-boot"; # simplest/safest choice, no need for limine's extras here
  roudix.terminal               = lib.mkDefault "ghostty";
  roudix.desktop.type           = lib.mkDefault "gnome"; # simplest DE to hand to a non-technical user
  roudix.flatpak.enable         = lib.mkDefault true;   # easy manual app installs for him, outside of what you maintain
  roudix.fstrim.enable          = lib.mkDefault true;

  # ── Laptop power (TLP) — L380 is explicitly supported, see
  # modules/system/power/laptop.nix ─────────────────────────────────────
  roudix.laptop.enable          = lib.mkDefault true;
  roudix.laptop.thinkpad        = lib.mkDefault true;

  # ── Hands-off updates: this is the whole point of this host ─────────────
  roudix.autoupdate.enable      = lib.mkDefault true;
  roudix.autoupdate.branch      = lib.mkDefault "main";
  # No roudix.autoupdate.flakeAttr: nh resolves the flake attribute from
  # networking.hostName below, which is why it must read "nixie".

  roudix.mesa.useGit             = lib.mkDefault false;
  roudix.matrixClient            = lib.mkDefault "none";

  # ── Network ───────────────────────────────────────────────────────────────
  networking.hostName = "nixie";
}
