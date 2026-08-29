<div align="center">
<img src="assets/logo/roudix-logo.png" width="250"/>

# Roudix
### NixOS configuration (Unstable) — Various Wayland compositor (hyprland, niri, mangowc and umbriel) · Gnome and KDE · CachyOS Kernel

![NixOS](https://img.shields.io/badge/NixOS-unstable-5277C3?style=for-the-badge&logo=nixos&logoColor=white)
![Wayland](https://img.shields.io/badge/Wayland-Niri%20%2F%20Hyprland-FFB800?style=for-the-badge&logo=wayland&logoColor=black)
![Kernel](https://img.shields.io/badge/Kernel-CachyOS-FF4500?style=for-the-badge&logo=linux&logoColor=white)

<br/>

| Niri + DankMaterialShell | Niri + Noctalia |
|:---:|:---:|
| ![Niri + DMS](assets/screenshot/my-dms-setup.png) | ![Niri + Noctalia](assets/screenshot/my-noctalia-setup.png) |

<sub>Personal customization — yours will look different depending on your setup 👀</sub>

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
| Kernel | CachyOS (Choose your kernel variant see in[Features](docs/features.md) or in [Installation](docs/installation.md) ) |
| Bootloader | Limine (default) · systemd-boot |
| Compositor | Niri (scrollable tiling) · Hyprland (dynamic tiling) · MangoWC · Umbriel (scrollable tiling, Noctalia-native) |
| Graphical shell | Noctalia · DankMaterialShell · Caelestia |
| Desktop Environment | KDE Plasma · Gnome |
| Display Manager | DMS Greeter (Dms only) · Noctalia Greeter (noctalia only) · plasma-login-manager (KDE only) · GDM (Gnome only) |
| Terminal | Configurable (Ghossty, Kitty, Foot, Wzertem, Konsole, Ptyxis) |
| Shell | Fish · Bash |
| Browser | Configurable (Brave, Helium, Vivaldi, Firefox, LibreWolf, Chromium, Zen Twilight) |
| File Manager | Configurable (Nautilus, Thunar, Dolphin, Nemo) |
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
│   ├── niri-custom.nix.example      # optional — copy to niri-custom.nix for niri overrides (auto-imported)
│   ├── umbriel-custom.nix.example   # optional — copy to umbriel-custom.nix for Umbriel overrides (auto-imported)
│   ├── mango-custom.nix.example     # optional — copy to mango-custom.nix for MangoWC overrides (auto-imported)
│   ├── gnome.nix                    # Home config for GNOME (wallpaper, theme, icons, cursor)
│   ├── gnome-extensions.nix         # GNOME extensions — packages, enabled UUIDs, dconf settings
│   ├── kde.nix                      # Home config for KDE (wallpaper, theme, icons, cursor)
│   ├── hyprland.nix                 # Home config for Hyprland (shell-aware)
│   ├── mangowc.nix                  # Home config for MangoWC (screenshot.sh, packages) — text-based, no typed Nix schema
│   └── shell-modules.nix            # Shared shell module imports (noctalia, dms, caelestia)
│
├── dotfiles/                        # Raw config files managed by Home Manager
│   ├── easyeffects/                 # EasyEffects presets
│   ├── fastfetch/
│   │   └── roudix.txt               # Default Roudix ASCII logo for fastfetch
│   # niri/, niri-dms/ removed — niri config is now fully
│   # Nix-native (see modules/home/desktop/niri/ below).
│   ├── hyprland/                    # Hyprland + Noctalia dotfiles
│   │   └── cfg/                     # Hyprland split config (managed by user — .conf, .lua, etc.)
│   ├── hyprland-dms/                # Hyprland + DankMaterialShell dotfiles
│   ├── hyprland-caelestia/          # Hyprland + Caelestia dotfiles
│   └── perso/                       # Personal config (gitignored)
│
├── pkgs/
│   ├── roudix-branding              # Roudix Branding package
│   ├── roudix-kernel-switcher       # Roudix Kernel 
│   ├── roudix-switcher/             # Roudix Desktop Switcher GUI package
│   └──   roudix-scheduler-switcher    # Scheduler Switcher GUI package
│
└── modules/
    ├── system/                      # NixOS system-level modules
    │   ├── desktop/                 # Desktop environment modules (NixOS-level)
    │   ├── default.nix              # Desktop options (roudix.desktop.type + roudix.desktop.shell)
    │   ├── niri.nix                 # Niri + polkit
    │   ├── hyprland.nix             # Hyprland + UWSM + polkit + xdg-portal
    │   ├── gnome.nix                # GNOME
    │   ├── kde.nix                  # KDE Plasma 6 + plasma-login-manager
    │   ├── mango.nix                # Mangowc + polkit
    │   └── umbriel.nix              # Umbriel + polkit
    │
    ├── autoupdate.nix           # Auto git pull + rebuild on config changes
    ├── binary-caches.nix        # Nix binary caches (substituters + trusted keys)
    ├── boot.nix                 # Limine bootloader + multi-OS entries
    ├── boot.local.nix           # gitignored — your personal boot entries
    ├── boot.local.nix.example   # copy this to boot.local.nix to get started
    ├── browser.nix              # Browser selection (roudix.browsers + roudix.zen.enable)
    ├── common.nix               # Shared system config (all hosts)
    ├── cpu.nix                  # CPU configuration (Intel/AMD microcode + i2c modules)
    ├── environment.nix          # Environment variables
    ├── flatpak.nix              # Flatpak service + auto update
    ├── fstrim.nix               # fstrim for SSD/NVMe
    ├── gaming.nix               # Steam, Gamescope, ananicy-cpp, game-performance
    ├── gpu/                     # GPU configuration (AMD/NVIDIA/Intel/VM — split per vendor)
    ├── hosts-gta.nix            # BattlEye hosts block (GTA fix, optional)
    ├── kernel.nix               # CachyOS kernel variant selection
    ├── matrix.nix               # Matrix client selection (roudix.matrixClient)
    ├── appimage.nix             # AppImage support
    ├── openlinkhub.nix          # OpenLinkHub — Corsair iCUE Link driver + RAM RGB (roudix.memory.*)
    ├── openrgb.nix              # OpenRGB LED control
    ├── roudix-rgb.nix           # RGB controller routing (openlinkhub / openrgb / none)
    ├── pipewire.nix             # PipeWire audio + rnnoise noise suppression
    ├── update.nix               # Flake update configuration
    ├── version.nix              # Roudix OS branding (os-release, distroName)
    ├── virtualization.nix       # QEMU/KVM (disabled by default)
    └── vm-guest.nix             # VM guest optimizations (clipboard, QEMU agent, Spice)
    └── # filemanager, terminal option to choose your favorite terminal and file manager do it via local.nix in host/roudix/
    │
    └── home/                        # Home Manager user-level modules
        ├── bash.nix                 # Bash shell config + roudix-switch + roudix-shell-switch
        ├── fastfetch.nix            # Fastfetch + fish autostart
        ├── fish.nix                 # Fish shell + aliases + roudix-switch + roudix-shell-switch
        ├── gaming-home.nix          # User gaming packages (proton, mangohud...)
        ├── git.nix                  # Git config
        ├── mangohud.nix             # MangoHud overlay
        ├── papirus-icon.nix         # Papirus icon theme
        ├── papirus-folders.nix      # Papirus folder color configuration
        ├── tela-icon.nix            # Tela icon theme
        ├── spicetify.nix            # Spotify + Spicetify (Comfy theme)
        ├── ssh.nix                  # SSH + GitHub
        ├── # mango and hyprland will soon get the same approch to niri and umbriel
        └── desktop/                 # Per-compositor Home Manager config (Nix-native)
            ├── niri/                # programs.niri.settings, split by topic, shell-aware
            │   ├── default.nix      # assembles settings, live-theme include, packages
            │   ├── _general.nix     # environment, autostart, cursor (shell-aware)
            │   ├── _animation.nix
            │   ├── _input.nix
            │   ├── _layout.nix
            │   ├── _output.nix      # outputs + named workspaces
            │   ├── _ws.nix          # shared workspace-icon glyph constants
            │   ├── _rules-common.nix
            │   ├── _rules-noctalia.nix / _rules-dms.nix
            │   ├── _binds-noctalia.nix / _binds-dms.nix
            │   └── _include-noctalia.nix / _include-dms.nix  # appends live-theme `include` to niri-flake's rendered config
            └── umbriel/             # programs.umbriel.settings, split by topic (Noctalia-only)
                ├── default.nix
                ├── _general.nix / _appearance.nix / _animation.nix / _input.nix
                ├── _layout.nix / _output.nix / _binds.nix / _rules.nix
                └── _include-noctalia.nix  # loads noctalia.toml (Umbriel's native live-theme include)
```

---

## Flake inputs

| Input | Source |
|-------|--------|
| nixpkgs | [nixos-unstable](https://github.com/NixOS/nixpkgs/tree/nixos-unstable) |
| nixpkgs-stable | [nixos-26.05](https://github.com/NixOS/nixpkgs/tree/nixos-26.05) |
| niri | [epireyn/niri-flake](https://github.com/epireyn/niri-flake) |
| home-manager | [nix-community/home-manager](https://github.com/nix-community/home-manager) |
| noctalia | [noctalia-dev/noctalia](https://github.com/noctalia-dev/noctalia) |
| umbriel | [noctalia-dev/umbriel](https://github.com/noctalia-dev/umbriel) |
| caelestia-shell | [caelestia-dots/shell](https://github.com/caelestia-dots/shell) |
| dms | [AvengeMedia/DankMaterialShell](https://github.com/AvengeMedia/DankMaterialShell) |
| nix-cachyos-kernel | [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel) |
| chaotic | [chaotic-cx/nyx](https://github.com/chaotic-cx/nyx) |
| zen-browser | [0xc000022070/zen-browser-flake](https://github.com/0xc000022070/zen-browser-flake) |
| spicetify-nix | [Gerg-L/spicetify-nix](https://github.com/Gerg-L/spicetify-nix) |
| millennium | [SteamClientHomebrew/Millennium](https://github.com/SteamClientHomebrew/Millennium) |
| helium | [x13-me/helium-nix](https://github.com/x13-me/helium-nix) |
| nix-flatpak | [gmodena/nix-flatpak](https://github.com/gmodena/nix-flatpak) |
| plasma-manager | [nix-community/plasma-manager](https://github.com/nix-community/plasma-manager) |
| brave-previews | [roudinebwt/brave-preview](https://github.com/roudinebwt/brave-preview) |
| roudix-caches | [RoudineBWT/Roudix-caches](https://github.com/RoudineBWT/Roudix-caches) |
| nix-gaming-edge | [powerofthe69/nix-gaming-edge](https://github.com/powerofthe69/nix-gaming-edge) |
---

## See also

| Project | Description |
|---------|-------------|
| [GLF OS](https://framagit.org/gaming-linux-fr/glf-os/glf-os) | NixOS-based gaming distro by Gaming Linux FR |

---

## Personal dotfiles

Personal config files live in `dotfiles/perso/` — they are gitignored (except for `dotfiles/perso/README.md`) and never touched by `git pull` or the auto-updater.

See [`dotfiles/perso/README.md`](dotfiles/perso/README.md) for structure and usage.

For compositor-level overrides (monitors, keybinds, gaps…), use the generated user override files instead — they are managed by home-manager and safe from `git pull`. See [Desktop & shells](docs/desktop.md#personal-compositor-overrides) for details.
