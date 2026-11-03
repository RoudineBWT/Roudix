# roudix-secureboot — guided Secure Boot setup for Roudix.
#
# Secure Boot in Roudix means Limine signed with sbctl (roudix.boot.secureBoot)
# and, optionally, the separate "NixOS EAC" boot entry (roudix.boot.eac). The
# firmware part (Setup Mode, turning Secure Boot on) can't be done from the
# running system: this tool shows where you are, runs the steps that can be
# automated and tells you the next one. Docs: docs/secure-boot-eac.md.
#
# The paths below can be overridden to test the script against fake data:
#   ROUDIX_SB_EFIVARS ROUDIX_SB_EFI_DIR ROUDIX_SB_SBCTL_DIR ROUDIX_SB_TPM_DIR
# and ROUDIX_SB_NO_SUDO=1 skips the sudo re-exec.

shopt -s nullglob

efivars="${ROUDIX_SB_EFIVARS:-/sys/firmware/efi/efivars}"
efi_dir="${ROUDIX_SB_EFI_DIR:-/sys/firmware/efi}"
sbctl_dir="${ROUDIX_SB_SBCTL_DIR:-/var/lib/sbctl}"
tpm_dir="${ROUDIX_SB_TPM_DIR:-/sys/class/tpm}"
global_guid="8be4df61-93ca-11d2-aa0d-00e098032b8c"
db_guid="d719b2cb-3d3a-4596-a3bc-dad00e67656f"

# What the configuration says (set by the NixOS module, empty when run standalone).
cfg_bootloader="${ROUDIX_BOOTLOADER:-}"
cfg_secureboot="${ROUDIX_SB_ENABLED:-}"
cfg_eac="${ROUDIX_EAC_ENABLED:-}"

assume_yes=0

if [ -t 1 ]; then
  green=$'\e[32m'; red=$'\e[31m'; yellow=$'\e[33m'; bold=$'\e[1m'; reset=$'\e[0m'
else
  green=""; red=""; yellow=""; bold=""; reset=""
fi

usage() {
  cat <<'EOF'
Usage: roudix-secureboot [-y] [command]

Commands:
  status       Show where you are and the next step (default)
  create-keys  Create the sbctl signing keys (in /var/lib/sbctl)
  enroll       Enroll your keys, next to Microsoft's (needs the firmware in Setup Mode)
  firmware     Reboot into the firmware setup (to clear keys / turn Secure Boot on)
  verify       Check that Limine is signed and point at the EAC check
  help         This text

  -y, --yes    Don't ask for confirmation

The order is: create-keys, put the firmware in Setup Mode, enroll, set
roudix.boot.secureBoot.enable = true and rebuild, then turn Secure Boot on in
the firmware. See docs/secure-boot-eac.md.
EOF
}

ok()   { printf '  %s✓%s %s\n' "$green" "$reset" "$*"; }
bad()  { printf '  %s✗%s %s\n' "$red" "$reset" "$*"; }
warn() { printf '  %s!%s %s\n' "$yellow" "$reset" "$*"; }
info() { printf '  %s\n' "$*"; }
die()  { printf '%s%s%s\n' "$red" "$*" "$reset" >&2; exit 1; }

confirm() {
  [ "$assume_yes" -eq 1 ] && return 0
  local answer
  read -r -p "$1 [y/N] " answer || return 1
  [[ "$answer" =~ ^[yY]$ ]]
}

# ── reading the machine ─────────────────────────────────────────────────────

# Value byte of an EFI variable (the first four bytes are attributes), or empty.
efi_byte() {
  [ -r "$1" ] || return 0
  od -An -t u1 -j4 -N1 "$1" 2>/dev/null | tr -d ' \n' || true
}

is_uefi() { [ -d "$efi_dir" ]; }

tpm_version() {
  local d
  for d in "$tpm_dir"/tpm*; do
    if [ -r "$d/tpm_version_major" ]; then
      tr -d '[:space:]' < "$d/tpm_version_major"
      return 0
    fi
  done
  return 0
}

keys_exist() {
  [ -f "$sbctl_dir/keys/PK/PK.pem" ] && [ -f "$sbctl_dir/keys/db/db.pem" ]
}

