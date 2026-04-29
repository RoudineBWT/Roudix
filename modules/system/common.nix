{ pkgs, inputs, config, lib, username, ... }:
{
  imports = (
    if config.roudix.rgb == "openlinkhub" then [ ./openlinkhub.nix ]
    else if config.roudix.rgb == "openrgb"    then [ ./openrgb.nix ]
    else []
  );

  # ── Nix settings ────────────────────────────────────────────────────────
  nix.settings = {
    trusted-users = [ "root" "${username}" ];
    experimental-features = [ "nix-command" "flakes" ];
    extra-substituters = [
      "https://attic.xuyh0120.win/lantian"
      "https://cache.garnix.io"
      "https://noctalia.cachix.org"
      "https://prismlauncher.cachix.org"
      "https://nix-community.cachix.org"
      "http://37.59.123.5:8080/glf"
      "https://roudix.cachix.org"
    ];
    extra-trusted-public-keys = [
      "lantian:EeAUQ+W+6r7EtwnmYjeVwx5kOGEBpjlBfPlzGlTNvHc="
      "cache.garnix.io:CTFPyKSLcx5RMJKfLo5EEPUObbA78b0YQ2DTCJXqr9g="
      "noctalia.cachix.org-1:pCOR47nnMEo5thcxNDtzWpOxNFQsBRglJzxWPp3dkU4="
      "prismlauncher.cachix.org-1:9/n/FGyABA2jLUVfY+DEp4hKds/rwO+SCOtbOkDzd+c="
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCUSeBw="
      "glf:gLU8OSnfaopb5atQHiNJDgvS7/VbQ8HDQn3GOWT8w7Y="
      "roudix.cachix.org-1:h5EnhsXw4Mr6pLUpZIalE8SlfH1kKXgvPFvl+yrTAaQ="
    ];
  };

  nixpkgs.config.allowUnfree = true;

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
  console.keyMap = lib.mkDefault "us-acentos";

  # ── Fonts ───────────────────────────────────────────────────────────────
  fonts.packages = with pkgs; [
    nerd-fonts.jetbrains-mono
    nerd-fonts.noto
    noto-fonts
    noto-fonts-color-emoji
    # nerd-fonts.iosevka
    nerd-fonts.hurmit
  ];

  # ── User ────────────────────────────────────────────────────────────────
  users.users.${username} = {
    isNormalUser = true;
    extraGroups = [ "wheel" "video" "audio" "input" "networkmanager" "plugdev" "disk" "storage" "i2c" "bluetooth" "render" "greeter" ];
    shell = if config.roudix.shell == "bash" then pkgs.bash else pkgs.fish;
  };

  # ── System packages ─────────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    git wget curl
    yazi
    capitaine-cursors
    efibootmgr
    pciutils
    python3
    dust
    fd
    ripgrep
    bat
    jq
    unzip
    zip
    file
    lsof
    nmap
    dig
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
  services.udisks2.enable = true;
  services.power-profiles-daemon.enable = true;
  services.upower.enable = true;
  services.gvfs.enable = true;
  hardware.bluetooth.enable = true;
  hardware.bluetooth.powerOnBoot = true;
  services.blueman.enable = true;
  networking.firewall.enable = true;
  networking.firewall.checkReversePath = false;
  networking.firewall.allowedTCPPorts = [ 443 ];
  security.polkit.enable = true;

  system.stateVersion = "26.05";
}
