#!/usr/bin/env bash
# install.sh — Roudix installer
# https://github.com/RoudineBWT/Roudix

set -euo pipefail

# ── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${CYAN}${BOLD}[roudix]${NC} $*"; }
success() { echo -e "${GREEN}${BOLD}[✓]${NC} $*"; }
warn()    { echo -e "${YELLOW}${BOLD}[!]${NC} $*"; }
error()   { echo -e "${RED}${BOLD}[✗]${NC} $*"; exit 1; }

ask() {
  local prompt="$1"
  local var_name="$2"
  echo -e "${BOLD}$prompt${NC}"
  read -r "$var_name"
}

pick() {
  # pick "Question" VAR_NAME "opt1|desc1" "opt2|desc2" ...
  local prompt="$1"; shift
  local var_name="$1"; shift
  local options=("$@")

  echo -e "\n${BOLD}$prompt${NC}"
  for i in "${!options[@]}"; do
    local val="${options[$i]%%|*}"
    local desc="${options[$i]#*|}"
    printf "  ${CYAN}%2d)${NC} %-30s %s\n" "$((i+1))" "$val" "$desc"
  done

  while true; do
    read -rp "Choice [1-${#options[@]}]: " choice
    if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#options[@]} )); then
      local selected="${options[$((choice-1))]}"
      printf -v "$var_name" '%s' "${selected%%|*}"
      break
    fi
    warn "Invalid choice, please try again."
  done
}

# ── Bootstrap: git + nix flakes ──────────────────────────────────────────────
info "Bootstrapping environment (git + nix flakes)..."

if ! command -v git >/dev/null 2>&1; then
  info "Installing git..."
  nix-env -iA nixos.git || error "Failed to install git."
fi
success "git is available."

# ── Banner ───────────────────────────────────────────────────────────────────
echo -e "
${CYAN}${BOLD}
██████╗  ██████╗ ██╗   ██╗██████╗ ██╗██╗  ██╗
██╔══██╗██╔═══██╗██║   ██║██╔══██╗██║╚██╗██╔╝
██████╔╝██║   ██║██║   ██║██║  ██║██║ ╚███╔╝
██╔══██╗██║   ██║██║   ██║██║  ██║██║ ██╔██╗
██║  ██║╚██████╔╝╚██████╔╝██████╔╝██║██╔╝ ██╗
╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═╝
${NC}${BOLD}         NixOS Configuration Installer${NC}
"


# ── Username ──────────────────────────────────────────────────────────────────
echo ""
ask "Your username (used for the home directory):" USERNAME
[[ -z "$USERNAME" ]] && error "Username cannot be empty."

INSTALL_DIR="/home/${USERNAME}/.config/roudix"

# ── Clone repo ────────────────────────────────────────────────────────────────
if [[ -d "$INSTALL_DIR" ]]; then
  if [[ -d "$INSTALL_DIR/.git" ]]; then
    warn "Roudix repo already exists at $INSTALL_DIR."
    read -rp "Re-clone from scratch? [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
      rm -rf "$INSTALL_DIR"
      mkdir -p "/home/${USERNAME}/.config"
      git clone https://github.com/RoudineBWT/Roudix "$INSTALL_DIR"
      success "Repository re-cloned."
    else
      info "Using existing repo."
    fi
  else
    warn "Directory $INSTALL_DIR exists but is not a git repo."
    read -rp "Delete and clone? [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
      rm -rf "$INSTALL_DIR"
      mkdir -p "/home/${USERNAME}/.config"
      git clone https://github.com/RoudineBWT/Roudix "$INSTALL_DIR"
      success "Repository cloned."
    else
      info "Using existing directory."
    fi
  fi
else
  mkdir -p "/home/${USERNAME}/.config"
  git clone https://github.com/RoudineBWT/Roudix "$INSTALL_DIR"
  success "Repository cloned."
fi

cd "$INSTALL_DIR"

# ── Create username.nix ───────────────────────────────────────────────────────
info "Creating username.nix..."
echo "\"${USERNAME}\"" > "hosts/roudix/username.nix"
success "username.nix created."

# ── Generate hardware config ──────────────────────────────────────────────────
info "Generating hardware-configuration.nix..."

HW_CONFIG_STDERR=$(mktemp)
HW_CONFIG_FILE="hosts/roudix/hardware-configuration.nix"

# Generate into /etc/nixos (default) then copy — avoids stdout truncation on btrfs
nixos-generate-config 2>"$HW_CONFIG_STDERR" || true
cp /etc/nixos/hardware-configuration.nix "$HW_CONFIG_FILE"

