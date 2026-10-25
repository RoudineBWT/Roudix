{ lib, config, pkgs, ... }:
{
  options.roudix.boot = {
    enable = lib.mkOption {
      description = "Enable Roudix Boot configurations";
      type = lib.types.bool;
      default = true;
    };

    wallpaperAspect = lib.mkOption {
      description = ''
        Aspect ratio of the Limine boot wallpaper. Pick the one closest to your
        MAIN screen (the one with the highest resolution) so the stretched image
        is not distorted. Run ./scripts/detect-boot-aspect.sh to find out which
        one to use; the installers and roudix-switcher suggest it too.
          16x9  -> 1280x720, 1920x1080, 2560x1440, 3840x2160
          16x10 -> 1920x1200, 2560x1600, 2880x1800
          21x9  -> 2560x1080, 3440x1440
          4x3   -> 1024x768, 1280x1024 (5:4), 1600x1200
      '';
      type = lib.types.enum [ "16x9" "16x10" "21x9" "4x3" ];
      default = "16x9";
    };

    menuResolution = lib.mkOption {
      description = ''
        Resolution of the Limine menu, and so of its wallpaper: "auto" lets
        Limine pick, or "<width>x<height>" (e.g. "2560x1440") forces it.
        With several screens of different sizes Limine can end up on the smaller
        one: set your MAIN screen's resolution (the highest one) here. If the
        firmware doesn't offer it, Limine falls back to another one by itself.
        ./scripts/detect-boot-aspect.sh --resolution prints it; the installers
        and roudix-switcher suggest it too. Only used with limine.
      '';
      type = lib.types.either
        (lib.types.enum [ "auto" ])
        (lib.types.strMatching "[0-9]+x[0-9]+");
      default = "auto";
      example = "2560x1440";
    };

    bootloader = lib.mkOption {
      description = "Bootloader to use: \"limine\" or \"systemd-boot\"";
      type = lib.types.enum [ "limine" "systemd-boot" ];
      default = "limine";
    };
  };

  config = lib.mkIf config.roudix.boot.enable {

    # ── Bootloader ────────────────────────────────────────────────────────
    boot.loader.efi.canTouchEfiVariables = true;

    boot.loader.systemd-boot = lib.mkIf (config.roudix.boot.bootloader == "systemd-boot") {
      enable = true;
      configurationLimit = 3;
      editor = false;
    };

    boot.loader.limine = lib.mkIf (config.roudix.boot.bootloader == "limine") {
      enable = true;
      # Enroll config checksum for integrity verification
      enrollConfig = true;
      # Keep last 3 generations in the boot menu
      maxGenerations = 3;
      style = {
        wallpapers = [
          (builtins.path {
            path = ./bootloader + "/wallpaper-${config.roudix.boot.wallpaperAspect}.png";
            name = "limine-wallpaper";
          })
        ];
        wallpaperStyle = "stretched";
        # null = no `interface_resolution` line, Limine picks by itself
        interface.resolution =
          if config.roudix.boot.menuResolution == "auto" then null
          else config.roudix.boot.menuResolution;
        # ── Roudix Roux ──────────────────────────────────────────────
        graphicalTerminal = {
          foreground       = "eab676"; # tan (logo)
          background       = "aa150b05"; # near-black brown, semi-transparent
          brightForeground = "f6e2c4"; # light cream
          brightBackground = "ff150b05"; # near-black brown, opaque
          palette       = "150b05;c9622d;8a9a5b;eab676;6b8ca3;b06a4a;c98450;eab676";
          brightPalette = "5c2a12;e07a3f;a8b98a;f4c98f;89a8bd;c98a6a;dba06e;f6e2c4";
        };
      };
      # ── Extra boot entries for other OS on other ESPs ─────────────────
      # Use the PARTUUID of each ESP (not the filesystem UUID)
      # Get PARTUUIDs with: lsblk -o NAME,PARTUUID
      extraEntries = if builtins.pathExists ./boot.local.nix
        then (import ./boot.local.nix).extraEntries or ""
        else "";
    };

    # ── Rename boot profile label ─────────────────────────────────────────────
    system.nixos.label = lib.mkForce "${config.system.nixos.version}";

    # ── Rename UEFI entry to "Roudix" (on every boot, not just at activation) ──
    systemd.services.rename-uefi-entry = {
      description = "Rename UEFI boot entry to Roudix";
      wantedBy = [ "multi-user.target" ];
      after = [ "local-fs.target" ];
      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
      };
      script = ''
        if [ -d /sys/firmware/efi ]; then
          ENTRY=$(${pkgs.efibootmgr}/bin/efibootmgr -v 2>/dev/null \
            | ${pkgs.gnugrep}/bin/grep -i "Linux Boot Manager\|Limine\|UEFI OS" \
            | ${pkgs.gnugrep}/bin/grep -oP 'Boot[0-9A-F]{4}' \
            | head -1)
          if [ -n "$ENTRY" ]; then
            NUM=''${ENTRY#Boot}
            ${pkgs.efibootmgr}/bin/efibootmgr -b "$NUM" -L "Roudix" -q 2>/dev/null || true
          fi
        fi
      '';
    };

  };
}
