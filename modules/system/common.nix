{ pkgs, inputs, config, lib, username, ... }:
{
  # ── Nix settings ────────────────────────────────────────────────────────
  nix.settings = {
    trusted-users = [ "root" "${username}" ];
    experimental-features = [ "nix-command" "flakes" ];
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

  # ── OS release ──────────────────────────────────────────────────────────
  environment.etc."os-release".text = lib.mkForce ''
    NAME="Roudix"
    ID=nixos
    VERSION="${config.system.nixos.version}"
    VERSION_CODENAME="${config.system.nixos.codeName}"
    PRETTY_NAME="Roudix ${config.system.nixos.version}"
    HOME_URL="https://nixos.org/"
  '';

  # ── Kernel ──────────────────────────────────────────────────────────────
  boot.kernelModules = [ "ntsync" ];
  boot.kernelParams = [ "zswap.enabled=0" ];
  boot.kernel.sysctl = {
    "vm.swappiness" = 150;
    "vm.watermark_boost_factor" = 0;
    "vm.watermark_scale_factor" = 125;
  };

  # ── Network ─────────────────────────────────────────────────────────────
  networking.networkmanager.enable = true;
  networking.useDHCP = false;
  networking.nameservers = [ "1.1.1.1" "8.8.8.8" ];

  # ── Locale / timezone ───────────────────────────────────────────────────
  time.timeZone = lib.mkDefault "Europe/Brussels";
  environment.sessionVariables = {
    TZ = lib.mkDefault "Europe/Brussels";
    TZDIR = "/etc/zoneinfo";
    NH_FLAKE = "/home/${username}/.config/roudix";
  };
  i18n.defaultLocale = lib.mkDefault "en_US.UTF-8";
  console.keyMap = lib.mkDefault "us-accentos";

  # ── Fonts ───────────────────────────────────────────────────────────────
  fonts.packages = with pkgs; [
    nerd-fonts.jetbrains-mono
    nerd-fonts.noto
    noto-fonts
    noto-fonts-color-emoji
    nerd-fonts.iosevka
    nerd-fonts.hurmit
  ];

  # ── User ────────────────────────────────────────────────────────────────
  users.users.${username} = {
    isNormalUser = true;
    extraGroups = [ "wheel" "video" "audio" "input" "networkmanager" "plugdev" "disk" "storage" "i2c" "bluetooth" "render" ];
    shell = pkgs.fish;
  };

  # ── System packages ─────────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    git wget curl
    yazi
    capitaine-cursors
    efibootmgr
  ];

  # ── ZRAM ────────────────────────────────────────────────────────────────
  zramSwap = {
    enable = true;
    algorithm = "zstd";
    memoryPercent = 100;
    priority = 100;
  };

  # ── Programs ────────────────────────────────────────────────────────────
  programs.fish.enable = true;

  # ── Services ────────────────────────────────────────────────────────────
  services.udev.packages = [ pkgs.openrgb ];
  services.udisks2.enable = true;
  services.power-profiles-daemon.enable = true;
  services.upower.enable = true;
  services.hardware.openrgb.enable = true;
  hardware.i2c.enable = true;
  services.gvfs.enable = true;
  hardware.bluetooth.enable = true;
  hardware.bluetooth.powerOnBoot = true;
  services.blueman.enable = true;
  networking.firewall.enable = true;
  networking.firewall.checkReversePath = false;
  networking.firewall.allowedTCPPorts = [ 443 ];
  security.polkit.enable = true;

  system.stateVersion = "25.11";
}
