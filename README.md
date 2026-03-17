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

---

## Structure

```
roudix/
├── flake.nix                 # Inputs & outputs
├── flake.lock
├── configuration.nix         # NixOS system config
├── hardware-configuration.nix
├── niri.nix                  # Niri compositor + UWSM
├── home.nix                  # Home Manager entry point
├── niri/
│   ├── config.kdl            # Niri config
│   └── noctalia.kdl          # Noctalia config
├── logo/
│   └── roudix-logo.png
└── modules/
    ├── fastfetch.nix         # Fastfetch + fish autostart
    ├── fish.nix              # Fish shell + rebuild alias
    ├── gaming.nix            # Steam, Gamescope, GameMode
    ├── gaming-home.nix       # User gaming packages
    ├── git.nix               # Git config
    ├── mangohud.nix          # MangoHud overlay
    ├── ssh.nix               # SSH + GitHub
    ├── gpu.nix               # GPU configuration
    └── cpu.nix               # CPU configuration
```

---

## Flake inputs

| Input | Source |
|-------|--------|
| nixpkgs | nixos-unstable |
| home-manager | nix-community/home-manager |
| noctalia | noctalia-dev/noctalia-shell |
| nix-cachyos-kernel | xddxdd/nix-cachyos-kernel |
| zen-browser | 0xc000022070/zen-browser-flake |

---

## Features

**Kernel & Performance**
- CachyOS kernel with NTSync enabled (`ntsync` module)
- ZRAM enabled (100% RAM, zstd, swappiness 150)
- zswap disabled
- Intel microcode up to date
- GameMode with AMD GPU optimizations

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

**Other**
- OBS Studio with obs-pipewire-audio-capture + obs-vkcapture
- GPU Screen Recorder
- OpenRGB for LED control
- Flatpak enabled and auto update
- GVfs for disk mounting in Nautilus
- Nerd Fonts (JetBrains, Noto, Iosevka)

---

## Installation

> ⚠️ **This config is built around my hardware and username. Follow every step carefully before rebuilding.**

### 1. Clone the repo

```bash
git clone git@github.com:roudinebwt/roudix ~/.config/roudix
cd ~/.config/roudix
```

### 2. Replace hardware-configuration.nix

replace the existing one by your own hardware config:

```bash
sudo cp  /etc/nixos/hardware-configuration.nix ~/.config/roudix/hardware-configuration.nix
```

### 3. Replace username and paths

This config uses the username `roudine` and home path `/home/roudine`. Replace every occurrence with your own:

```bash
# List all files containing roudine
grep -r "roudine" ~/.config/roudix/ --include="*.nix" -l
```

Files to update manually:

| File | What to change |
|------|----------------|
| `configuration.nix` | `users.users.roudine` → your username |
| `home.nix` | `home.username` and `home.homeDirectory` |
| `modules/fish.nix` | the `rebuild` alias path |
| `modules/fastfetch.nix` | logo `source` path |
| `modules/ssh.nix` | `identityFile` path |
| `modules/git.nix` | your name and email |
| `modules/gpu.nix` | `hardware.myGpu` → "amd", "nvidia" or "intel" |
| `modules/gpu.nix` | `hardware.myCpu` → "amd" or "intel" |

### 4. Update the rebuild alias

In `modules/fish.nix`:

```nix
shellAliases = {
  rebuild = "sudo nixos-rebuild switch --flake /home/YOURUSERNAME/.config/roudix#roudix";
};
```

### 5. Update the disk mount

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
### 6. Set your GPU and CPU type

In `configuration.nix`:
```nix
hardware.myGpu = "amd"; # Change to "nvidia" or "intel"
hardware.myCpu = "intel"; # Change to "amd" or let "intel"
```

### 7. Build

```bash
sudo nixos-rebuild switch --flake .#roudix
```

Once built, use the `rebuild` alias from fish for all future updates.

---

## Updating

```bash
rebuild
```

To update flake inputs:

```bash
update && rebuild
```
