{ lib, config, pkgs, ... }:
{
  options.roudix.boot.enable = lib.mkOption {
    description = "Enable Roudix Boot configurations";
    type = lib.types.bool;
    default = true;
  };

  config = lib.mkIf config.roudix.boot.enable {

    # ── Bootloader ────────────────────────────────────────────────────────
    boot.loader.systemd-boot.enable = false;
    boot.loader.efi.canTouchEfiVariables = true;

    boot.loader.limine = {
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
              # ── Catppuccin Mocha Peach ─────────────────────────────────
              graphicalTerminal = {
                foreground       = "fab387"; # peach
                background       = "aa1e1e2e"; # base semi-transparent
                brightForeground = "f5e0dc"; # rosewater
                brightBackground = "ff1e1e2e"; # base opaque
                palette       = "1e1e2e;f38ba8;a6e3a1;f9e2af;fab387;eba0ac;f2cdcd;cdd6f4";
                brightPalette = "585b70;f38ba8;a6e3a1;f9e2af;fab387;eba0ac;f2cdcd;cdd6f4";
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

    # ── Rename UEFI entry to "Roudix" ─────────────────────────────────────
    system.activationScripts.renameUefiEntry = {
      text = ''
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