# ── btrfs subvolume auto-patch ────────────────────────────────────────────────
if grep -q "Failed to retrieve subvolume info" "$HW_CONFIG_STDERR" 2>/dev/null; then
  warn "btrfs détecté — patch automatique des options de montage..."

  # Read active btrfs mounts from /proc/mounts
  # Format: device mountpoint fstype options dump pass
  while IFS=' ' read -r _dev mountpoint _fstype mountopts _rest; do
    # Extract subvol= from mount options (subvolid handled separately)
    subvol=""
    compress=""
    noatime=""
    ssd=""
    discard=""

    IFS=',' read -ra opts_arr <<< "$mountopts"
    for opt in "${opts_arr[@]}"; do
      case "$opt" in
        subvol=*)   subvol="${opt#subvol=}" ;;
        compress=zstd|compress=zstd:*) compress="compress=zstd:1" ;;
        compress-force=zstd|compress-force=zstd:*) compress="compress-force=zstd:1" ;;
        compress=*|compress-force=*) compress="$opt" ;;
        noatime)    noatime="noatime" ;;
        ssd)        ssd="ssd" ;;
        discard=async|discard) discard="discard=async" ;;
      esac
    done

    # Skip if no subvol at all (truly bare btrfs mount, not even subvol=/)
    [[ -z "$subvol" ]] && continue

    # Escape mountpoint for use as sed pattern (handle special chars like /)
    escaped_mp=$(printf '%s\n' "$mountpoint" | sed 's/[\/&]/\\&/g')

    # Build the options list to inject
    # Strip leading slash from subvol name (Nix convention: subvol=home not subvol=/home)
    subvol="${subvol#/}"
    # Skip bare root subvol (subvol=/ → empty after strip, no options needed)
    [[ -z "$subvol" ]] && continue
    # Detect SSD/NVMe via sysfs to decide whether to add ssd + discard=async
    # Strip partition suffix to get base device (nvme0n1p2 → nvme0n1, sda1 → sda)
    base_dev=$(basename "$_dev" | sed 's/p\?[0-9]*$//')
    rotational=$(cat "/sys/block/${base_dev}/queue/rotational" 2>/dev/null)
    is_nvme=false
    [[ "$_dev" == /dev/nvme* ]] && is_nvme=true

    nix_opts="\"subvol=${subvol}\""
    [[ -n "$compress" ]] && nix_opts="${nix_opts} \"${compress}\""
    if [[ "$rotational" == "0" ]]; then
      nix_opts="${nix_opts} \"ssd\""
      nix_opts="${nix_opts} \"discard=async\""
    fi

    # In hardware-configuration.nix, find the fileSystems."<mountpoint>" block
    # and inject/replace the options = [ ... ]; line
    # Strategy: if options line already exists → replace it; if not → insert after fsType line
    if grep -q "fileSystems\.\"${mountpoint}\"" "$HW_CONFIG_FILE"; then
      if grep -A5 "fileSystems\.\"${mountpoint}\"" "$HW_CONFIG_FILE" | grep -q "options = \["; then
        # Replace existing options line for this block
        # Use awk to only replace within the correct block
        awk -v mp="$mountpoint" -v opts="$nix_opts" '
          /fileSystems\."/ { in_block = ($0 ~ "\"" mp "\"") }
          in_block && /options = \[/ {
            sub(/options = \[[^\]]*\]/, "options = [ " opts " ]")
          }
          { print }
        ' "$HW_CONFIG_FILE" > "${HW_CONFIG_FILE}.tmp" && mv "${HW_CONFIG_FILE}.tmp" "$HW_CONFIG_FILE"
      else
        # Insert options line after the fsType = "btrfs"; line in this block
        awk -v mp="$mountpoint" -v opts="$nix_opts" '
          /fileSystems\."/ { in_block = ($0 ~ "\"" mp "\"") }
          in_block && /fsType = "btrfs"/ {
            print
            print "      options = [ " opts " ];"
            next
          }
          { print }
        ' "$HW_CONFIG_FILE" > "${HW_CONFIG_FILE}.tmp" && mv "${HW_CONFIG_FILE}.tmp" "$HW_CONFIG_FILE"
      fi
      success "Options btrfs injectées pour ${mountpoint} (subvol=${subvol}${compress:+, $compress}${noatime:+, noatime})."
    fi
  done < <(grep ' btrfs ' /proc/mounts)
fi

rm -f "$HW_CONFIG_STDERR"
success "hardware-configuration.nix generated."

# ── Copy local.nix ────────────────────────────────────────────────────────────
info "Creating local.nix from example..."
cp hosts/roudix/local.nix.example hosts/roudix/local.nix
cp home/local.nix.example home/local.nix
success "local.nix created."

# ── Copy boot.local.nix ───────────────────────────────────────────────────────
info "Creating boot.local.nix from example..."
cp modules/system/boot.local.nix.example modules/system/boot.local.nix
success "boot.local.nix created."

