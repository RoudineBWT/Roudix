{ pkgs, inputs, config, lib, username, ... }:
{
  # ── Nix settings ────────────────────────────────────────────────────────
  nix.settings = {
    trusted-users = [ "root" "${username}" ];
    experimental-features = [ "nix-command" "flakes" ];
    # Substituters / public keys live in ./binary-caches.nix (single copy; the
    # flake's nixConfig is the only other place, it has to be literal).

    # A dead or slow cache must not freeze a rebuild (CI already uses 3 s):
    # give up on it quickly and, if a path really is nowhere, build locally.
    # Trade-off: with a third-party cache down, an unattended auto-update
    # may compile locally — the "idle" scheduling below keeps that harmless.
    connect-timeout = 5;
    fallback = true;
    warn-dirty = false;
    # GC on the fly instead of dying with "No space left on device" in the
    # middle of a big build: below min-free, delete dead paths up to max-free.
    min-free = 1024 * 1024 * 1024;      # 1 GiB
    max-free = 5 * 1024 * 1024 * 1024;  # 5 GiB
  };

  # Builds run by the daemon (rebuild, unattended auto-update) only get the
  # CPU/disk nobody else wants: the desktop and games stay smooth.
  nix.daemonCPUSchedPolicy = "idle";
  nix.daemonIOSchedClass = "idle";
  nix.daemonIOSchedPriority = 7;

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
  # DNS comes from DHCP / VPN / the local resolver (Pi-hole...) through
  # systemd-resolved, like CachyOS. The public servers are only a fallback.
  networking.networkmanager.dns = "systemd-resolved";
  # Wi-Fi channels/power limits of the actual country (wireless-regdb).
  hardware.wirelessRegulatoryDatabase = true;
  services.resolved = {
    enable = true;
    settings.Resolve.FallbackDNS = [ "1.1.1.1" "9.9.9.9" ];
  };

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
    lshw
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
  # power-profiles-daemon has been replaced by tuned (Fedora's default
  # since F41). tuned-ppd (ppdSupport) provides the same D-Bus API, so
  # `powerprofilesctl` (used by game-performance) keeps working with no
  # change on the script's side.
  services.power-profiles-daemon.enable = false;
  services.tuned = {
    enable = true;
    ppdSupport = true;
    # Custom Roudix profile for gaming: based on throughput-performance
    # (performance governor + I/O/network tuning) WITHOUT
    # latency-performance's C-state locking, which could worsen the
    # already-suspected CPU instability (see SMT-related crashes).
    # Extension point for adding Roudix-specific tweaks later without
    # depending on a stock profile.
    profiles."roudix-gaming" = {
      main = {
        include = "throughput-performance";
      };
    };
    # The "performance" profile exposed via powerprofilesctl (and thus via
    # game-performance) points to our custom profile instead of
    # tuned-ppd's default (throughput-performance directly).
    ppdSettings.profiles = {
      "power-saver" = "powersave";
      balanced = "balanced";
      performance = "roudix-gaming";
    };
  };
  services.upower.enable = true;
  services.gvfs.enable = true;
  hardware.bluetooth.enable = true;
  hardware.bluetooth.powerOnBoot = true;
  services.blueman.enable = true;
  networking.firewall.enable = true;
  networking.firewall.checkReversePath = false;
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