# True when the firmware's db holds a certificate owned by our sbctl GUID.
# EFI stores GUIDs mixed-endian: the first three fields little-endian.
own_keys_enrolled() {
  local g gb hex
  [ -r "$sbctl_dir/GUID" ] || return 1
  g="$(tr -d '[:space:]-' < "$sbctl_dir/GUID")"
  [ "${#g}" -eq 32 ] || return 1
  gb="${g:6:2}${g:4:2}${g:2:2}${g:0:2}${g:10:2}${g:8:2}${g:14:2}${g:12:2}${g:16:16}"
  [ -r "$efivars/db-$db_guid" ] || return 1
  hex="$(od -An -v -t x1 "$efivars/db-$db_guid" | tr -d ' \n')"
  [[ "$hex" == *"${gb,,}"* ]]
}

verify_output() { sbctl verify 2>/dev/null || true; }

limine_signed() {
  local out
  out="$(verify_output)"
  grep -qi 'limine/BOOTX64\.EFI is signed' <<<"$out"
}

efi_entries() { efibootmgr 2>/dev/null || true; }

has_entry() {
  local out
  out="$(efi_entries)"
  grep -qi "$1" <<<"$out"
}

# ── commands ────────────────────────────────────────────────────────────────

cmd_status() {
  local sb setup tpm
  sb="$(efi_byte "$efivars/SecureBoot-$global_guid")"
  setup="$(efi_byte "$efivars/SetupMode-$global_guid")"
  tpm="$(tpm_version)"

  printf '%sRoudix Secure Boot%s\n' "$bold" "$reset"

  if ! is_uefi; then
    bad "This machine booted in legacy BIOS/CSM mode: Secure Boot needs UEFI."
    return 0
  fi
  ok "Firmware: UEFI"

  if [ "$tpm" = "2" ]; then ok "TPM: 2.0"; else warn "TPM 2.0 not found (only needed for the EAC entry)"; fi

  local keys=0 enrolled=0 signed=0
  if keys_exist; then keys=1; ok "sbctl keys: created ($sbctl_dir)"; else bad "sbctl keys: not created"; fi

  case "$setup" in
    1) info "Firmware mode: Setup Mode (ready to enroll keys)" ;;
    0) info "Firmware mode: User Mode (keys are installed)" ;;
    *) warn "Firmware mode: unknown (EFI variables not readable)" ;;
  esac

  if own_keys_enrolled; then enrolled=1; ok "Your keys: enrolled in the firmware"; else bad "Your keys: not enrolled in the firmware"; fi

  if [ "$sb" = "1" ]; then ok "Secure Boot: on"; else bad "Secure Boot: off"; fi

  if [ "$cfg_bootloader" != "" ] && [ "$cfg_bootloader" != "limine" ]; then
    warn "Bootloader: $cfg_bootloader (Secure Boot signing here is for Limine only)"
  elif limine_signed; then
    signed=1; ok "Limine: signed"
  else
    bad "Limine: not signed"
  fi

  if has_entry 'NixOS EAC'; then ok "EAC boot entry: present"; else info "EAC boot entry: not set up"; fi

  if [ -n "$cfg_secureboot$cfg_eac" ]; then
    info "Config: roudix.boot.secureBoot.enable = ${cfg_secureboot:-?}, roudix.boot.eac.enable = ${cfg_eac:-?}"
  fi

  printf '\n%sNext step%s\n' "$bold" "$reset"
  if [ "$keys" -eq 0 ]; then
    info "Create your signing keys:  roudix-secureboot create-keys"
  elif [ "$enrolled" -eq 0 ] && [ "$setup" = "1" ]; then
    info "The firmware is in Setup Mode. Enroll your keys:  roudix-secureboot enroll"
  elif [ "$enrolled" -eq 0 ]; then
    info "Put the firmware in Setup Mode: in its setup, clear (don't restore) the Secure Boot keys,"
    info "leave Secure Boot off, then boot Roudix again. Open the setup with:  roudix-secureboot firmware"
    if has_entry 'Windows Boot Manager'; then
      warn "Windows is installed: if it uses BitLocker, have its recovery key ready (aka.ms/myrecoverykey)."
    fi
  elif [ "$signed" -eq 0 ]; then
    info "Set roudix.boot.secureBoot.enable = true; in your local.nix and rebuild, then run:  roudix-secureboot verify"
  elif [ "$sb" != "1" ]; then
    info "Reboot once with Secure Boot still off to check Roudix starts, then turn Secure Boot on:  roudix-secureboot firmware"
  else
    ok "Secure Boot is on and Limine is signed."
    if has_entry 'NixOS EAC'; then
      info "To use the EAC entry:  sudo eac-reboot   then, inside it:  sudo eacnix-check"
    else
      info "Optional: roudix.boot.eac.enable = true; adds the EAC entry (docs/secure-boot-eac.md)."
    fi
  fi
  return 0
}