# ── Multi-boot: detect other OS via EFI NVRAM ─────────────────────────────────
echo -e "\n${BOLD}══════════════════════════════════════${NC}"
info "Détection des autres systèmes (NVRAM EFI)..."
echo -e "${BOLD}══════════════════════════════════════${NC}"

BOOT_LOCAL_NIX="modules/system/boot.local.nix"

# Entries we want to skip — NixOS/Roudix itself and firmware tools
SKIP_PATTERN="nixos|roudix|uefi|firmware|setup|shell|pxe|ipv4|ipv6|network|floppy|optical|cd|dvd|usb boot"

# Collect EFI entries from NVRAM using efibootmgr -v
# Each relevant line looks like:
#   Boot0001* Windows Boot Manager  HD(1,GPT,<PARTUUID>,...)/File(\EFI\Microsoft\Boot\bootmgfw.efi)
declare -a DETECTED_LABELS=()
declare -a DETECTED_PARTUUIDS=()
declare -a DETECTED_EFIPATHS=()

while IFS= read -r line; do
  # Only active boot entries (marked with *)
  [[ "$line" =~ ^Boot[0-9A-Fa-f]{4}\* ]] || continue

  # Extract human label (between * and the HD( block)
  label=$(echo "$line" | sed 's/^Boot[0-9A-Fa-f]\{4\}\*[[:space:]]*//' | sed 's/[[:space:]]*HD(.*$//' | sed 's/[[:space:]]*$//')

  # Skip if label matches things we don't want in Limine
  if echo "$label" | grep -qiE "$SKIP_PATTERN"; then
    continue
  fi

  # Extract PARTUUID from the HD(...) GPT block
  # Format: HD(<part>,GPT,<PARTUUID>,...)
  partuuid=$(echo "$line" | grep -oiP '(?<=GPT,)[0-9a-f-]{36}' | head -1)
  [[ -z "$partuuid" ]] && continue

  # Extract EFI path — comes after HD(...)/  as \EFI\...\file.efi
  # efibootmgr sometimes appends garbage bytes after the .efi — strip them
  efi_path=$(echo "$line" | grep -oP 'HD\([^)]+\)/(?:\\[^\s\\,]+)+' | \
    grep -oP '(?<=/)(?:\\[^\s\\,]+)+' | head -1 | tr '\\' '/')
  efi_path=$(echo "$efi_path" | sed 's/\(\.efi\).*/\1/i')
  [[ -z "$efi_path" ]] && continue

  DETECTED_LABELS+=("$label")
  DETECTED_PARTUUIDS+=("$partuuid")
  DETECTED_EFIPATHS+=("$efi_path")

done < <(efibootmgr -v 2>/dev/null)

# ── Interactive selection ──────────────────────────────────────────────────────
SELECTED_ENTRIES=()

