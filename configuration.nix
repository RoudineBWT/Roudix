{ pkgs, inputs, config, lib, ... }:
{
  imports = [ ./hardware-configuration.nix ./gaming.nix];

  # ── Bootloader ──────────────────────────────────────────────────────────
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

  # ── Roudix ──────────────────────────────────────────────────────
  environment.etc."os-release".text = lib.mkForce ''
    NAME="Roudix"
    ID=nixos
    VERSION="${config.system.nixos.version}"
    VERSION_CODENAME="${config.system.nixos.codeName}"
    PRETTY_NAME="Roudix ${config.system.nixos.version}"
    HOME_URL="https://nixos.org/"
  '';

  # ── Kernel CachyOS ──────────────────────────────────────────────────────
nix.settings = {
  trusted-users = [ "root" "roudine" ];
  substituters = [
    "https://cache.nixos.org"
    "https://attic.xuyh0120.win/lantian"
    "https://cache.garnix.io"
  ];
  trusted-public-keys = [
    "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
    "lantian:EeAUQ+W+6r7EtwnmYjeVwx5kOGEBpjlBfPlzGlTNvHc="
    "cache.garnix.io:CTFPyKSLcx5RMJKfLo5EEPUObbA78b0YQ2DTCJXqr9g="
  ];
};

  nixpkgs.config.allowUnfree = true;
  hardware.cpu.intel.updateMicrocode = true;
  boot.kernelModules = [ "ntsync" ];
  nixpkgs.overlays = [ inputs.nix-cachyos-kernel.overlays.pinned ];

  boot.kernelPackages = pkgs.linuxKernel.packagesFor
    pkgs.cachyosKernels.linux-cachyos-latest;
  # Variante LTO (Clang+ThinLTO, compile plus long mais plus rapide) :
  # pkgs.cachyosKernels.linux-cachyos-latest-lto

  # ── Nix ─────────────────────────────────────────────────────────────────
  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  # ── Réseau ──────────────────────────────────────────────────────────────
  networking.hostName = "roudix";
  networking.networkmanager.enable = true;
  networking.extraHosts = ''
    127.0.0.1 paradise-s1.battleye.com
    127.0.0.1 test-s1.battleye.com
    127.0.0.1 paradiseenhanced-s1.battleye.com
  '';

  # ── Locale / timezone ───────────────────────────────────────────────────
  time.timeZone = "Europe/Brussels";
  environment.variables = {
    TZ = "Europe/Brussels"; # Mangohud needs it
    TZDIR = "/etc/zoneinfo";
  };
  i18n.defaultLocale = "en_US.UTF-8";
  console.keyMap = "us";          # layout us intl comme dans ta config niri

  # ── Son ─────────────────────────────────────────────────────────────────
  services.pipewire = {
    enable = true;
    alsa.enable = true;
    pulse.enable = true;
    wireplumber.enable = true;
  };
  # ── Disk configuration ─────────────────────────────────────────────────────────────────
  fileSystems."/mnt/gaming" = {
    device = "/dev/disk/by-uuid/b1f03b7d-59fc-4d29-aeb7-efbeae507860";
    fsType = "btrfs";  # ou ntfs, btrfs, exfat...
    options = [ "defaults" "nofail" ];  # nofail = boot même si le disque est absent
  };

  # ── Graphique / Wayland ─────────────────────────────────────────────────
   # XDG portals (obligatoire pour Niri + Nautilus)
  xdg.portal = {
    enable = true;
    extraPortals = [
      pkgs.xdg-desktop-portal-gnome
      pkgs.xdg-desktop-portal-gtk
    ];
    config.common.default = "*";
  };

  # ── Polkit ──────────────────────────────────────────────────────────────
  # spawn-at-startup pointe vers polkit-gnome dans ta config
  security.polkit.enable = true;
  systemd.user.services.polkit-gnome = {
    description = "GNOME Polkit authentication agent";
    wantedBy = [ "graphical-session.target" ];
    after = [ "graphical-session.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
      Restart = "on-failure";
    };
  };

  # ── Fonts (Nerd Fonts pour les icônes des workspaces) ───────────────────
  fonts.packages = with pkgs; [
    nerd-fonts.jetbrains-mono
    nerd-fonts.noto
    noto-fonts
    noto-fonts-color-emoji
    nerd-fonts.iosevka
  ];

  # ── Utilisateur ─────────────────────────────────────────────────────────
  users.users.roudine = {
    isNormalUser = true;
    extraGroups = [ "wheel" "video" "audio" "input" "networkmanager" "plugdev" "disk" "storage" "i2c" ];
    shell = pkgs.fish;
  };

  # ── Paquets système ─────────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    git wget curl
    polkit_gnome
    yazi
    capitaine-cursors
  ];

# ── ZRAM (config CachyOS) ─────────────────────────────────────────────────
zramSwap = {
  enable = true;
  algorithm = "zstd";
  memoryPercent = 100; # même taille que la RAM
  priority = 100;
};

# Désactiver zswap (incompatible avec zram)
boot.kernelParams = [ "zswap.enabled=0" ];

# Swappiness à 150 comme CachyOS
boot.kernel.sysctl = {
  "vm.swappiness" = 150;
  "vm.watermark_boost_factor" = 0;
  "vm.watermark_scale_factor" = 125;
  };
 # ── CleanUP ────────────────────────────────────────────────────────────
  nix.gc = {
    automatic = true;
    dates = "weekly";
    options = "--delete-older-than 7d";
  };

  # ── Programs ────────────────────────────────────────────────────────────
  programs.fish.enable = true;

  # ── Services ────────────────────────────────────────────────────────────
  services.xserver.enable = true;
  services.displayManager.gdm.enable = true;
  services.udev.packages = [ pkgs.openrgb ];
  services.udisks2.enable = true;
  services.power-profiles-daemon.enable = true;
  services.upower.enable = true;
  services.hardware.openrgb.enable = true;
  services.hardware.openrgb.motherboard = "intel"; # ou "intel"
  hardware.i2c.enable = true;
  services.gvfs.enable = true;
  services.flatpak.enable = true;

  system.stateVersion = "25.05";
}
