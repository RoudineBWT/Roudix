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
    [[ "$confirm" =~ ^[Yy]$ ]] || error "Installation cancelled."
    rm -rf "$INSTALL_DIR"
    mkdir -p "/home/${USERNAME}/.config"
    git clone https://github.com/RoudineBWT/Roudix "$INSTALL_DIR"
    success "Repository cloned."
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
nixos-generate-config --show-hardware-config > "hosts/roudix/hardware-configuration.nix"
success "hardware-configuration.nix generated."

# ── Copy local.nix ────────────────────────────────────────────────────────────
info "Creating local.nix from example..."
cp hosts/roudix/local.nix.example hosts/roudix/local.nix
success "local.nix created."

# ── Configuration questions ───────────────────────────────────────────────────
echo -e "\n${BOLD}══════════════════════════════════════${NC}"
info "Hardware & software configuration"
echo -e "${BOLD}══════════════════════════════════════${NC}"

pick "GPU:" GPU \
  "amd|AMD GPU" \
  "nvidia|NVIDIA GPU" \
  "intel|Intel integrated GPU"

pick "CPU:" CPU \
  "amd|AMD CPU" \
  "intel|Intel CPU"

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

pick "Enable GTA Online fix? (blocks IP causing long loading times)" GTA_FIX \
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
sed -i "s/hardware\.myCpu[[:space:]]*=[[:space:]]*\"[^\"]*\"/hardware.myCpu     = \"${CPU}\"/"       hosts/roudix/local.nix
sed -i "s/hardware\.myKernel[[:space:]]*=[[:space:]]*\"[^\"]*\"/hardware.myKernel = \"${KERNEL}\"/"  hosts/roudix/local.nix
sed -i "s/roudix\.chromium[[:space:]]*=[[:space:]]*\"[^\"]*\"/roudix.chromium    = \"${BROWSER}\"/"  hosts/roudix/local.nix
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
read -rp "Apply configuration now? [y/N]: " confirm
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

  read -rp "Reboot now? [y/N]: " reboot_now
  if [[ "$reboot_now" =~ ^[Yy]$ ]]; then
    sudo reboot
  fi

else
  warn "You can apply it later manually."
  echo -e "  ${CYAN}cd $INSTALL_DIR${NC}"
  echo -e "  ${CYAN}sudo nixos-rebuild switch --flake .#roudix --accept-flake-config${NC}"
  echo ""
  warn "Reboot required after applying the configuration."
fi
