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
    # Imported for its OPTIONS only (roudix.gaming.*, which the home-manager
    # side and the installer's local.nix read) — roudix.gaming.enable is
    # false below, so no Steam/Gamescope/Wine/scx lands on this machine.
    # Only Heroic is installed (roudix.gaming.apps.heroic.enable below).
    ../../modules/system/gaming
    # Deliberately NOT imported on this host (family laptop, no RGB, no VMs
    # — keeps the closure smaller and avoids modules that need attention no
    # one on this machine will give them):
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
  # Cinnamon: classic desktop layout for a non-technical user, and an X11
  # session for older PCs (GNOME 49 is Wayland-only). Back to GNOME: set
  # roudix.desktop.type = "gnome" in hosts/nixie/local.nix.
  roudix.desktop.type           = lib.mkDefault "cinnamon";
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

  # ── Apps: nothing installed by default that nobody asked for ─────────────
  # These two default to ON in their modules (Spotify + Spicetify, OBS +
  # v4l2loopback), so they must be switched off explicitly here.
  roudix.musicPlayer             = lib.mkDefault "none";
  roudix.contentCreation.enable  = lib.mkDefault false;

  # ── Gaming: Heroic only ──────────────────────────────────────────────────
  # roudix.gaming.enable is the "full gaming" switch (Steam, Gamescope,
  # Wine, Proton, scx...). Off here; the launchers are individually opt-in
  # when it's off (their defaults follow roudix.gaming.enable).
  roudix.gaming.enable           = lib.mkDefault false;
  roudix.gaming.apps.heroic.enable = lib.mkDefault true;

  # ── Network ───────────────────────────────────────────────────────────────
  networking.hostName = "nixie";
}
