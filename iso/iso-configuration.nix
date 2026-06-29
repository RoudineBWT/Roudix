{ pkgs, lib, modulesPath, ... }:

{
  # ── Branding ─────────────────────────────────────────────────────────────
  networking.hostName = "roudix-live";
  system.stateVersion = "26.11";

  # ── Locale par défaut (GeoIP override ça dans Calamares) ─────────────────
  time.timeZone = "Europe/Brussels";
  i18n.defaultLocale = "fr_BE.UTF-8";
  console.keyMap = "be-latin1";

  # ── Nix settings ─────────────────────────────────────────────────────────
  nix.settings = {
    experimental-features = [ "nix-command" "flakes" ];
    # Tous les caches Roudix pour que nixos-install soit rapide
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
    # Permettre à nixos-install de tourner sans sandbox depuis la live
    sandbox = false;
  };

  # ── Autologin sur la live ─────────────────────────────────────────────────
  services.displayManager.autoLogin.enable = true;
  services.displayManager.autoLogin.user = "nixos";

  # ── Packages disponibles sur la live ─────────────────────────────────────
  environment.systemPackages = with pkgs; [
    # Outils d'installation
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
    pciutils       # lspci — détection GPU dans nixos.py
    usbutils
    dmidecode

    # Nix
    nixos-install-tools

    # Calamares deps
    python3
    xdg-user-dirs

    # Utilitaires live utiles
    vim
    htop
    networkmanagerapplet
  ];

  # ── Embarquer le flake Roudix dans l'ISO ─────────────────────────────────
  # Le workflow rsync copie le repo principal dans iso/roudix-cfg/ au build time.
  # Calamares copiera /iso/iso-cfg/ vers /mnt/etc/nixos/ puis lancera :
  #   nixos-install --flake /mnt/etc/nixos#roudix
  isoImage.contents = [
    {
      source = ./roudix-cfg;
      target = "/iso/iso-cfg";
    }
  ];

  isoImage.isoName   = "roudix.iso";
  isoImage.volumeID  = "ROUDIX";

  # ── Config Calamares ──────────────────────────────────────────────────────
  # nixos.py est un module Python custom — il doit être dans un dossier
  # "nixos" avec un descripteur module.desc pour que Calamares le charge.
  environment.etc = {
    # Settings principal
    "calamares/settings.conf".source = ./calamares/settings.conf;

    # Modules de config
    "calamares/modules/nixos.conf".source        = ./calamares/modules/nixos.conf;
    "calamares/modules/users.conf".source        = ./calamares/modules/users.conf;
    "calamares/modules/locale.conf".source       = ./calamares/modules/locale.conf;
    "calamares/modules/welcome.conf".source      = ./calamares/modules/welcome.conf;
    "calamares/modules/packagechooser-desktop.conf".source = ./calamares/modules/packagechooser-desktop.conf;
    "calamares/modules/packagechooser-shell.conf".source   = ./calamares/modules/packagechooser-shell.conf;
    "calamares/modules/packagechooser-kernel.conf".source  = ./calamares/modules/packagechooser-kernel.conf;
    "calamares/modules/packagechooser-browser.conf".source = ./calamares/modules/packagechooser-browser.conf;

    # Module Python custom nixos — Calamares cherche le .py dans un sous-dossier
    # portant le nom du module, avec un module.desc dedans.
    "calamares/modules/nixos/main.py".source     = ./calamares/modules/nixos.py;
    "calamares/modules/nixos/module.desc".text   = ''
      ---
      type: "job"
      name: "nixos"
      interface: "python"
      script: "main.py"
    '';
  };

  # ── Script post-install : clone le repo dans ~/.config/roudix ────────────
  # NH_FLAKE dans common.nix pointe vers /home/<user>/.config/roudix
  # Ce script est embarqué dans l'ISO et lancé par Calamares en fin d'install
  # via un module shellprocess (à ajouter dans settings.conf si besoin).
  environment.etc."calamares/scripts/post-install.sh" = {
    mode = "0755";
    text = ''
      #!/usr/bin/env bash
      # Appelé après nixos-install pour cloner le flake Roudix
      # dans le home de l'utilisateur (pour que nh os switch fonctionne).
      set -euo pipefail

      ROOT="$1"        # rootMountPoint passé par Calamares
      USERNAME="$2"    # username passé par nixos.py

      HOME_DIR="$ROOT/home/$USERNAME"
      CONFIG_DIR="$HOME_DIR/.config/roudix"

      if [ ! -d "$CONFIG_DIR" ]; then
        mkdir -p "$CONFIG_DIR"
        cp -r /iso/iso-cfg/. "$CONFIG_DIR/"
        chown -R 1000:1000 "$CONFIG_DIR"
        echo "Roudix config copié dans $CONFIG_DIR"
      fi
    '';
  };
}
