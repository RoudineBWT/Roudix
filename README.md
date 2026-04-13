<div align="center">
<img src="assets/logo/roudix-logo.png" width="250"/>

# Roudix
### NixOS configuration — Niri · Hyprland · Noctalia · DMS · Caelestia · CachyOS Kernel

![NixOS](https://img.shields.io/badge/NixOS-unstable-5277C3?style=for-the-badge&logo=nixos&logoColor=white)
![Wayland](https://img.shields.io/badge/Wayland-Niri%20%2F%20Hyprland-FFB800?style=for-the-badge&logo=wayland&logoColor=black)
![Kernel](https://img.shields.io/badge/Kernel-CachyOS-FF4500?style=for-the-badge&logo=linux&logoColor=white)

</div>

---

## Hardware

| Component | Model |
|-----------|-------|
| CPU | Intel Core i5-13600KF |
| GPU | AMD Radeon RX 7900 XT |

---

## Stack

| Layer | Choice |
|-------|--------|
| OS | Roudix (NixOS unstable) |
| Kernel | CachyOS (linux-cachyos-lts-lto-v3) |
| Bootloader | Limine |
| Compositor | Niri (scrollable tiling) · Hyprland (dynamic tiling) |
| Graphical shell | Noctalia · DankMaterialShell · Caelestia |
| Display Manager | GDM / Ly / plasma-login-manager |
| Terminal | Ghostty |
| Shell | Fish · Bash |
| Browser | Configurable (Brave, Helium, Vivaldi, Firefox, LibreWolf, Chromium, Zen) |
| File Manager | Nautilus |
| Editor | Zed |
| Music | Spotify + Spicetify (Comfy theme) |

---

## Documentation

| | |
|-|-|
| 🖥️ [Desktop & shells](docs/desktop.md) | Switch compositors and graphical shells, personal overrides (Niri, Hyprland, GNOME, KDE) |
| ⚡ [Aliases & functions](docs/aliases.md) | All shell aliases and functions — `roudix-switch`, `roudix-shell-switch`, `rebuild`… |
| 🚀 [Installation](docs/installation.md) | Automated and manual installation guide |
| ✨ [Features](docs/features.md) | Full feature list by desktop environment |
| 🔄 [Auto-update](docs/autoupdate.md) | Automatic git pull + rebuild configuration |

---

## Structure

```
roudix/
├── roudix-installer.sh              # Bash-based installer
├── flake.nix                        # Inputs & outputs
├── flake.lock
├── docs/                            # Documentation
│   ├── desktop.md                   # Desktop environments & graphical shells
│   ├── aliases.md                   # Shell aliases & functions
│   ├── installation.md              # Installation guide
│   ├── features.md                  # Feature list
│   └── autoupdate.md                # Auto-update configuration
│
├── hosts/
│   └── roudix/                      # Single host — DE selected via roudix.desktop.type
│       ├── configuration.nix
│       ├── username.nix             # gitignored — your username (see installation)
│       ├── local.nix                # gitignored — your personal system overrides
│       ├── local.nix.example        # copy this to local.nix to get started
│       └── hardware-configuration.nix
│
├── home/                            # Home Manager — user-level configuration
│   ├── common.nix                   # Shared home config (all users & DEs)
│   ├── local.nix                    # gitignored — your personal home overrides
│   ├── local.nix.example            # copy this to home/local.nix to get started
│   ├── niri.nix                     # Home config for Niri (shell-aware)
│   ├── gnome.nix                    # Home config for GNOME (wallpaper, theme, icons, cursor)
│   ├── gnome-extensions.nix         # GNOME extensions — packages, enabled UUIDs, dconf settings
│   ├── kde.nix                      # Home config for KDE (wallpaper, theme, icons, cursor)
│   ├── hyprland.nix                 # Home config for Hyprland (shell-aware)
│   └── shell-modules.nix            # Shared shell module imports (noctalia, dms, caelestia)
│
├── dotfiles/                        # Raw config files managed by Home Manager
│   ├── easyeffects/                 # EasyEffects presets
│   ├── fastfetch/
│   │   └── roudix.txt               # Default Roudix ASCII logo for fastfetch
│   ├── niri/                        # Niri + Noctalia dotfiles
│   │   ├── cfg/                     # Niri split config
│   │   ├── config.kdl               # include injected by Nix at build time
│   │   └── noctalia.kdl             # Noctalia shell config
│   ├── niri-dms/                    # Niri + DankMaterialShell dotfiles
│   ├── niri-caelestia/              # Niri + Caelestia dotfiles
│   ├── hyprland/                    # Hyprland + Noctalia dotfiles
│   │   ├── cfg/                     # Hyprland split config
│   │   └── hyprland.conf            # source injected by Nix at build time
│   ├── hyprland-dms/                # Hyprland + DankMaterialShell dotfiles
│   ├── hyprland-caelestia/          # Hyprland + Caelestia dotfiles
│   └── perso/                       # Personal config (gitignored)
│
├── pkgs/
│   └── roudix-switcher/             # Roudix Desktop Switcher GUI package
│
└── modules/
    ├── desktop/                     # Desktop environment modules (NixOS-level)
    │   ├── default.nix              # Desktop options (roudix.desktop.type + roudix.desktop.shell)
    │   ├── niri.nix                 # Niri + polkit
    │   ├── hyprland.nix             # Hyprland + UWSM + polkit + xdg-portal
    │   ├── gnome.nix                # GNOME
    │   └── kde.nix                  # KDE Plasma 6 + plasma-login-manager
    │
    ├── system/                      # NixOS system-level modules
    │   ├── autoupdate.nix           # Auto git pull + rebuild on config changes
    │   ├── binary-caches.nix        # Nix binary caches (substituters + trusted keys)
    │   ├── boot.nix                 # Limine bootloader + multi-OS entries
    │   ├── boot.local.nix           # gitignored — your personal boot entries
    │   ├── boot.local.nix.example   # copy this to boot.local.nix to get started
    │   ├── browser.nix              # Browser selection (roudix.browsers + roudix.zen.enable)
    │   ├── common.nix               # Shared system config (all hosts)
    │   ├── cpu.nix                  # CPU configuration (Intel/AMD microcode)
    │   ├── environment.nix          # Environment variables
    │   ├── flatpak.nix              # Flatpak service + auto update
    │   ├── fstrim.nix               # fstrim for SSD/NVMe
    │   ├── gaming.nix               # Steam, Gamescope, ananicy-cpp, game-performance
    │   ├── gpu.nix                  # GPU configuration (AMD/NVIDIA/Intel)
    │   ├── hosts-gta.nix            # BattlEye hosts block (GTA fix, optional)
    │   ├── kernel.nix               # CachyOS kernel variant selection
    │   ├── pipewire.nix             # PipeWire audio configuration
    │   ├── update.nix               # Flake update configuration
    │   ├── version.nix              # Roudix OS branding (os-release, distroName)
    │   ├── virtualization.nix       # QEMU/KVM (disabled by default)
    │   └── vm-guest.nix             # VM guest optimizations (clipboard, QEMU agent, Spice)
    │
    └── home/                        # Home Manager user-level modules
        ├── bash.nix                 # Bash shell config + roudix-switch + roudix-shell-switch
        ├── fastfetch.nix            # Fastfetch + fish autostart
        ├── fish.nix                 # Fish shell + aliases + roudix-switch + roudix-shell-switch
        ├── gaming-home.nix          # User gaming packages (proton, mangohud...)
        ├── git.nix                  # Git config
        ├── mangohud.nix             # MangoHud overlay
        ├── papirus-folders.nix      # Papirus folder color configuration
        ├── spicetify.nix            # Spotify + Spicetify (Comfy theme)
        └── ssh.nix                  # SSH + GitHub
```

---

## Flake inputs

| Input | Source |
|-------|--------|
| nixpkgs | nixos-unstable |
| nixpkgs-stable | nixos-25.11 |
| home-manager | nix-community/home-manager |
| noctalia | noctalia-dev/noctalia-shell |
| noctalia-qs | noctalia-dev/noctalia-qs |
| caelestia-shell | caelestia-dots/shell |
| dms | AvengeMedia/DankMaterialShell |
| nix-cachyos-kernel | xddxdd/nix-cachyos-kernel |
| zen-browser | 0xc000022070/zen-browser-flake |
| spicetify-nix | Gerg-L/spicetify-nix |
| millennium | SteamClientHomebrew/Millennium |
| helium | AlvaroParker/helium-nix |
| nix-flatpak | gmodena/nix-flatpak |
| glf-os | framagit.org/gaming-linux-fr/glf-os |
| plasma-manager | nix-community/plasma-manager |

---

## Personal dotfiles

Personal config files live in `dotfiles/perso/` — they are gitignored (except for `dotfiles/perso/README.md`) and never touched by `git pull` or the auto-updater.

See [`dotfiles/perso/README.md`](dotfiles/perso/README.md) for structure and usage.

For compositor-level overrides (monitors, keybinds, gaps…), use the generated user override files instead — they are managed by home-manager and safe from `git pull`. See [Desktop & shells](docs/desktop.md#personal-compositor-overrides) for details.
