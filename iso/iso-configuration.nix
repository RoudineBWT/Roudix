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

  # ── Bureau / display manager : fourni par installation-cd-graphical-calamares-gnome.nix ──

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
    calamares
    calamares-nixos-extensions  # patché via overlay : module nixos + branding roudix
                                 # doit être installé À CÔTÉ de calamares pour que
                                 # /run/current-system/sw fusionne les deux lib/calamares/modules

    python3
    xdg-user-dirs

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
      target = "/iso-cfg";
    }
  ];

  image.fileName     = "roudix.iso";
  isoImage.volumeID  = "ROUDIX";

  # ── Script post-install : clone le repo dans ~/.config/roudix ────────────
  # ── Branche /etc/calamares/settings.conf vers notre settings.conf patché ──
  # calamares (le binaire) cherche son settings.conf dans son PROPRE /etc en
  # priorité ; comme c'est un store path read-only différent de celui de
  # calamares-nixos-extensions, on force NixOS à fusionner /etc/calamares/
  # vers notre version Roudix patchée.
  environment.etc."calamares/settings.conf".source =
    "${pkgs.calamares-nixos-extensions}/etc/calamares/settings.conf";
  environment.etc."calamares/modules".source =
    "${pkgs.calamares-nixos-extensions}/etc/calamares/modules";

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
