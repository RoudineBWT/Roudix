{ pkgs, lib, modulesPath, roudix-installer, disko, ... }:

{
  imports = [ ./branding.nix ];

  networking.hostName = "roudix-live";
  system.stateVersion = "26.11";

  # ── Boot menu ─────────────────────────────────────────────────────────────
  isoImage.grubTheme = null;
  isoImage.appendToMenuLabel = " — Roudix Installer";

  # ── Locale par défaut ─────────────────────────────────────────────────────
  time.timeZone = "Europe/Brussels";
  i18n.defaultLocale = "fr_BE.UTF-8";
  console.keyMap = "be-latin1";

  # ── Nix settings ─────────────────────────────────────────────────────────
  nix.settings = {
    experimental-features = [ "nix-command" "flakes" ];
    substituters = [
      "https://cache.nixos.org"
      "https://roudix.cachix.org"
      "https://noctalia.cachix.org"
      "https://nix-community.cachix.org"
      "https://cache.garnix.io"
      "http://37.59.123.5:8080/glf"
      "https://nix-cache.tokidoki.dev/tokidoki"
    ];
    trusted-public-keys = [
      "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
      "roudix.cachix.org-1:h5EnhsXw4Mr6pLUpZIalE8SlfH1kKXgvPFvl+yrTAaQ="
      "noctalia.cachix.org-1:pCOR47nnMEo5thcxNDtzWpOxNFQsBRglJzxWPp3dkU4="
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCUSeBw="
      "cache.garnix.io:CTFPyKSLcx5RMJKfLo5EEPUObbA78b0YQ2DTCJXqr9g="
      "glf:gLU8OSnfaopb5atQHiNJDgvS7/VbQ8HDQn3GOWT8w7Y="
      "tokidoki:MD4VWt3kK8Fmz3jkiGoNRJIW31/QAm7l1Dcgz2Xa4hk="
    ];
    sandbox = false;
  };

  # ── Bureau / display manager : fourni par installation-cd-graphical-gnome.nix ──

  # ── Packages disponibles sur la live ─────────────────────────────────────
  environment.systemPackages = with pkgs; [
    git
    curl
    wget
    rsync
    parted
    gptfdisk
    cryptsetup
    dosfstools
    e2fsprogs
    btrfs-progs
    efibootmgr
    pciutils
    usbutils
    dmidecode

    nixos-install-tools
    roudix-installer.packages.${pkgs.system}.default
    disko.packages.${pkgs.system}.disko

    python3
    xdg-user-dirs

    vim
    htop
    networkmanagerapplet
  ];

  # ── Embarquer le flake Roudix dans l'ISO ─────────────────────────────────
  # Le workflow rsync copie le repo principal dans iso/roudix-cfg/ au build time.
  # roudix-installer copie /iso/iso-cfg/ vers /mnt/etc/nixos/ puis lance :
  #   nixos-install --flake /mnt/etc/nixos#roudix
  isoImage.contents = [
    {
      source = ./roudix-cfg;
      target = "/iso-cfg";
    }
  ];

  image.fileName     = "roudix.iso";
  isoImage.volumeID  = "ROUDIX";

  # ── Autostart de l'installeur ─────────────────────────────────────────────
  # roudix-installer a besoin de root pour disko/nixos-install. Le live user
  # ("nixos") est wheel + NOPASSWD + SETENV -> sudo --preserve-env transparent,
  # même mécanisme que ce qu'utilisait Calamares pour Wayland.
  environment.etc."xdg/autostart/roudix-installer.desktop".text = ''
    [Desktop Entry]
    Type=Application
    Version=1.0
    Name=Install Roudix
    GenericName=System Installer
    TryExec=roudix-installer
    Exec=sh -c "sudo --preserve-env=WAYLAND_DISPLAY,XDG_RUNTIME_DIR,DISPLAY roudix-installer"
    Comment=Roudix Installer
    Icon=roudix
    Terminal=false
    StartupNotify=true
    Categories=System;
    X-AppStream-Ignore=true
  '';
}
