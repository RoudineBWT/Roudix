#!/usr/bin/env bash
# Offline test of modules/system/boot/roudix-secureboot.sh against fake EFI
# variables, sbctl state and commands. Run: bash scripts/test-roudix-secureboot.sh
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# What writeShellApplication wraps around the script.
{ printf '#!/usr/bin/env bash\nset -o errexit\nset -o nounset\nset -o pipefail\n'
  cat "$here/modules/system/boot/roudix-secureboot.sh"; } > "$work/roudix-secureboot"
chmod +x "$work/roudix-secureboot"

GLOBAL=8be4df61-93ca-11d2-aa0d-00e098032b8c
DBGUID=d719b2cb-3d3a-4596-a3bc-dad00e67656f
OWNER=47a6f4e9-a6f0-4645-aaf6-5cf10e030a51

mkdir -p "$work/bin"
cat > "$work/bin/sbctl" <<'FAKE'
#!/usr/bin/env bash
case "$1" in
  verify)
    case "${FAKE_LIMINE:-absent}" in
      signed)   echo "✓ /boot/EFI/limine/BOOTX64.EFI is signed" ;;
      unsigned) echo "✗ /boot/EFI/limine/BOOTX64.EFI is not signed" ;;
    esac
    echo "✗ /boot/EFI/Microsoft/Boot/bootmgfw.efi is not signed"
    exit 1 ;;   # the real one exits non-zero when anything is unsigned
  create-keys)
    mkdir -p "$ROUDIX_SB_SBCTL_DIR/keys/PK" "$ROUDIX_SB_SBCTL_DIR/keys/db"
    touch "$ROUDIX_SB_SBCTL_DIR/keys/PK/PK.pem" "$ROUDIX_SB_SBCTL_DIR/keys/db/db.pem"
    echo "47a6f4e9-a6f0-4645-aaf6-5cf10e030a51" > "$ROUDIX_SB_SBCTL_DIR/GUID" ;;
  *) echo "$*" >> "$FAKE_LOG" ;;
esac
FAKE
cat > "$work/bin/efibootmgr" <<'FAKE'
#!/usr/bin/env bash
echo "BootCurrent: 0000"
echo "Boot0000* Limine"
[ "${FAKE_WINDOWS:-0}" = 1 ] && echo "Boot0001* Windows Boot Manager"
[ "${FAKE_EAC:-0}" = 1 ] && echo "Boot0002* NixOS EAC"
true
FAKE
cat > "$work/bin/systemctl" <<'FAKE'
#!/usr/bin/env bash
echo "systemctl $*" >> "$FAKE_LOG"
FAKE
chmod +x "$work/bin/"*

fails=0
n=0

# world <uefi> <tpm> <keys> <setup|-> <enrolled> <sb|-> <limine> [windows] [eac]
world() {
  rm -rf "$work/w"; mkdir -p "$work/w/efivars" "$work/w/tpm0" "$work/w/sbctl"
  [ "$1" = 1 ] && mkdir -p "$work/w/efi"
  [ "$2" = 2 ] && echo 2 > "$work/w/tpm0/tpm_version_major"
  if [ "$3" = 1 ]; then
    mkdir -p "$work/w/sbctl/keys/PK" "$work/w/sbctl/keys/db"
    touch "$work/w/sbctl/keys/PK/PK.pem" "$work/w/sbctl/keys/db/db.pem"
    echo "$OWNER" > "$work/w/sbctl/GUID"
  fi
  if [ "$4" != "-" ]; then { printf '\x07\x00\x00\x00'; printf '%b' "\\x0$4"; } > "$work/w/efivars/SetupMode-$GLOBAL"; fi
  if [ "$6" != "-" ]; then { printf '\x07\x00\x00\x00'; printf '%b' "\\x0$6"; } > "$work/w/efivars/SecureBoot-$GLOBAL"; fi
  if [ "$5" = 1 ]; then
    { printf '\x07\x00\x00\x00junkjunk'
      printf '\xe9\xf4\xa6\x47\xf0\xa6\x45\x46\xaa\xf6\x5c\xf1\x0e\x03\x0a\x51'
      printf 'morejunk'; } > "$work/w/efivars/db-$DBGUID"
  else
    { printf '\x07\x00\x00\x00'; printf 'someone else owns this certificate'; } > "$work/w/efivars/db-$DBGUID"
  fi
  export FAKE_LIMINE="$7" FAKE_WINDOWS="${8:-0}" FAKE_EAC="${9:-0}" FAKE_LOG="$work/log"
  : > "$work/log"
}

run() {
  PATH="$work/bin:$PATH" ROUDIX_SB_NO_SUDO=1 \
    ROUDIX_SB_EFIVARS="$work/w/efivars" ROUDIX_SB_EFI_DIR="$work/w/efi" \
    ROUDIX_SB_SBCTL_DIR="$work/w/sbctl" ROUDIX_SB_TPM_DIR="$work/w" \
    "$work/roudix-secureboot" "$@" 2>&1
}

