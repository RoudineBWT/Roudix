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
info "Cloning Roudix into ${INSTALL_DIR}..."

if [[ -d "$INSTALL_DIR" ]]; then
  warn "Directory $INSTALL_DIR already exists."
  read -rp "Delete and re-clone? [y/N]: " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || error "Installation cancelled."
  rm -rf "$INSTALL_DIR"
fi

mkdir -p "/home/${USERNAME}/.config"
git clone https://github.com/RoudineBWT/Roudix "$INSTALL_DIR"
success "Repository cloned."

cd "$INSTALL_DIR"

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
  "brave|Brave" \
  "helium|Helium" \
  "vivaldi|Vivaldi"

pick "Desktop environment:" DE \
  "niri|Niri" \
  "gnome|GNOME" \
  "kde|KDE Plasma"

# ── Write local.nix ───────────────────────────────────────────────────────────
info "Writing configuration to local.nix..."

sed -i "s/hardware\.myGpu\s*=\s*\"[^\"]*\"/hardware.myGpu     = \"${GPU}\"/"      hosts/roudix/local.nix
sed -i "s/hardware\.myCpu\s*=\s*\"[^\"]*\"/hardware.myCpu     = \"${CPU}\"/"      hosts/roudix/local.nix
sed -i "s/hardware\.myKernel\s*=\s*\"[^\"]*\"/hardware.myKernel  = \"${KERNEL}\"/" hosts/roudix/local.nix
sed -i "s/roudix\.chromium\s*=\s*\"[^\"]*\"/roudix.chromium    = \"${BROWSER}\"/"  hosts/roudix/local.nix
sed -i "s/roudix\.desktop\.type\s*=\s*\"[^\"]*\"/roudix.desktop.type = \"${DE}\"/" hosts/roudix/local.nix

success "local.nix configured."

# ── Update username in flake.nix ──────────────────────────────────────────────
info "Updating username in flake.nix..."
sed -i "s/username\s*=\s*\"[^\"]*\"/username = \"${USERNAME}\"/" flake.nix
success "flake.nix updated."

# ── Git track local files ─────────────────────────────────────────────────────
info "Adding local files to git index (local only, never pushed)..."
git add -f hosts/roudix/hardware-configuration.nix
git add -f hosts/roudix/local.nix
success "Files tracked locally."

# ── Summary ───────────────────────────────────────────────────────────────────
echo -e "\n${BOLD}══════════════════════════════════════${NC}"
success "Setup complete!"
echo -e "${BOLD}══════════════════════════════════════${NC}"
echo -e "
  ${BOLD}User        :${NC} $USERNAME
  ${BOLD}GPU         :${NC} $GPU
  ${BOLD}CPU         :${NC} $CPU
  ${BOLD}Kernel      :${NC} $KERNEL
  ${BOLD}Browser     :${NC} $BROWSER
  ${BOLD}Desktop     :${NC} $DE
  ${BOLD}Config dir  :${NC} $INSTALL_DIR
"

# ── Smart apply (detect risky switch → boot) ────────────────────────────────
read -rp "Apply configuration now? [y/N]: " confirm
if [[ "$confirm" =~ ^[Yy]$ ]]; then
  info "Checking if 'switch' is safe..."
  cd "$INSTALL_DIR" || error "Failed to enter install directory."

  if dry_output=$(sudo nixos-rebuild switch --flake .#roudix --dry-run 2>&1); then
    if echo "$dry_output" | grep -q "not recommended"; then
      warn "'switch' is not recommended by NixOS. Using 'boot' instead..."
      sudo nixos-rebuild boot --flake .#roudix
      success "Configuration built with 'boot'."
      warn "Reboot required to apply the new configuration."
    else
      info "'switch' seems safe. Applying..."
      sudo nixos-rebuild switch --flake .#roudix
      success "Configuration applied successfully!"
      warn "Please reboot your system to complete the setup."
    fi
  else
    warn "Dry-run failed. Using 'boot' as fallback..."
    sudo nixos-rebuild boot --flake .#roudix
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
  echo -e "  ${CYAN}sudo nixos-rebuild switch --flake .#roudix${NC}"
  echo ""
  warn "Reboot required after applying the configuration."
fi
