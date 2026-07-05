{ pkgs, lib, modulesPath, roudix-installer, disko, roudixBranding, ... }:

{
  imports = [ ./branding.nix ];

  networking.hostName = "roudix-live";
  system.stateVersion = "26.11";

  # ── Boot menu ─────────────────────────────────────────────────────────────
  isoImage.appendToMenuLabel = " — Roudix Installer";

  boot.loader.grub.theme = pkgs.runCommand "roudix-grub-theme" {} ''
    mkdir -p $out
    cp ${roudixBranding}/share/icons/hicolor/256x256/apps/roudix-logo.png $out/logo.png
    cat > $out/theme.txt <<'THEMEEOF'
    desktop-color: "#1e1e2e"
    title-text: ""

    + image {
        top = 6%
        left = 50%-100
        width = 200
        height = 200
        file = "logo.png"
    }

    + boot_menu {
        left = 15%
        top = 42%
        width = 70%
        height = 48%
        item_color = "#cdd6f4"
        selected_item_color = "#fab387"
        item_height = 32
        item_padding = 4
        item_spacing = 6
    }
    THEMEEOF
  '';

  # ── Entrées de boot par disposition clavier (façon GLF-OS) ────────────────
  # Chaque specialisation = une entrée de menu séparée, générée automatiquement
  # par NixOS (pas de grub.cfg écrit à la main). Couvre le clavier console
  # (TTY) ET la disposition GNOME par défaut de la session live.
  specialisation =
    let
      keyboardLayouts = {
        us = { keymap = "us"; xkb = "us"; label = "QWERTY (English)"; };
        be = { keymap = "be-latin1"; xkb = "be"; label = "AZERTY (Belge)"; };
        fr = { keymap = "fr"; xkb = "fr"; label = "AZERTY (Français)"; };
        de = { keymap = "de"; xkb = "de"; label = "QWERTZ (Deutsch)"; };
        ch = { keymap = "ch"; xkb = "ch"; label = "QWERTZ (Suisse)"; };
        uk = { keymap = "uk"; xkb = "gb"; label = "QWERTY (British)"; };
      };
    in
    lib.mapAttrs (name: kb: {
      inheritParentConfig = true;
      configuration = {
        console.keyMap = lib.mkForce kb.keymap;
        services.xserver.xkb.layout = lib.mkForce kb.xkb;
        environment.etc."dconf/db/local.d/01-roudix-keyboard".text = ''
          [org/gnome/desktop/input-sources]
          sources=[('xkb', '${kb.xkb}')]
        '';
        # programs.dconf.enable est déjà à true dans branding.nix (parent),
        # hérité automatiquement — le redéfinir ici risquerait le même
        # conflit de définitions que console.keyMap plus haut.
        # system.nixos.label n'accepte que [a-zA-Z0-9_.-] — pas d'espaces
        # ni de parenthèses, d'où le slug plutôt que kb.label directement.
        system.nixos.label = "Roudix-Installer-${name}";
      };
    }) keyboardLayouts;

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

  # ── Bureau / display manager : GDM+GNOME de base fourni par
  # installation-cd-graphical-gnome.nix, personnalisé par le vrai module
  # modules/system/desktop/gnome.nix (importé via branding.nix ci-dessus).

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