if [[ ${#DETECTED_LABELS[@]} -eq 0 ]]; then
  info "Aucun autre OS détecté dans la NVRAM EFI — boot.local.nix laissé vide."
  SKIP_ENTRY_MSG=true
else
  echo -e "\n  ${BOLD}OS détectés dans la NVRAM EFI :${NC}\n"
  for i in "${!DETECTED_LABELS[@]}"; do
    printf "  ${CYAN}%2d)${NC} %-35s ${BOLD}PARTUUID:${NC} %s\n" \
      "$((i+1))" "${DETECTED_LABELS[$i]}" "${DETECTED_PARTUUIDS[$i]}"
    printf "      ${BOLD}EFI path:${NC} %s\n" "${DETECTED_EFIPATHS[$i]}"
  done

  echo -e "\n  ${BOLD}Lesquels veux-tu ajouter dans Limine ?${NC}"
  echo -e "  (entre les numéros séparés par des espaces, ex: ${CYAN}1 3${NC} — ou ${CYAN}0${NC} pour aucun)\n"
  read -rp "  Choix: " raw_choices

  if [[ "$raw_choices" != "0" && -n "$raw_choices" ]]; then
    for choice in $raw_choices; do
      idx=$((choice - 1))
      if (( idx >= 0 && idx < ${#DETECTED_LABELS[@]} )); then
        SELECTED_ENTRIES+=("$idx")
      else
        warn "Entrée $choice ignorée (hors limites)."
      fi
    done
  fi
fi

# ── Write boot.local.nix ──────────────────────────────────────────────────────
if [[ ${#SELECTED_ENTRIES[@]} -gt 0 ]]; then
  info "Génération de boot.local.nix..."

  ENTRIES_BLOCK=""
  for idx in "${SELECTED_ENTRIES[@]}"; do
    label="${DETECTED_LABELS[$idx]}"
    partuuid="${DETECTED_PARTUUIDS[$idx]}"
    efi_path="${DETECTED_EFIPATHS[$idx]}"
    ENTRIES_BLOCK+="    //${label}\n"
    ENTRIES_BLOCK+="      protocol: efi\n"
    ENTRIES_BLOCK+="      path: uuid(${partuuid}):${efi_path}\n"
  done

  {
    echo "# ── boot.local.nix ──────────────────────────────────────────────────────────"
    echo "# Generated by roudix-installer — gitignored, never overwritten by git pull."
    echo "# ────────────────────────────────────────────────────────────────────────────"
    echo "{"
    echo "  extraEntries = ''"
    echo "    /+Other systems and bootloaders"
    printf '%b' "$ENTRIES_BLOCK"
    echo "  '';"
    echo "}"
  } > "$BOOT_LOCAL_NIX"

  success "boot.local.nix configuré avec ${#SELECTED_ENTRIES[@]} entrée(s)."
  for idx in "${SELECTED_ENTRIES[@]}"; do
    echo -e "  ${GREEN}✓${NC} ${DETECTED_LABELS[$idx]}"
  done
else
  [[ -z "${SKIP_ENTRY_MSG:-}" ]] && info "Aucune entrée ajoutée — boot.local.nix laissé vide (NixOS only)."
fi

# ── Configuration questions ───────────────────────────────────────────────────
echo -e "\n${BOLD}══════════════════════════════════════${NC}"
info "Hardware & software configuration"
echo -e "${BOLD}══════════════════════════════════════${NC}"

# Auto-detect GPU via sysfs PCI vendor IDs (works without lspci on live ISO)
DETECTED_GPU=""
NVIDIA_LAPTOP="false"
declare -A GPU_VENDORS_FOUND=()

for vendor_file in /sys/bus/pci/devices/*/vendor; do
  vendor=$(cat "$vendor_file" 2>/dev/null)
  class_file="${vendor_file/vendor/class}"
  class=$(cat "$class_file" 2>/dev/null)
  # PCI class 0x03xxxx = display controller
  [[ "$class" == 0x03* ]] || continue
  case "$vendor" in
    0x1002) GPU_VENDORS_FOUND[amd]=1    ;;
    0x10de) GPU_VENDORS_FOUND[nvidia]=1 ;;
    0x8086) GPU_VENDORS_FOUND[intel]=1  ;;
  esac
done

# Detect Optimus: NVIDIA + iGPU (Intel or AMD) = laptop discrete GPU
if [[ -n "${GPU_VENDORS_FOUND[nvidia]:-}" ]]; then
  DETECTED_GPU="nvidia"
  if [[ -n "${GPU_VENDORS_FOUND[intel]:-}" || -n "${GPU_VENDORS_FOUND[amd]:-}" ]]; then
    NVIDIA_LAPTOP="true"
    igpu="${GPU_VENDORS_FOUND[intel]:+Intel}${GPU_VENDORS_FOUND[amd]:+AMD}"
    warn "Configuration Optimus détectée (${igpu} iGPU + NVIDIA dGPU) — nvidiaLaptop activé."
  fi
elif [[ -n "${GPU_VENDORS_FOUND[amd]:-}" ]]; then
  DETECTED_GPU="amd"
elif [[ -n "${GPU_VENDORS_FOUND[intel]:-}" ]]; then
  DETECTED_GPU="intel"
fi

if [[ -n "$DETECTED_GPU" ]]; then
  info "GPU détecté automatiquement : ${BOLD}${DETECTED_GPU}${NC}${NVIDIA_LAPTOP:+ (laptop Optimus)}"
  read -rp "Confirmer ? [Y/n]: " gpu_confirm
  if [[ "${gpu_confirm:-Y}" =~ ^[Yy]$ ]]; then
    GPU="$DETECTED_GPU"
  else
    NVIDIA_LAPTOP="false"
    pick "GPU:" GPU \
      "amd|AMD GPU" \
      "nvidia|NVIDIA GPU" \
      "intel|Intel integrated GPU"
    # If user manually picked nvidia, ask about laptop
    if [[ "$GPU" == "nvidia" ]]; then
      pick "Laptop avec NVIDIA dGPU (Optimus) ?" NVIDIA_LAPTOP \
        "false|Non — desktop ou NVIDIA seul" \
        "true|Oui — laptop Intel/AMD + NVIDIA"
    fi
  fi
else
  pick "GPU:" GPU \
    "amd|AMD GPU" \
    "nvidia|NVIDIA GPU" \
    "intel|Intel integrated GPU"
  if [[ "$GPU" == "nvidia" ]]; then
    pick "Laptop avec NVIDIA dGPU (Optimus) ?" NVIDIA_LAPTOP \
      "false|Non — desktop ou NVIDIA seul" \
      "true|Oui — laptop Intel/AMD + NVIDIA"
  fi
fi

# Auto-detect CPU vendor
DETECTED_CPU=""
if grep -q "AuthenticAMD" /proc/cpuinfo 2>/dev/null; then
  DETECTED_CPU="amd"
elif grep -q "GenuineIntel" /proc/cpuinfo 2>/dev/null; then
  DETECTED_CPU="intel"
fi

if [[ -n "$DETECTED_CPU" ]]; then
  info "CPU détecté automatiquement : ${BOLD}${DETECTED_CPU}${NC}"
  read -rp "Confirmer ? [Y/n]: " cpu_confirm
  if [[ "${cpu_confirm:-Y}" =~ ^[Yy]$ ]]; then
    CPU="$DETECTED_CPU"
  else
    pick "CPU:" CPU \
      "amd|AMD CPU" \
      "intel|Intel CPU"
  fi
else
  pick "CPU:" CPU \
    "amd|AMD CPU" \
    "intel|Intel CPU"
fi

pick "Kernel:" KERNEL \
  "cachyos-latest|Standard latest CachyOS kernel" \
  "cachyos-latest-v3|x86_64-v3 optimized (recommended for modern CPUs)" \
  "cachyos-latest-lto|LTO build for better performance" \
  "cachyos-latest-lto-v3|LTO + x86_64-v3 (best performance, modern CPUs only)" \
  "cachyos-lts|Long-term support CachyOS kernel" \
  "cachyos-lts-v3|LTS + x86_64-v3 optimized" \
  "cachyos-lts-lto-v3|LTS + LTO + x86_64-v3 (stable + performance)" \
  "cachyos-rc|Release candidate — bleeding edge, potentially unstable"

pick "Browser:" BROWSER \
  "none|No chromium base browser" \
  "brave|Brave" \
  "helium|Helium" \
  "vivaldi|Vivaldi"

pick "Install Zen Browser?" ZEN \
  "false|No" \
  "true|Yes"

pick "Desktop environment:" DE \
  "niri|Niri" \
  "gnome|GNOME" \
  "kde|KDE Plasma" \
  "hyprland|Hyprland"

pick "Default shell:" SHELL_DEFAULT \
  "fish|Fish — smart, user-friendly shell (recommended)" \
  "bash|Bash — classic Unix shell"

pick "Running inside a VM?" VM_GUEST \
  "false|No — bare metal install" \
  "true|Yes — enable VM guest optimizations"

pick "Enable gaming packages? (Steam, Wine, Lutris...)" GAMING \
  "true|Yes" \
  "false|No"

pick "Timezone:" TIMEZONE \
  "Europe/Brussels|Belgique" \
  "Europe/Paris|France" \
  "Europe/London|Royaume-Uni" \
  "Europe/Amsterdam|Pays-Bas" \
  "Europe/Berlin|Allemagne" \
  "Europe/Vienna|Autriche" \
  "Europe/Zurich|Suisse" \
  "Europe/Luxembourg|Luxembourg" \
  "Europe/Madrid|Espagne" \
  "Europe/Lisbon|Portugal" \
  "Europe/Rome|Italie" \
  "Europe/Warsaw|Pologne" \
  "Europe/Prague|République Tchèque" \
  "Europe/Bratislava|Slovaquie" \
  "Europe/Budapest|Hongrie" \
  "Europe/Bucharest|Roumanie" \
  "Europe/Sofia|Bulgarie" \
  "Europe/Athens|Grèce" \
  "Europe/Helsinki|Finlande" \
  "Europe/Stockholm|Suède" \
  "Europe/Oslo|Norvège" \
  "Europe/Copenhagen|Danemark" \
  "Europe/Tallinn|Estonie" \
  "Europe/Riga|Lettonie" \
  "Europe/Vilnius|Lituanie" \
  "Europe/Kiev|Ukraine" \
  "Europe/Moscow|Russie (Moscou)" \
  "Europe/Istanbul|Turquie" \
  "Atlantic/Reykjavik|Islande" \
  "Africa/Casablanca|Maroc" \
  "Africa/Algiers|Algérie" \
  "Africa/Tunis|Tunisie" \
  "Africa/Cairo|Égypte" \
  "Africa/Johannesburg|Afrique du Sud" \
  "Africa/Lagos|Nigéria" \
  "Africa/Nairobi|Kenya" \
  "America/New_York|États-Unis (Est)" \
  "America/Chicago|États-Unis (Centre)" \
  "America/Denver|États-Unis (Montagne)" \
  "America/Los_Angeles|États-Unis (Ouest)" \
  "America/Anchorage|États-Unis (Alaska)" \
  "Pacific/Honolulu|États-Unis (Hawaï)" \
  "America/Toronto|Canada (Est)" \
  "America/Vancouver|Canada (Ouest)" \
  "America/Mexico_City|Mexique" \
  "America/Bogota|Colombie" \
  "America/Lima|Pérou" \
  "America/Santiago|Chili" \
  "America/Buenos_Aires|Argentine" \
  "America/Sao_Paulo|Brésil (São Paulo)" \
  "America/Caracas|Venezuela" \
  "Asia/Dubai|Émirats Arabes Unis" \
  "Asia/Riyadh|Arabie Saoudite" \
  "Asia/Jerusalem|Israël" \
  "Asia/Beirut|Liban" \
  "Asia/Baghdad|Irak" \
  "Asia/Tehran|Iran" \
  "Asia/Karachi|Pakistan" \
  "Asia/Kolkata|Inde" \
  "Asia/Dhaka|Bangladesh" \
  "Asia/Colombo|Sri Lanka" \
  "Asia/Kathmandu|Népal" \
  "Asia/Almaty|Kazakhstan" \
  "Asia/Tashkent|Ouzbékistan" \
  "Asia/Bangkok|Thaïlande" \
  "Asia/Ho_Chi_Minh|Vietnam" \
  "Asia/Jakarta|Indonésie (Ouest)" \
  "Asia/Singapore|Singapour" \
  "Asia/Kuala_Lumpur|Malaisie" \
  "Asia/Manila|Philippines" \
  "Asia/Shanghai|Chine" \
  "Asia/Hong_Kong|Hong Kong" \
  "Asia/Taipei|Taïwan" \
  "Asia/Seoul|Corée du Sud" \
  "Asia/Tokyo|Japon" \
  "Australia/Perth|Australie (Ouest)" \
  "Australia/Adelaide|Australie (Centre)" \
  "Australia/Sydney|Australie (Est)" \
  "Pacific/Auckland|Nouvelle-Zélande" \
  "Pacific/Fiji|Fidji" \
  "UTC|UTC"

pick "Keyboard layout (console):" KEYMAP \
  "us|English (US) QWERTY" \
  "us-acentos|English (US) International (accents)" \
  "uk|English (UK) QWERTY" \
  "be-latin1|Belge AZERTY" \
  "fr|Français AZERTY" \
  "fr-latin9|Français AZERTY (latin9)" \
  "fr_CH|Français Suisse QWERTZ" \
  "de|Allemand QWERTZ" \
  "de-latin1|Allemand QWERTZ (latin1)" \
  "at|Autrichien QWERTZ" \
  "ch|Suisse QWERTZ" \
  "nl|Néerlandais QWERTY" \
  "es|Espagnol QWERTY" \
  "es-cp850|Espagnol QWERTY (cp850)" \
  "pt-latin1|Portugais QWERTY (latin1)" \
  "br-abnt2|Portugais Brésilien ABNT2" \
  "it|Italien QWERTY" \
  "it-latin1|Italien QWERTY (latin1)" \
  "pl2|Polonais QWERTY" \
  "ru|Russe" \
  "ua|Ukrainien" \
  "cz-lat2|Tchèque QWERTY (latin2)" \
  "sk-qwerty|Slovaque QWERTY" \
  "hu|Hongrois QWERTY" \
  "ro|Roumain QWERTY" \
  "trq|Turc Q" \
  "trf|Turc F" \
  "jp106|Japonais 106 touches" \
  "sv-latin1|Suédois QWERTY (latin1)" \
  "no-latin1|Norvégien QWERTY (latin1)" \
  "dk-latin1|Danois QWERTY (latin1)" \
  "fi-latin1|Finnois QWERTY (latin1)" \
  "gr|Grec" \
  "il|Hébreu" \
  "arabic|Arabe" \
  "dvorak|Dvorak (US)" \
  "dvorak-l|Dvorak gauche" \
  "dvorak-r|Dvorak droite" \
  "colemak|Colemak"

pick "System locale:" LOCALE \
  "en_US.UTF-8|English (US)" \
  "en_GB.UTF-8|English (UK)" \
  "fr_BE.UTF-8|Français (Belgique)" \
  "fr_FR.UTF-8|Français (France)" \
  "fr_CH.UTF-8|Français (Suisse)" \
  "de_DE.UTF-8|Deutsch (Deutschland)" \
  "de_AT.UTF-8|Deutsch (Österreich)" \
  "de_CH.UTF-8|Deutsch (Schweiz)" \
  "nl_BE.UTF-8|Nederlands (België)" \
  "nl_NL.UTF-8|Nederlands (Nederland)" \
  "es_ES.UTF-8|Español (España)" \
  "es_MX.UTF-8|Español (México)" \
  "pt_PT.UTF-8|Português (Portugal)" \
  "pt_BR.UTF-8|Português (Brasil)" \
  "it_IT.UTF-8|Italiano (Italia)" \
  "pl_PL.UTF-8|Polski (Polska)" \
  "ru_RU.UTF-8|Русский (Россия)" \
  "uk_UA.UTF-8|Українська (Україна)" \
  "cs_CZ.UTF-8|Čeština (Česká republika)" \
  "sk_SK.UTF-8|Slovenčina (Slovensko)" \
  "hu_HU.UTF-8|Magyar (Magyarország)" \
  "ro_RO.UTF-8|Română (România)" \
  "tr_TR.UTF-8|Türkçe (Türkiye)" \
  "ja_JP.UTF-8|日本語 (日本)" \
  "zh_CN.UTF-8|中文 (中国大陆)" \
  "zh_TW.UTF-8|中文 (台灣)" \
  "ko_KR.UTF-8|한국어 (대한민국)" \
  "ar_SA.UTF-8|العربية (المملكة العربية السعودية)" \
  "he_IL.UTF-8|עברית (ישראל)" \
  "hi_IN.UTF-8|हिन्दी (भारत)" \
  "sv_SE.UTF-8|Svenska (Sverige)" \
  "nb_NO.UTF-8|Norsk bokmål (Norge)" \
  "da_DK.UTF-8|Dansk (Danmark)" \
  "fi_FI.UTF-8|Suomi (Suomi)" \
  "el_GR.UTF-8|Ελληνικά (Ελλάδα)" \
  "C.UTF-8|C (POSIX minimal)"

pick "Enable GTA Online fix? (blocks IP to play on linux)" GTA_FIX \
  "false|No" \
  "true|Yes"

pick "Enable Flatpak?" FLATPAK \
  "false|No" \
  "true|Yes"

pick "Enable virtualization? (libvirt, virt-manager...)" VIRTUALIZATION \
  "false|No" \
  "true|Yes"

pick "Enable automatic updates?" AUTOUPDATE \
  "true|Yes" \
  "false|No"

AUTOUPDATE_INTERVAL="1h"
if [[ "$AUTOUPDATE" == "true" ]]; then
  echo -e "\n${BOLD}Auto-update check interval (e.g. 1h, 6h, 12h, 24h) [default: 1h]:${NC}"
  read -rp "Interval: " input_interval
  [[ -n "$input_interval" ]] && AUTOUPDATE_INTERVAL="$input_interval"
fi

# ── Write local.nix ───────────────────────────────────────────────────────────
info "Writing configuration to local.nix..."

sed -i "s/hardware\.myGpu[[:space:]]*=[[:space:]]*\"[^\"]*\"/hardware.myGpu     = \"${GPU}\"/"       hosts/roudix/local.nix
sed -i -E "s/hardware\.nvidiaLaptop[[:space:]]*=[[:space:]]*(true|false)/hardware.nvidiaLaptop = ${NVIDIA_LAPTOP}/" hosts/roudix/local.nix
sed -i "s/hardware\.myCpu[[:space:]]*=[[:space:]]*\"[^\"]*\"/hardware.myCpu     = \"${CPU}\"/"       hosts/roudix/local.nix
sed -i "s/hardware\.myKernel[[:space:]]*=[[:space:]]*\"[^\"]*\"/hardware.myKernel = \"${KERNEL}\"/"  hosts/roudix/local.nix
sed -i "s/roudix\.browsers[[:space:]]*=[[:space:]]*\[[^]]*\]/roudix.browsers = [\"${BROWSER}\"]/"    hosts/roudix/local.nix
sed -i -E "s/roudix\.zen\.enable[[:space:]]*=[[:space:]]*(true|false)/roudix.zen.enable           = ${ZEN}/" hosts/roudix/local.nix
sed -i "s/roudix\.desktop\.type[[:space:]]*=[[:space:]]*\"[^\"]*\"/roudix.desktop.type = \"${DE}\"/" hosts/roudix/local.nix
sed -i "s/roudix\.shell[[:space:]]*=[[:space:]]*\"[^\"]*\"/roudix.shell = \"${SHELL_DEFAULT}\"/" hosts/roudix/local.nix
sed -i -E "s/roudix\.vmGuest\.enable[[:space:]]*=[[:space:]]*(true|false)/roudix.vmGuest.enable       = ${VM_GUEST}/" hosts/roudix/local.nix
sed -i -E "s/roudix\.gaming\.enable[[:space:]]*=[[:space:]]*(true|false)/roudix.gaming.enable        = ${GAMING}/" hosts/roudix/local.nix
sed -i "s|time\.timeZone[[:space:]]*=[[:space:]]*\"[^\"]*\"|time.timeZone                        = \"${TIMEZONE}\"|"         hosts/roudix/local.nix
sed -i "s|environment\.sessionVariables\.TZ[[:space:]]*=[[:space:]]*\"[^\"]*\"|environment.sessionVariables.TZ      = \"${TIMEZONE}\"|" hosts/roudix/local.nix
sed -i "s|i18n\.defaultLocale[[:space:]]*=[[:space:]]*\"[^\"]*\"|i18n.defaultLocale                   = \"${LOCALE}\"|"       hosts/roudix/local.nix
sed -i "s|console\.keyMap[[:space:]]*=[[:space:]]*\"[^\"]*\"|console.keyMap                       = \"${KEYMAP}\"|"           hosts/roudix/local.nix
sed -i -E "s/roudix\.hosts\.gtaFix\.enable[[:space:]]*=[[:space:]]*(true|false)/roudix.hosts.gtaFix.enable  = ${GTA_FIX}/" hosts/roudix/local.nix
sed -i -E "s/roudix\.flatpak\.enable[[:space:]]*=[[:space:]]*(true|false)/roudix.flatpak.enable       = ${FLATPAK}/" hosts/roudix/local.nix
sed -i -E "s/roudix\.virtualization\.enable[[:space:]]*=[[:space:]]*(true|false)/roudix.virtualization.enable = ${VIRTUALIZATION}/" hosts/roudix/local.nix
sed -i -E "s/roudix\.autoupdate\.enable[[:space:]]*=[[:space:]]*(true|false)/roudix.autoupdate.enable    = ${AUTOUPDATE}/" hosts/roudix/local.nix
sed -i "s/roudix\.autoupdate\.interval[[:space:]]*=[[:space:]]*\"[^\"]*\"/roudix.autoupdate.interval  = \"${AUTOUPDATE_INTERVAL}\"/" hosts/roudix/local.nix

success "local.nix configured."

# ── Summary ───────────────────────────────────────────────────────────────────
echo -e "\n${BOLD}══════════════════════════════════════${NC}"
success "Setup complete!"
echo -e "${BOLD}══════════════════════════════════════${NC}"
echo -e "
  ${BOLD}User          :${NC} $USERNAME
  ${BOLD}GPU           :${NC} $GPU
  ${BOLD}CPU           :${NC} $CPU
  ${BOLD}Kernel        :${NC} $KERNEL
  ${BOLD}Browser       :${NC} $BROWSER
  ${BOLD}Zen Browser   :${NC} $ZEN
  ${BOLD}Desktop       :${NC} $DE
  ${BOLD}Shell         :${NC} $SHELL_DEFAULT
  ${BOLD}VM Guest      :${NC} $VM_GUEST
  ${BOLD}Gaming        :${NC} $GAMING
  ${BOLD}Timezone      :${NC} $TIMEZONE
  ${BOLD}Locale        :${NC} $LOCALE
  ${BOLD}Keymap        :${NC} $KEYMAP
  ${BOLD}GTA Fix       :${NC} $GTA_FIX
  ${BOLD}Flatpak       :${NC} $FLATPAK
  ${BOLD}Virtualization:${NC} $VIRTUALIZATION
  ${BOLD}Auto-update   :${NC} $AUTOUPDATE $([ "$AUTOUPDATE" == "true" ] && echo "(every $AUTOUPDATE_INTERVAL)")
  ${BOLD}Config dir    :${NC} $INSTALL_DIR
"

# ── Smart apply (detect risky switch → boot) ────────────────────────────────
read -rp "Apply configuration now? [Y/n]: " confirm
confirm="${confirm:-Y}"
if [[ "$confirm" =~ ^[Yy]$ ]]; then
  info "Checking if 'switch' is safe..."
  cd "$INSTALL_DIR" || error "Failed to enter install directory."

  if dry_output=$(sudo nixos-rebuild switch --flake path:$(pwd)#roudix --dry-run 2>&1); then
    if echo "$dry_output" | grep -q "not recommended"; then
      warn "'switch' is not recommended by NixOS. Using 'boot' instead..."
      sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
      success "Configuration built with 'boot'."
      warn "Reboot required to apply the new configuration."
    else
      info "'switch' seems safe. Applying..."
      sudo nixos-rebuild switch --flake path:$(pwd)#roudix --accept-flake-config
      success "Configuration applied successfully!"

      warn "Please reboot your system to complete the setup."
    fi
  else
    warn "Dry-run failed. Using 'boot' as fallback..."
    sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
    success "Configuration built with 'boot'."
    warn "Reboot required to apply the new configuration."
  fi

  read -rp "Reboot now? [Y/n]: " reboot_now
  reboot_now="${reboot_now:-Y}"
  if [[ "$reboot_now" =~ ^[Yy]$ ]]; then
    sudo reboot
  fi

else
  warn "You can apply it later manually."
  echo -e "  ${CYAN}cd $INSTALL_DIR${NC}"
  echo -e "  ${CYAN}sudo nixos-rebuild boot --flake path:${pwd}#roudix --accept-flake-config${NC}"
  echo ""
  warn "Reboot required after applying the configuration."
fi
