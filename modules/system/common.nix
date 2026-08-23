{ pkgs, inputs, config, lib, username, ... }:
{
  # ── Nix settings ────────────────────────────────────────────────────────
  nix.settings = {
    trusted-users = [ "root" "${username}" ];
    experimental-features = [ "nix-command" "flakes" ];
    extra-substituters = [
      "https://attic.xuyh0120.win/lantian"
      "https://noctalia.cachix.org"
      "https://prismlauncher.cachix.org"
      "https://nix-community.cachix.org"
      "https://roudix.cachix.org"
      "https://nix-cache.tokidoki.dev/tokidoki"
      "https://nyx-cache.chaotic.cx/"
      "https://niri-epireyn.cachix.org"
      "https://hyprland.cachix.org"
    ];
    extra-trusted-public-keys = [
      "niri-epireyn.cachix.org-1:tlVyFN7CtsDT+ZcLPS+ekFWeT1X6X4OqvWqbBMyIzFA="
      "lantian:EeAUQ+W+6r7EtwnmYjeVwx5kOGEBpjlBfPlzGlTNvHc="
      "noctalia.cachix.org-1:pCOR47nnMEo5thcxNDtzWpOxNFQsBRglJzxWPp3dkU4="
      "prismlauncher.cachix.org-1:9/n/FGyABA2jLUVfY+DEp4hKds/rwO+SCOtbOkDzd+c="
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCUSeBw="
      "roudix.cachix.org-1:h5EnhsXw4Mr6pLUpZIalE8SlfH1kKXgvPFvl+yrTAaQ="
      "tokidoki:MD4VWt3kK8Fmz3jkiGoNRJIW31/QAm7l1Dcgz2Xa4hk="
      "nyx-cache.chaotic.cx:dJxTrgMC3V3cFfyIiBQDQorG6k1LsqurH/srpMSq7qk="
      "hyprland.cachix.org-1:a7pgxzMz7+chwVL3/pzj6jIBMioiJM7ypFP8PwtkuGc="
    ];
  };

  nixpkgs.config.allowUnfree = true;

  # Overlay du flake Hyprland : garde pkgs.hyprland cohérent avec
  # programs.hyprland.package partout où du code référence pkgs.hyprland
  # (ex: certains paquets nixpkgs qui le prennent en dépendance).
  # Les plugins Hyprland (borders-plus-plus, etc.) viennent eux du flake
  # hyprland-plugins dédié (cf. home/hyprland.nix), pas de
  # pkgs.hyprlandPlugins — l'input hyprland.follows dans hyprland-plugins
  # garantit la correspondance exacte de version.
  nixpkgs.overlays = [ inputs.hyprland.overlays.default ];

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
    nerd-fonts.lilex
    nerd-fonts.caskaydia-cove
    nerd-fonts.hack
    nerd-fonts.iosevka
    nerd-fonts.hurmit
    nerd-fonts.fantasque-sans-mono
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
    bibata-cursors
    efibootmgr
    pciutils
    dmidecode
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
    ffmpegthumbnailer
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
  programs.nix-ld.enable = true;
  programs.nix-ld.libraries = with pkgs; [
    stdenv.cc.cc.lib
    icu
    openssl
    zlib
    libGL
    fontconfig
    freetype
    libX11
    libXext
    libXrender
    libXrandr
    libXi
    libXcursor
    libXfixes
    libXcomposite
    libXdamage
    libXinerama
    libICE
    libSM
    libXtst
    libXxf86vm
    libxkbcommon
    dbus
    glib
  ];
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
  security.wrappers.pkexec = {
    enable = lib.mkForce true;
    owner  = "root";
    group  = "root";
    setuid = true;
    source = lib.getExe' config.security.polkit.package "pkexec";
  };

  system.stateVersion = "26.11";
}