cmd_create_keys() {
  if keys_exist; then
    ok "Keys already exist in $sbctl_dir (nothing to do). Back them up."
    return 0
  fi
  sbctl create-keys
  ok "Keys created in $sbctl_dir. Back that folder up: without it you can't re-sign Limine."
  info "Next:  roudix-secureboot status"
}

cmd_enroll() {
  is_uefi || die "This machine booted in legacy BIOS mode: no Secure Boot."
  keys_exist || die "No sbctl keys yet. Run:  roudix-secureboot create-keys"
  if [ "$(efi_byte "$efivars/SetupMode-$global_guid")" != "1" ]; then
    die "The firmware is not in Setup Mode, so it won't accept new keys. Clear the Secure Boot keys in its setup (roudix-secureboot firmware), keep Secure Boot off, boot Roudix and try again."
  fi
  if has_entry 'Windows Boot Manager'; then
    warn "Windows is installed: changing the Secure Boot keys can make BitLocker ask for its recovery key."
  fi
  info "This enrolls your keys together with Microsoft's and the firmware's own (sbctl enroll-keys -m -f)."
  confirm "Enroll now?" || die "Cancelled."
  sbctl enroll-keys -m -f
  ok "Keys enrolled."
  info "Next: set roudix.boot.secureBoot.enable = true; in your local.nix, rebuild, then:  roudix-secureboot verify"
}

cmd_firmware() {
  info "Secure Boot has to be changed in the firmware setup."
  confirm "Reboot into the firmware setup now?" || die "Cancelled."
  systemctl reboot --firmware-setup
}

cmd_verify() {
  local out
  out="$(verify_output)"
  if grep -qi 'limine/BOOTX64\.EFI is signed' <<<"$out"; then
    ok "Limine is signed."
  elif grep -qi 'limine/BOOTX64\.EFI is not signed' <<<"$out"; then
    bad "Limine is not signed. Set roudix.boot.secureBoot.enable = true; and rebuild."
    return 1
  else
    warn "No Limine EFI file found by sbctl (is the bootloader Limine, and /boot mounted?)."
    return 1
  fi
  info "The other files sbctl lists as \"not signed\" (Windows, Fedora, EAC entry, kernels) are expected:"
  info "they are signed by their vendors, or checked by Limine through hashes."
  if command -v eacnix-check >/dev/null 2>&1; then
    info "EAC: boot the EAC entry (sudo eac-reboot) and run  sudo eacnix-check  there."
  fi
}

# ── main ────────────────────────────────────────────────────────────────────

args=()
for a in "$@"; do
  case "$a" in
    -y|--yes) assume_yes=1 ;;
    -h|--help) args+=("help") ;;
    *) args+=("$a") ;;
  esac
done

command_name="${args[0]:-status}"

if [ "$command_name" = "help" ]; then usage; exit 0; fi

if [ "$(id -u)" -ne 0 ] && [ "${ROUDIX_SB_NO_SUDO:-}" != "1" ]; then
  exec sudo -- "$0" "$@"
fi

case "$command_name" in
  status)      cmd_status ;;
  create-keys) cmd_create_keys ;;
  enroll)      cmd_enroll ;;
  firmware)    cmd_firmware ;;
  verify)      cmd_verify ;;
  *)           usage >&2; exit 2 ;;
esac
