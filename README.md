<div align="center">
<img src="logo/roudix-logo.png" width="250"/>

# Roudix
### NixOS configuration — Niri · Noctalia · CachyOS Kernel

![NixOS](https://img.shields.io/badge/NixOS-unstable-5277C3?style=for-the-badge&logo=nixos&logoColor=white)
![Wayland](https://img.shields.io/badge/Wayland-Niri-FFB800?style=for-the-badge&logo=wayland&logoColor=black)
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
| OS | NixOS unstable |
| Kernel | CachyOS (linux-cachyos-latest) |
| Compositor | Niri (scrollable tiling Wayland) |
| Shell | Noctalia |
| Display Manager | GDM |
| Terminal | Ghostty |
| Shell | Fish |
| Browser | Zen Browser |
| File Manager | Nautilus |
| Editor | Zed |
| Music | Spotify + Spicetify (Comfy theme) |

---

## Structure

```
roudix/
├── flake.nix                 # Inputs & outputs — set username here
├── flake.lock
├── configuration.nix         # NixOS system config
├── hardware-configuration.nix
├── niri.nix                  # Niri compositor + UWSM
├── home.nix                  # Home Manager entry point
├── dotfiles/
│   ├── easyeffects/          # EasyEffects presets
│   └── niri/
│       ├── config.kdl        # Niri config
│       └── noctalia.kdl      # Noctalia config
├── logo/
│   └── roudix-logo.png
└── modules/
    ├── cpu.nix               # CPU configuration (Intel/AMD microcode + OpenRGB)
    ├── fastfetch.nix         # Fastfetch + fish autostart
    ├── fish.nix              # Fish shell + aliases
    ├── fstrim.nix            # fstrim for SSD/NVMe
    ├── gaming.nix            # Steam, Gamescope, GameMode (system)
    ├── gaming-home.nix       # User gaming packages
    ├── git.nix               # Git config
    ├── gpu.nix               # GPU configuration (AMD/NVIDIA/Intel)
    ├── mangohud.nix          # MangoHud overlay
    ├── pipewire.nix          # PipeWire audio configuration
    ├── spicetify.nix         # Spotify + Spicetify (Comfy theme + marketplace)
    ├── ssh.nix               # SSH + GitHub
    └── virtualization.nix    # QEMU/KVM (disabled by default)
```

---

## Flake inputs

| Input | Source |
|-------|--------|
| nixpkgs | nixos-unstable |
| nixpkgs-stable | nixos-25.11 |
| home-manager | nix-community/home-manager |
| noctalia | noctalia-dev/noctalia-shell |
| nix-cachyos-kernel | xddxdd/nix-cachyos-kernel |
| zen-browser | 0xc000022070/zen-browser-flake |
| spicetify-nix | Gerg-L/spicetify-nix |
| glf-os | framagit.org/gaming-linux-fr/glf-os (NVIDIA drivers only) |

---

## Features

**Kernel & Performance**
- CachyOS kernel with NTSync enabled (`ntsync` module)
- ZRAM enabled (100% RAM, zstd, swappiness 150)
- zswap disabled
- CPU microcode auto-configured (Intel or AMD)
- GameMode with GPU optimizations

**Gaming**
- Steam + Proton-GE + Gamescope session
- Custom horizontal MangoHud overlay
- Controller support (Steam Hardware + game-devices-udev-rules)
- 32-bit support for Wine/Steam
- Heroic, Lutris, PrismLauncher

**Desktop**
- Niri scrollable tiling Wayland compositor
- Noctalia modern shell
- Capitaine Cursors White
- adw-gtk3 GTK theme + Papirus icons
- GNOME Polkit agent
- GDM display manager

**Music**
- Spotify patched with Spicetify
- Comfy theme
- Adblock + hide podcasts extensions
- Marketplace for additional themes & extensions

**Other**
- OBS Studio with obs-pipewire-audio-capture + obs-vkcapture
- GPU Screen Recorder
- OpenRGB for LED control (auto-configured per CPU)
- Flatpak enabled with daily auto-update
- GVfs for disk mounting in Nautilus
- Nerd Fonts (JetBrains, Noto, Iosevka)
- QEMU/KVM + Virt-Manager (optional, disabled by default)
- NVIDIA drivers sourced from GLF OS (auto-updated via `nix flake update`)

---

## Installation

> ⚠️ **Follow every step carefully before rebuilding.**

### 1. Clone the repo

> **If `git` is not installed** (fresh NixOS install):

```bash
nix-shell -p git --run "git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix"
```

> **Otherwise:**

```bash
git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix
cd ~/.config/roudix
```

### 2. Add binary caches (recommended for fresh installs)

Without this, Nix will compile everything from source which requires a lot of RAM and time. Run this before building:

```bash
sudo mkdir -p /etc/nix
sudo tee -a /etc/nix/nix.conf << EOF
substituters = https://cache.nixos.org https://attic.xuyh0120.win/lantian https://cache.garnix.io
trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY= lantian:EeAUQ+W+6r7EtwnmYjeVwx5kOGEBpjlBfPlzGlTNvHc= cache.garnix.io:CTFPyKSLcx5RMJKfLo5EEPUObbA78b0YQ2DTCJXqr9g=
EOF
sudo systemctl restart nix-daemon
```

Once built, your config takes over and manages the caches automatically.

### 3. Set your username

Open `flake.nix` and change **only this one line** — everything else adapts automatically:

```nix
username = "roudine"; # ← Change to your username
```

### 4. Replace hardware-configuration.nix

```bash
sudo cp /etc/nixos/hardware-configuration.nix ~/.config/roudix/hardware-configuration.nix
```

### 5. Set your GPU and CPU type

In `configuration.nix`:

```nix
hardware.myGpu = "amd"; # "amd", "nvidia" or "intel"
hardware.myCpu = "intel"; # "intel" or "amd"
```

> **NVIDIA note:** drivers are automatically pulled from GLF OS and kept up to date with `nix flake update`. Open drivers are enabled by default (Turing/RTX 20xx and newer). Set `open = false` in `modules/gpu.nix` for older GPUs (GTX series).

### 6. Update the disk mount

In `configuration.nix`, replace the UUID with your own (or remove the block entirely):

```bash
lsblk -f  # find your disk UUID
```

```nix
fileSystems."/mnt/gaming" = {
  device = "/dev/disk/by-uuid/YOUR-UUID-HERE";
  fsType = "btrfs";
  options = [ "defaults" "nofail" ];
};
```

### 7. Update git config

In `modules/git.nix`, set your name and email:

```nix
settings = {
  user.name = "yourname";
  user.email = "your@email.com";
};
```

### 8. Enable/disable optional modules

In `configuration.nix`:

```nix
roudix.gaming.enable = true;
roudix.pipewire.enable = true;
roudix.fstrim.enable = true;          # recommended for SSD/NVMe
roudix.virtualization.enable = false; # enable for QEMU/KVM
```

### 9. Build

> **If flakes and nix-command are not enabled yet** (fresh NixOS install):

```bash
nix --extra-experimental-features 'nix-command flakes' shell nixpkgs#git -c sudo nixos-rebuild switch --flake .#roudix
```

> **Otherwise:**

```bash
sudo nixos-rebuild switch --flake .#roudix
```

Once built, use the fish aliases for all future operations.

---

## Aliases

| Alias | Action |
|-------|--------|
| `rebuild` | Apply configuration immediately |
| `update` | Update flake inputs + apply |
| `cleanup` | Remove old generations + garbage collect |

---

## Updating

```bash
update
```
