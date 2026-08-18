{ config, pkgs, lib, modulesPath, roudix-installer, disko, roudixBranding, ... }:

{
  imports = [ ./branding.nix ];

  networking.hostName = "roudix-live";
  system.stateVersion = "26.11";

  # ── Boot menu ─────────────────────────────────────────────────────────────
  isoImage.appendToMenuLabel = " — Roudix Installer";

  # boot.loader.grub.theme s'applique au GRUB du système une fois installé
  # sur le disque, mais PAS au menu graphique EFI affiché au démarrage de
  # l'ISO elle-même : celui-là est piloté par isoImage.grubTheme, qui vaut
  # pkgs.nixos-grub2-theme par défaut (le thème avec la baguette magique
  # qu'on voit sur les captures — la preuve que notre thème custom n'était
  # jamais utilisé). On réutilise la même dérivation pour les deux.
  boot.loader.grub.theme = pkgs.runCommand "roudix-grub-theme" {} ''
    mkdir -p $out
    cp ${roudixBranding}/share/icons/hicolor/256x256/apps/roudix-logo.png $out/logo.png

    # IMPORTANT : le menu EFI de l'ISO ne charge une police que si elle est
    # trouvée À L'INTÉRIEUR du dossier du thème (voir iso-image.nix :
    # `find $\{grubTheme\} -iname '*.pf2' -printf "loadfont ..."`). Seule
    # l'entrée cachée "Text mode" charge unicode.pf2 par défaut — le mode
    # graphique avec thème, lui, n'aurait chargé AUCUNE police sans ça, et
    # le menu risquait d'afficher du texte invisible. unicode.pf2 couvre
    # aussi les accents (Français, etc.).
    cp ${pkgs.grub2}/share/grub/unicode.pf2 $out/unicode.pf2

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

  # Sans ceci, l'ISO ignore complètement notre thème et affiche le thème
  # par défaut de nixpkgs (pkgs.nixos-grub2-theme) au démarrage — c'est
  # ça qu'on voyait sur la capture d'écran.
  isoImage.grubTheme = config.boot.loader.grub.theme;

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
        # Même remarque que pour le wallpaper dans branding.nix : on passe
        # par programs.dconf.profiles.user.databases (et pas par un
        # environment.etc."dconf/db/..." à la main), car programs.dconf.
        # profiles.* revendique tout /etc/dconf comme un seul symlink vers
        # le store dès qu'il est utilisé quelque part (ici, dans le parent
        # branding.nix). Un fichier etc manuel sous ce même sous-arbre fait
        # planter etc.drv avec "mkdir: Permission denied" — c'était l'erreur
        # du run CI (Roudix-Installer-de). La liste "databases" se
        # concatène automatiquement avec celle du parent (inheritParentConfig),
        # donc pas besoin de lib.mkForce ici, contrairement à console.keyMap.
        programs.dconf.profiles.user.databases = [{
          settings = {
            "org/gnome/desktop/input-sources" = {
              sources = [ (lib.gvariant.mkTuple [ "xkb" kb.xkb ]) ];
            };
          };
        }];
        # programs.dconf.enable est déjà à true dans branding.nix (parent),
        # hérité automatiquement.
        # system.nixos.label n'accepte que [a-zA-Z0-9_.-] — pas d'espaces
        # ni de parenthèses, d'où le slug plutôt que kb.label directement.
        system.nixos.label = "Roudix-Installer-${name}";
      };
    }) keyboardLayouts;

  # ── Locale par défaut ─────────────────────────────────────────────────────
  time.timeZone = "Europe/Brussels";
  i18n.defaultLocale = "en_US.UTF-8";
  console.keyMap = "us";

  # ── Nix settings ─────────────────────────────────────────────────────────
  nix.settings = {
    experimental-features = [ "nix-command" "flakes" ];
    substituters = [
      "https://cache.nixos.org"
      "https://roudix.cachix.org"
      "https://noctalia.cachix.org"
      "https://nix-community.cachix.org"
      "https://nix-cache.tokidoki.dev/tokidoki"
      "https://nyx-cache.chaotic.cx/"
    ];
    trusted-public-keys = [
      "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
      "roudix.cachix.org-1:h5EnhsXw4Mr6pLUpZIalE8SlfH1kKXgvPFvl+yrTAaQ="
      "noctalia.cachix.org-1:pCOR47nnMEo5thcxNDtzWpOxNFQsBRglJzxWPp3dkU4="
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCUSeBw="
      "tokidoki:MD4VWt3kK8Fmz3jkiGoNRJIW31/QAm7l1Dcgz2Xa4hk="
      "nyx-cache.chaotic.cx:dJxTrgMC3V3cFfyIiBQDQorG6k1LsqurH/srpMSq7qk="
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
