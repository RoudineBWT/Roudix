{ pkgs, inputs, config, lib, username, ... }:
{
  imports = [
    ./hardware-configuration.nix
    ./modules/gaming.nix
    ./modules/gpu.nix
    ./modules/cpu.nix
    ./modules/pipewire.nix
    ./modules/fstrim.nix
    ./modules/virtualization.nix
  ];

  # ── Configuration ──────────────────────────────────────────────────────────
  hardware.myGpu = "amd";          # "nvidia" or "intel" or "amd"
  hardware.myCpu = "intel";        # "intel" or "amd"
  roudix.gaming.enable = true;     # enable (true) or disable (false) the config
  roudix.fstrim.enable = true;     # enable (true) or disable (false) the config
  roudix.pipewire.enable = true;   # enable (true) or disable (false) the config
  roudix.virtualization.enable = true; # enable (true) or disable (false) the config

  # ── Bootloader ──────────────────────────────────────────────────────────
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;
  boot.loader.systemd-boot.configurationLimit = 3;

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
    trusted-users = [ "root" "${username}" ];
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
  boot.kernelModules = [ "ntsync" ];
  nixpkgs.overlays = [ inputs.nix-cachyos-kernel.overlays.pinned ];

  boot.kernelPackages = pkgs.linuxKernel.packagesFor
    pkgs.cachyosKernels.linux-cachyos-latest-x86_64-v3;

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
  environment.sessionVariables = {
    TZ = "Europe/Brussels";
    TZDIR = "/etc/zoneinfo";
    FLAKE = "/home/${username}/.config/roudix";
  };
  i18n.defaultLocale = "en_US.UTF-8";
  console.keyMap = "us";

  # ── Disk configuration ───────────────────────────────────────────────────
  fileSystems."/mnt/gaming" = {
    device = "/dev/disk/by-uuid/b1f03b7d-59fc-4d29-aeb7-efbeae507860";
    fsType = "btrfs";
    options = [ "defaults" "nofail" ];
  };

  # ── Graphique / Wayland ─────────────────────────────────────────────────
  xdg.portal = {
    enable = true;
    extraPortals = [
      pkgs.xdg-desktop-portal-gnome
      pkgs.xdg-desktop-portal-gtk
    ];
    config.common.default = "*";
  };

  # ── Polkit ──────────────────────────────────────────────────────────────
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

  # ── Fonts ───────────────────────────────────────────────────────────────
  fonts.packages = with pkgs; [
    nerd-fonts.jetbrains-mono
    nerd-fonts.noto
    noto-fonts
    noto-fonts-color-emoji
    nerd-fonts.iosevka
    nerd-fonts.hurmit
  ];

  # ── Utilisateur ─────────────────────────────────────────────────────────
  users.users.${username} = {
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

  # ── ZRAM (config CachyOS) ────────────────────────────────────────────────
  zramSwap = {
    enable = true;
    algorithm = "zstd";
    memoryPercent = 100;
    priority = 100;
  };

  boot.kernelParams = [ "zswap.enabled=0" ];

  boot.kernel.sysctl = {
    "vm.swappiness" = 150;
    "vm.watermark_boost_factor" = 0;
    "vm.watermark_scale_factor" = 125;
  };

  # ── CleanUP ─────────────────────────────────────────────────────────────
  nix.gc = {
    automatic = true;
    dates = "weekly";
    options = "--delete-older-than 7d";
  };

  # ── Programs ────────────────────────────────────────────────────────────
  programs.fish.enable = true;

  # ── Greeter ─────────────────────────────────────────────────────────────
  services.displayManager.gdm.enable = true;

  # ── Services ────────────────────────────────────────────────────────────
  services.udev.packages = [ pkgs.openrgb ];
  services.udisks2.enable = true;
  services.power-profiles-daemon.enable = true;
  services.upower.enable = true;
  services.hardware.openrgb.enable = true;
  hardware.i2c.enable = true;
  services.gvfs.enable = true;
  services.flatpak.enable = true;

  # ── Flatpak Update auto ──────────────────────────────────────────────────
  systemd.services.flatpak-update = {
    description = "Update Flatpak apps";
    serviceConfig.ExecStart = "${pkgs.flatpak}/bin/flatpak update --noninteractive";
    wantedBy = [ "multi-user.target" ];
  };

  systemd.timers.flatpak-update = {
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "daily";
      Persistent = true;
    };
  };

  system.stateVersion = "25.11";
}