expect() {  # expect "<name>" "<substring>" <output>
  n=$((n + 1))
  if grep -qF -- "$2" <<<"$3"; then echo "ok $n - $1"
  else echo "not ok $n - $1 (missing: $2)"; printf '%s\n' "${3//$'\n'/$'\n    | '}" | sed '1s/^/    | /'; fails=$((fails + 1)); fi
}
refute() {
  n=$((n + 1))
  if grep -qF -- "$2" <<<"$3"; then echo "not ok $n - $1 (unexpected: $2)"; printf '%s\n' "${3//$'\n'/$'\n    | '}" | sed '1s/^/    | /'; fails=$((fails + 1))
  else echo "ok $n - $1"; fi
}

world 0 - 0 - 0 - absent;  out="$(run status)"
expect "legacy BIOS is reported" "legacy BIOS" "$out"

world 1 - 0 - 0 - absent;  out="$(run status)"
expect "no keys: create them" "roudix-secureboot create-keys" "$out"
expect "no TPM is only a warning" "TPM 2.0 not found" "$out"

world 1 2 1 0 0 0 absent;  out="$(run status)"
expect "TPM 2.0 detected" "TPM: 2.0" "$out"
expect "user mode, keys not enrolled: Setup Mode instructions" "Put the firmware in Setup Mode" "$out"

world 1 2 1 0 0 0 absent 1;  out="$(run status)"
expect "Windows present: BitLocker warning" "BitLocker" "$out"

world 1 2 1 1 0 0 absent;  out="$(run status)"
expect "Setup Mode: enroll" "roudix-secureboot enroll" "$out"

world 1 2 1 0 1 0 unsigned;  out="$(run status)"
expect "own keys detected in db" "Your keys: enrolled" "$out"
expect "enrolled but Limine unsigned: enable the option" "roudix.boot.secureBoot.enable = true" "$out"

world 1 2 1 0 0 0 absent;  out="$(run status)"
expect "foreign db: keys not enrolled" "Your keys: not enrolled" "$out"

world 1 2 1 0 1 0 signed;  out="$(run status)"
expect "signed, Secure Boot off: turn it on" "turn Secure Boot on" "$out"

world 1 2 1 0 1 1 signed;  out="$(run status)"
expect "all done" "Secure Boot is on and Limine is signed" "$out"
expect "EAC optional hint" "roudix.boot.eac.enable" "$out"

world 1 2 1 0 1 1 signed 0 1;  out="$(run status)"
expect "EAC entry present: how to use it" "sudo eac-reboot" "$out"

world 1 2 1 0 1 1 signed;  out="$(ROUDIX_BOOTLOADER=systemd-boot run status)"
expect "non-Limine bootloader is flagged" "Limine only" "$out"

# enroll
world 1 2 1 0 0 0 absent
if out="$(run -y enroll)"; then n=$((n+1)); echo "not ok $n - enroll must refuse outside Setup Mode"; fails=$((fails+1))
else expect "enroll refuses outside Setup Mode" "not in Setup Mode" "$out"; fi

world 1 2 0 1 0 0 absent
if out="$(run -y enroll)"; then n=$((n+1)); echo "not ok $n - enroll needs keys"; fails=$((fails+1))
else expect "enroll needs keys first" "create-keys" "$out"; fi

world 1 2 1 1 0 0 absent
out="$(run -y enroll)"
expect "enroll in Setup Mode succeeds" "Keys enrolled" "$out"
expect "enroll runs sbctl enroll-keys -m -f" "enroll-keys -m -f" "$(cat "$work/log")"

world 1 2 1 1 0 0 absent 1
out="$(run -y enroll)"
expect "enroll warns about BitLocker" "BitLocker" "$out"

# create-keys
world 1 2 0 - 0 - absent
out="$(run create-keys)"
expect "create-keys runs" "Keys created" "$out"
out="$(run create-keys)"
expect "create-keys is idempotent" "already exist" "$out"

# verify
world 1 2 1 0 1 0 signed
out="$(run verify)"
expect "verify: signed" "Limine is signed" "$out"
if world 1 2 1 0 1 0 unsigned && out="$(run verify)"; then n=$((n+1)); echo "not ok $n - verify must fail on unsigned Limine"; fails=$((fails+1))
else expect "verify: unsigned fails" "Limine is not signed" "$out"; fi

# firmware (confirmed with -y)
world 1 2 1 0 1 0 signed
run -y firmware >/dev/null
expect "firmware reboots into setup" "systemctl reboot --firmware-setup" "$(cat "$work/log")"

# help and unknown command
out="$("$work/roudix-secureboot" help)"
expect "help works without root" "Usage: roudix-secureboot" "$out"
if out="$(run bogus)"; then n=$((n+1)); echo "not ok $n - unknown command must fail"; fails=$((fails+1))
else expect "unknown command prints usage" "Usage:" "$out"; fi

echo
if [ "$fails" -eq 0 ]; then echo "all $n checks passed"; else echo "$fails of $n checks FAILED"; exit 1; fi
