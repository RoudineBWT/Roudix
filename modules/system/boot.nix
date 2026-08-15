{ lib, config, pkgs, ... }:
{
  options.roudix.boot = {
    enable = lib.mkOption {
      description = "Enable Roudix Boot configurations";
      type = lib.types.bool;
      default = true;
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
            path = ./bootloader/wallpaper.png;
            name = "limine-wallpaper";
          })
        ];
        wallpaperStyle = "stretched";
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

    # ── Rename UEFI entry to "Roudix" (à chaque boot, pas juste à l'activation) ──
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
