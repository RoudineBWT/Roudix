{ lib, config, pkgs, ... }:
{
  options.roudix.boot.enable = lib.mkOption {
    description = "Enable Roudix Boot configurations";
    type = lib.types.bool;
    default = true;
  };

  config = lib.mkIf config.roudix.boot.enable {

    # ── Rename UEFI entry to "Roudix" ────────────────────────────────────
    system.activationScripts.renameUefiEntry = lib.mkIf (config.boot.loader.systemd-boot.enable or false) {
      text = ''
        if [ -d /sys/firmware/efi ]; then
          ENTRY=$(${pkgs.efibootmgr}/bin/efibootmgr -v 2>/dev/null \
            | ${pkgs.gnugrep}/bin/grep -i "Linux Boot Manager\|systemd-boot\|UEFI OS" \
            | ${pkgs.gnugrep}/bin/grep -oP 'Boot[0-9A-F]{4}' \
            | head -1)
          if [ -n "$ENTRY" ]; then
            NUM=''${ENTRY#Boot}
            ${pkgs.efibootmgr}/bin/efibootmgr -b "$NUM" -L "Roudix" -q 2>/dev/null || true
          fi
        fi
      '';
    };

    # ── Auto-detect other OS bootloaders across all ESPs ─────────────────
    # systemd-boot can only load EFI files from its own ESP (/boot).
    # So we copy bootloaders from other ESPs into /boot and create entries.
    system.activationScripts.detectOtherOS = lib.mkIf (config.boot.loader.systemd-boot.enable or false) {
      deps = [ "renameUefiEntry" ];
      text = ''
        ESP="/boot"
        ENTRIES_DIR="$ESP/loader/entries"
        ${pkgs.coreutils}/bin/mkdir -p "$ENTRIES_DIR"

        # Copy a bootloader from another ESP into our ESP and create an entry
        install_os() {
          local name="$1"
          local src_efi="$2"   # absolute path on the mounted foreign ESP
          local base_esp="$3"  # mount point of the foreign ESP

          local slug=$(echo "$name" | ${pkgs.coreutils}/bin/tr '[:upper:] ' '[:lower:]-')
          local rel_path="''${src_efi#$base_esp}"   # e.g. /EFI/Microsoft/Boot/bootmgfw.efi
          local dst="$ESP$rel_path"
          local entry_file="$ENTRIES_DIR/roudix-other-$slug.conf"

          # Copy the EFI binary to our ESP if not already present
          ${pkgs.coreutils}/bin/mkdir -p "$(${pkgs.coreutils}/bin/dirname "$dst")"
          ${pkgs.coreutils}/bin/cp -u "$src_efi" "$dst" 2>/dev/null || true

          # Skip creating the entry if it already points to the right file
          if [ -f "$entry_file" ] && ${pkgs.gnugrep}/bin/grep -q "$rel_path" "$entry_file" 2>/dev/null; then
            return
          fi

          echo "title   $name (detected)" >  "$entry_file"
          echo "efi     $rel_path"        >> "$entry_file"
          echo "sort-key z_other_$slug"   >> "$entry_file"
        }

        # Match EFI path to OS name and call install_os
        detect_os() {
          local efi_path="$1"
          local base_esp="$2"
          local name=""
          case "$efi_path" in
            */debian/*)         name="Debian" ;;
            */ubuntu/*)         name="Ubuntu" ;;
            */fedora/*)         name="Fedora" ;;
            */opensuse/*)       name="openSUSE" ;;
            */arch/*)           name="Arch Linux" ;;
            */cachyos/*)        name="CachyOS" ;;
            */limine/*)         name="CachyOS" ;;
            */manjaro/*)        name="Manjaro" ;;
            */pop-os/*)         name="Pop!_OS" ;;
            */Microsoft/Boot/*) name="Windows" ;;
            *)                  return ;;
          esac
          install_os "$name" "$efi_path" "$base_esp"
        }

        # ── Scan all ESPs on the system ───────────────────────────────────
        EFI_PARTTYPE="c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
        current_esp=$(${pkgs.util-linux}/bin/findmnt -n -o SOURCE /boot 2>/dev/null || echo "")

        for part in $(${pkgs.util-linux}/bin/lsblk -o NAME,PARTTYPE -rn \
            | ${pkgs.gnugrep}/bin/grep -i "$EFI_PARTTYPE" \
            | ${pkgs.gawk}/bin/awk '{print "/dev/"$1}'); do

          # Skip the ESP already mounted at /boot (already scanned by systemd-boot)
          [ "$part" = "$current_esp" ] && continue

          # Skip if not a valid block device
          [ -b "$part" ] || continue

          mnt="/tmp/roudix-esp-scan-$$"
          ${pkgs.coreutils}/bin/mkdir -p "$mnt"

          if ${pkgs.util-linux}/bin/mount -t vfat -o ro "$part" "$mnt" 2>/dev/null; then
            for efi in \
              "$mnt"/EFI/*/grubx64.efi \
              "$mnt"/EFI/*/shimx64.efi \
              "$mnt"/EFI/*/BOOTX64.EFI \
              "$mnt"/EFI/limine/BOOTX64.EFI \
              "$mnt"/EFI/limine/limine-uefi-cd.bin \
              "$mnt"/EFI/Microsoft/Boot/bootmgfw.efi; do
              [ -f "$efi" ] && detect_os "$efi" "$mnt"
            done
            ${pkgs.util-linux}/bin/umount "$mnt"
          fi

          ${pkgs.coreutils}/bin/rmdir "$mnt" 2>/dev/null || true
        done

        # ── Remove stale entries whose EFI file no longer exists ──────────
        for entry in "$ENTRIES_DIR"/roudix-other-*.conf; do
          [ -f "$entry" ] || continue
          efi_rel=$(${pkgs.gnugrep}/bin/grep "^efi " "$entry" 2>/dev/null \
            | ${pkgs.gawk}/bin/awk '{print $2}')
          if [ -n "$efi_rel" ] && [ ! -f "$ESP$efi_rel" ]; then
            ${pkgs.coreutils}/bin/rm -f "$entry"
          fi
        done
      '';
    };

  };
}
