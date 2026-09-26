{ config, pkgs, lib, modulesPath, roudix-installer, disko, roudixBranding, ... }:

{
  imports = [ ./branding.nix ];

  networking.hostName = "roudix-live";
  system.stateVersion = "26.11";

  # ── Boot menu ─────────────────────────────────────────────────────────────
  isoImage.appendToMenuLabel = " — Roudix Installer";

  # boot.loader.grub.theme applies to the installed system's GRUB, but
  # NOT to the graphical EFI menu shown when booting the ISO itself —
  # that one is driven by isoImage.grubTheme, which defaults to
  # pkgs.nixos-grub2-theme. Reuse the same derivation for both.
  boot.loader.grub.theme = pkgs.runCommand "roudix-grub-theme" {} ''
    mkdir -p $out
    cp ${roudixBranding}/share/icons/hicolor/256x256/apps/roudix-logo.png $out/logo.png

    # IMPORTANT: the ISO's EFI menu only loads a font if it's found
    # INSIDE the theme folder (see iso-image.nix's
    # `find $\{grubTheme\} -iname '*.pf2' -printf "loadfont ..."`). Without
    # this, only the hidden "Text mode" entry gets a font by default and the
    # graphical themed menu could render invisible text. unicode.pf2 also
    # covers accented characters.
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

  # Without this, the ISO falls back to the default nixpkgs theme
  # (pkgs.nixos-grub2-theme) at boot instead of ours.
  isoImage.grubTheme = config.boot.loader.grub.theme;

  # ── Boot entries per keyboard layout (GLF-OS style) ────────────────
  # Each specialisation is a separate menu entry, generated automatically
  # by NixOS (no hand-written grub.cfg). Covers both the console keyboard
  # (TTY) and the live session's default GNOME layout.
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
        # Same reasoning as the wallpaper in branding.nix: go through
        # programs.dconf.profiles.user.databases rather than a manual
        # environment.etc, since programs.dconf.profiles.* already owns
        # /etc/dconf once it's used anywhere (in branding.nix). The
        # "databases" list concatenates automatically with the parent's
        # (inheritParentConfig), so no lib.mkForce needed here, unlike
        # console.keyMap.
        programs.dconf.profiles.user.databases = [{
          settings = {
            "org/gnome/desktop/input-sources" = {
              sources = [ (lib.gvariant.mkTuple [ "xkb" kb.xkb ]) ];
            };
          };
        }];
        # programs.dconf.enable is already true in branding.nix (parent).
        # system.nixos.label only accepts [a-zA-Z0-9_.-], hence the
        # slug instead of kb.label directly.
        system.nixos.label = "Roudix-Installer-${name}";
      };
    }) keyboardLayouts;

  # ── Default locale ─────────────────────────────────────────────────────
  time.timeZone = "Europe/Brussels";
  i18n.defaultLocale = "en_US.UTF-8";
  console.keyMap = "us";

  # ── Nix settings ─────────────────────────────────────────────────────────
  nix.settings = {
    experimental-features = [ "nix-command" "flakes" ];
    substituters = [
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
    trusted-public-keys = [
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
    sandbox = false;
  };

  # ── Desktop / display manager: base GDM+GNOME provided by
  # installation-cd-graphical-gnome.nix, customized by the real
  # modules/system/desktop/gnome.nix module (imported via branding.nix above).

  # ── Packages available on the live image ─────────────────────────────────
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

    # A plain applications-menu entry, in addition to the autostart one
    # below — /etc/xdg/autostart is only ever read for session autostart,
    # never scanned by GNOME's app grid (which reads XDG_DATA_DIRS/applications,
    # i.e. /run/current-system/sw/share/applications here). Without this,
    # closing the installer by accident leaves no way to relaunch it short
    # of a terminal.
    (pkgs.writeTextFile {
      name = "roudix-installer-desktop-item";
      destination = "/share/applications/roudix-installer.desktop";
      text = ''
        [Desktop Entry]
        Type=Application
        Version=1.0
        Name=Install Roudix
        GenericName=System Installer
        TryExec=roudix-installer
        Exec=sh -c "sudo --preserve-env=WAYLAND_DISPLAY,XDG_RUNTIME_DIR,DISPLAY roudix-installer"
        Comment=Roudix Installer
        Icon=roudix-installer
        Terminal=false
        StartupNotify=true
        Categories=System;
      '';
    })
  ];


  zramSwap = {
    enable = true;
    algorithm = "zstd";
    memoryPercent = 100;
  };

  # ── Embed the Roudix flake in the ISO ─────────────────────────────────
  # The rsync workflow copies the main repo into iso/roudix-cfg/ at build time.
  # roudix-installer copies /iso/iso-cfg/ to /mnt/etc/nixos/ then runs:
  #   nixos-install --flake /mnt/etc/nixos#roudix
  isoImage.contents = [
    {
      source = ./roudix-cfg;
      target = "/iso-cfg";
    }
  ];

  image.fileName     = "roudix.iso";
  isoImage.volumeID  = "ROUDIX";

  # ── Installer autostart ─────────────────────────────────────────────
  # roudix-installer needs root for disko/nixos-install. The live user
  # ("nixos") is wheel + NOPASSWD + SETENV, so sudo --preserve-env is
  # transparent — same mechanism Calamares used for Wayland.
  environment.etc."xdg/autostart/roudix-installer.desktop".text = ''
    [Desktop Entry]
    Type=Application
    Version=1.0
    Name=Install Roudix
    GenericName=System Installer
    TryExec=roudix-installer
    Exec=sh -c "sudo --preserve-env=WAYLAND_DISPLAY,XDG_RUNTIME_DIR,DISPLAY roudix-installer"
    Comment=Roudix Installer
    Icon=roudix-installer
    Terminal=false
    StartupNotify=true
    Categories=System;
    X-AppStream-Ignore=true
  '';
}
