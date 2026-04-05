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

      # ── Extra boot entries for other OS on other ESPs ─────────────────
      # Use the PARTUUID of each ESP (not the filesystem UUID)
      # Get PARTUUIDs with: lsblk -o NAME,PARTUUID
      extraEntries = ''
        /Windows
          protocol: efi
          path: uuid(ff4a714e-8ba8-4b3b-bf24-27ab1d7c4364):/EFI/Microsoft/Boot/bootmgfw.efi

        /CachyOS
          protocol: efi
          path: uuid(337d9565-6dab-41c8-bebd-1128795554be):/EFI/limine/BOOTX64.EFI
      '';
    };

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
