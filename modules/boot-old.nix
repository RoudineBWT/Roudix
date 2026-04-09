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
    #
    # Strategy per bootloader type :
    #   Windows      → entrée UEFI native via efibootmgr (copier bootmgfw.efi
    #                  seul casse le BCD lookup → erreur 0xc000000f)
    #   GRUB / shim  → copie grubx64.efi / shimx64.efi dans /boot + entrée .conf
    #   Limine       → copie limine_x64.efi dans /boot + entrée .conf
    #   systemd-boot → lit loader/entries/ de l'ESP étrangère et importe
    #                  chaque entrée individuellement (nom + EFI exacts)
    system.activationScripts.detectOtherOS = lib.mkIf (config.boot.loader.systemd-boot.enable or false) {
      deps = [ "renameUefiEntry" ];
      text = ''
        ESP="/boot"
        ENTRIES_DIR="$ESP/loader/entries"
        ${pkgs.coreutils}/bin/mkdir -p "$ENTRIES_DIR"

        # ── install_os : copie un EFI et crée l'entrée .conf ─────────────
        # Cas spécial Windows : crée une entrée UEFI native à la place.
        install_os() {
          local name="$1"
          local src_efi="$2"   # chemin absolu sur l'ESP montée
          local base_esp="$3"  # point de montage de l'ESP (sans slash final)

          local slug
          slug=$(echo "$name" \
            | ${pkgs.gnused}/bin/sed 's/[[:upper:]]/\L&/g; s/[ \/!()+]/-/g; s/[^a-z0-9-]//g')
          base_esp="''${base_esp%/}"

          # ── Windows ──────────────────────────────────────────────────────
          if [ "$name" = "Windows" ]; then
            local win_part
            win_part=$(${pkgs.util-linux}/bin/findmnt -n -o SOURCE "$base_esp" 2>/dev/null || echo "")
            if [ -n "$win_part" ] && [ -b "$win_part" ]; then
              local disk part_num
              disk=$(${pkgs.util-linux}/bin/lsblk -no PKNAME "$win_part" 2>/dev/null | head -1)
              part_num=$(${pkgs.util-linux}/bin/lsblk -no PARTN "$win_part" 2>/dev/null | head -1)
              if [ -n "$disk" ] && [ -n "$part_num" ]; then
                if ! ${pkgs.efibootmgr}/bin/efibootmgr -v 2>/dev/null \
                    | ${pkgs.gnugrep}/bin/grep -qi "Windows Boot Manager"; then
                  ${pkgs.efibootmgr}/bin/efibootmgr \
                    --create \
                    --disk "/dev/$disk" \
                    --part "$part_num" \
                    --label "Windows Boot Manager" \
                    --loader '\EFI\Microsoft\Boot\bootmgfw.efi' \
                    --quiet 2>/dev/null || true
                fi
              fi
            fi
            return
          fi

          # ── Autres OS ────────────────────────────────────────────────────
          local rel_path="''${src_efi#$base_esp}"
          local dst="$ESP$rel_path"
          local entry_file="$ENTRIES_DIR/roudix-other-$slug.conf"

          ${pkgs.coreutils}/bin/mkdir -p "$(${pkgs.coreutils}/bin/dirname "$dst")"
          ${pkgs.coreutils}/bin/cp -u "$src_efi" "$dst" 2>/dev/null || true

          if [ -f "$entry_file" ] && ${pkgs.gnugrep}/bin/grep -q "$rel_path" "$entry_file" 2>/dev/null; then
            return
          fi

          printf 'title   %s (detected)\n' "$name"    >  "$entry_file"
          printf 'efi     %s\n'            "$rel_path" >> "$entry_file"
          printf 'sort-key z_other_%s\n'  "$slug"      >> "$entry_file"
        }

        # ── detect_os : identifie l'OS depuis le chemin EFI ──────────────
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
            */endeavouros/*)    name="EndeavourOS" ;;
            */garuda/*)         name="Garuda Linux" ;;
            */gentoo/*)         name="Gentoo" ;;
            */nixos/*)          return ;;  # skip nos propres entrées NixOS
            */Microsoft/Boot/*) name="Windows" ;;
            *)                  return ;;
          esac
          install_os "$name" "$efi_path" "$base_esp"
        }

        # ── import_sdboot_entries : lit loader/entries/ d'une ESP étrangère
        # Couvre toute distro utilisant systemd-boot, peu importe le nom.
        # Le titre et le chemin EFI sont lus directement depuis les .conf,
        # donc pas besoin de connaître la distro à l'avance.
        import_sdboot_entries() {
          local base_esp="$1"
          local entries_src="$base_esp/loader/entries"
          [ -d "$entries_src" ] || return

          for conf in "$entries_src"/*.conf; do
            [ -f "$conf" ] || continue

            # Ignore les entrées NixOS (déjà gérées par systemd-boot)
            ${pkgs.gnugrep}/bin/grep -qi "nixos\|NixOS" "$conf" 2>/dev/null && continue

            local title efi_rel
            title=$(${pkgs.gnugrep}/bin/grep "^title " "$conf" 2>/dev/null \
              | head -1 \
              | ${pkgs.gawk}/bin/awk '{$1=""; sub(/^ /,""); print}')
            efi_rel=$(${pkgs.gnugrep}/bin/grep "^efi " "$conf" 2>/dev/null \
              | head -1 \
              | ${pkgs.gawk}/bin/awk '{print $2}')

            [ -n "$title" ]   || continue
            [ -n "$efi_rel" ] || continue

            local src_efi="$base_esp$efi_rel"
            [ -f "$src_efi" ] || continue

            install_os "$title" "$src_efi" "$base_esp"
          done
        }

        # ── Scan all ESPs on the system ───────────────────────────────────
        EFI_PARTTYPE="c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
        current_esp=$(${pkgs.util-linux}/bin/findmnt -n -o SOURCE /boot 2>/dev/null || echo "")

        for part in $(${pkgs.util-linux}/bin/lsblk -o NAME,PARTTYPE -rn \
            | ${pkgs.gnugrep}/bin/grep -i "$EFI_PARTTYPE" \
            | ${pkgs.gawk}/bin/awk '{print "/dev/"$1}'); do

          [ "$part" = "$current_esp" ] && continue
          [ -b "$part" ] || continue

          mnt=$(${pkgs.coreutils}/bin/mktemp -d /tmp/roudix-esp-scan-XXXXXX)

          if ${pkgs.util-linux}/bin/mount -t vfat -o ro,noatime "$part" "$mnt" 2>/dev/null; then

            # 1. Importe les entrées systemd-boot de l'ESP étrangère
            #    → couvre toute distro avec systemd-boot (nom exact depuis .conf)
            import_sdboot_entries "$mnt"

            # 2. Scan des binaires EFI connus
            #    → couvre GRUB, shim, Limine, Windows
            #    → fallback pour les distros sans loader/entries
            (
              shopt -s nullglob
              for efi in \
                "$mnt"/EFI/*/grubx64.efi \
                "$mnt"/EFI/*/shimx64.efi \
                "$mnt"/EFI/*/grub.efi \
                "$mnt"/EFI/limine/limine_x64.efi \
                "$mnt"/EFI/limine/BOOTX64.EFI \
                "$mnt"/EFI/Microsoft/Boot/bootmgfw.efi; do
                detect_os "$efi" "$mnt"
              done
            )

            ${pkgs.util-linux}/bin/umount "$mnt"
          fi

          ${pkgs.coreutils}/bin/rmdir "$mnt" 2>/dev/null || true
        done

        # ── Supprime les entrées obsolètes ────────────────────────────────
        # Windows est géré via efibootmgr, pas via un .conf :
        # on supprime toute ancienne entrée roudix-other-windows.conf.
        ${pkgs.coreutils}/bin/rm -f "$ENTRIES_DIR/roudix-other-windows.conf"

        for entry in "$ENTRIES_DIR"/roudix-other-*.conf; do
          [ -f "$entry" ] || continue
          efi_rel=$(${pkgs.gnugrep}/bin/grep "^efi " "$entry" 2>/dev/null \
            | ${pkgs.gawk}/bin/awk '{print $2}')
          [ -n "$efi_rel" ] || continue
          if [ ! -f "$ESP$efi_rel" ]; then
            ${pkgs.coreutils}/bin/rm -f "$entry" || true
          fi
        done
      '';
    };

  };
}
