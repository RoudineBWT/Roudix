<div align="center">
<img src="assets/logo/roudix-logo.png" width="250"/>

# Roudix
### NixOS configuration — Niri · Hyprland · Noctalia · CachyOS Kernel

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
| Shell | Noctalia |
| Display Manager | GDM / SDDM / plasma-login-manager |
| Terminal | Ghostty |
| Shell | Fish |
| Browser | Configurable (Brave, Helium, Vivaldi, Firefox, LibreWolf, Chromium, Zen) |
| File Manager | Nautilus |
| Editor | Zed |
| Music | Spotify + Spicetify (Comfy theme) |

---

## Structure

```
roudix/
├── roudix-installer.sh              # Bash-based installer
├── flake.nix                        # Inputs & outputs
├── flake.lock
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
│   ├── niri.nix                     # Home config for Niri + Noctalia
│   ├── gnome.nix                    # Home config for GNOME (wallpaper, theme, icons, cursor)
│   ├── kde.nix                      # Home config for KDE (wallpaper, theme, icons, cursor)
│   └── hyprland.nix                 # Home config for Hyprland + Noctalia
│
├── dotfiles/                        # Raw config files managed by Home Manager
│   ├── easyeffects/                 # EasyEffects presets
│   ├── fastfetch/
│   │   └── roudix.txt               # Default Roudix ASCII logo for fastfetch
│   ├── niri/
│   │   ├── cfg/                     # Niri split config
│   │   ├── config.kdl
│   │   └── noctalia.kdl             # Noctalia shell config
│   └── hyprland/
│   │   ├── cfg/                     # Hyprland split config
│   │   └── hyprland.conf
│   └── perso/                       # Personal config (gitignored)
│
├── pkgs/
│   └── roudix-switcher/             # Roudix Desktop Switcher package
│
└── modules/
    ├── desktop/                     # Desktop environment modules (NixOS-level)
    │   ├── default.nix              # Desktop option (roudix.desktop.type)
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
        ├── bash.nix                 # Bash shell config
        ├── fastfetch.nix            # Fastfetch + fish autostart
        ├── fish.nix                 # Fish shell + aliases + roudix-switch
        ├── gaming-home.nix          # User gaming packages (proton, mangohud...)
        ├── git.nix                  # Git config
        ├── mangohud.nix             # MangoHud overlay
        ├── papirus-folders.nix      # Papirus folder color configuration
        ├── spicetify.nix            # Spotify + Spicetify (Comfy theme)
        └── ssh.nix                  # SSH + GitHub
```

## Personal dotfiles

Personal config files live in `dotfiles/perso/` — they are gitignored (except for `dotfiles/perso/README.md`) and never touched by `git pull` or the auto-updater.

See [`dotfiles/perso/README.md`](dotfiles/perso/README.md) for structure and usage.

---


## Flake inputs

| Input | Source |
|-------|--------|
| nixpkgs | nixos-unstable |
| nixpkgs-stable | nixos-25.11 |
| home-manager | nix-community/home-manager |
| noctalia | noctalia-dev/noctalia-shell |
| noctalia-qs | noctalia-dev/noctalia-qs |
| nix-cachyos-kernel | xddxdd/nix-cachyos-kernel |
| zen-browser | 0xc000022070/zen-browser-flake |
| spicetify-nix | Gerg-L/spicetify-nix |
| millennium | SteamClientHomebrew/Millennium |
| helium | AlvaroParker/helium-nix |
| nix-flatpak | gmodena/nix-flatpak |
| glf-os | framagit.org/gaming-linux-fr/glf-os |

---

## Configurations

| Name | Description |
|------|-------------|
| `roudix` | Single config — desktop selected via `roudix.desktop.type` |

---

## Desktop environments

Switch desktop at any time with `roudix-switch <de>` or the **Roudix Desktop Switcher** GUI — no separate host needed.

| Value | Desktop | Notes |
|-------|---------|-------|
| `niri` | Niri + Noctalia | Default — scrollable tiling Wayland |
| `hyprland` | Hyprland + Noctalia | Dynamic tiling Wayland — launched via UWSM |
| `gnome` | GNOME 49.4 |
| `kde` | KDE Plasma 6 | plasma-login-manager, KDE Connect |

To change permanently, edit `hosts/roudix/local.nix`:

```nix
roudix.desktop.type = "niri"; # "niri", "hyprland", "gnome" or "kde"
```

Or use the fish function:

```fish
roudix-switch kde
```

> **Note:** `roudix-switch` uses `nh os boot` — changes apply on next reboot.

---

## Features

**Kernel & Performance**
- CachyOS kernel with NTSync enabled (`ntsync` module)
- 8 kernel variants available (set in `hosts/roudix/local.nix`)
- ZRAM enabled (100% RAM, zstd, swappiness 150)
- zswap disabled
- CPU microcode auto-configured (Intel or AMD)
- Intel: `split_lock_detect=off` applied automatically
- ananicy-cpp enabled (process priority daemon, CachyOS rules)

**Boot**
- Limine bootloader — modern, fast, multi-disk support
- Automatic UEFI entry rename to "Roudix"
- Multi-OS boot menu (Windows, other Linux distros on separate ESPs)
- Boot label shows Roudix name + NixOS release version

**Gaming**
- Steam + Proton-GE + Gamescope session
- Millennium Steam client patcher
- OBS capture env vars pre-configured (`OBS_VKCAPTURE`, `TZ`)
- Custom horizontal MangoHud overlay
- Controller support (Steam Hardware + game-devices-udev-rules)
- 32-bit support for Wine/Steam
- `game-performance` wrapper — switches CPU governor to performance for the duration of a game (usage: `game-performance %command%` in Steam launch options)
- `protonup-qt` on KDE, `protonplus` on other DEs

**Desktop (Niri)**
- Niri scrollable tiling Wayland compositor
- Noctalia modern shell
- Capitaine Cursors White
- adw-gtk3 + Papirus icons + Papirus Folders
- Discord with Vencord
- Element Desktop with gnome-libsecret / kwallet6 (auto-detected per DE)
- GNOME Polkit agent
- GDM display manager

**Desktop (Hyprland)**
- Hyprland dynamic tiling Wayland compositor launched via UWSM
- Noctalia modern shell
- xdg-desktop-portal-hyprland + gtk portal
- Capitaine Cursors White
- GNOME Polkit agent (started via systemd user service)
- swww wallpaper daemon
- grimblast screenshots

**Desktop (GNOME)**
- GNOME 49.4 (follows nixos-unstable branch)
- Curated extension set (blur, tiling, vitals, arcmenu...)
- Bloat removed via `environment.gnome.excludePackages`
- Papirus-Dark icon theme
- adw-gtk3-dark GTK theme (dark mode by default)
- Capitaine Cursors White
- Roudix wallpaper (light/dark based on system theme)
- `color-scheme = prefer-dark` applied via dconf
- Override wallpaper, theme, icons in `home/local.nix`

**Desktop (KDE)**
- KDE Plasma 6 with plasma-login-manager (Plasma 6.6+, nixpkgs unstable)
- KDE Connect enabled
- xdg-desktop-portal-kde
- Papirus-Dark icon theme
- Breeze Dark look & feel + color scheme
- Roudix Dark wallpaper on login screen and desktop
- Curated packages: partitionmanager, kcalc, digikam, vlc...
- Bloat removed (Discover excluded)
- Override wallpaper, panels, icon theme in `home/local.nix`

**Music**
- Spotify patched with Spicetify
- Comfy theme (local, customized)
- Adblock + hide podcasts extensions

**Browser**
- Configurable browser list via `roudix.browsers` option
- Supports `brave`, `helium` (via helium-nix flake), `vivaldi` (with ffmpeg codecs), `firefox`, `librewolf`, `chromium`, or `[]` for none
- Zen Browser available separately via `roudix.zen.enable = true` (disabled by default)

**Other**
- OBS Studio with pipewire + vkcapture plugins
- GPU Screen Recorder
- OpenRGB for LED control
- Flatpak with Flathub remote + daily auto-update (via nix-flatpak)
- Blueman Bluetooth manager
- QEMU/KVM + Virt-Manager (optional)
- VM guest optimizations module (clipboard sharing, auto-resize, QEMU agent, Spice)

---

## Installation

## Automated Installation

**Download the roudix-installer script**

```bash
nix-shell -p wget --run "wget https://github.com/RoudineBWT/Roudix/raw/refs/heads/main/roudix-installer.sh"
chmod +x roudix-installer.sh
./roudix-installer.sh
```

The installer handles everything interactively:
- Clones the repo, generates `hardware-configuration.nix`, creates all local config files
- **Detects other OSes automatically** via EFI NVRAM (`efibootmgr`) — no manual PARTUUID lookup needed
- **Detects GPU and CPU automatically** (`lspci` / `/proc/cpuinfo`) — pre-selects and asks for confirmation
- **Detects if running in a VM** (`systemd-detect-virt`) — pre-enables VM guest mode and warns that GPU/CPU detection may be inaccurate
- Asks about kernel, desktop, browser, locale, timezone, keymap, and optional modules
- Builds and applies the configuration

## Manual Installation

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

### 2. Set your username

Create the `username.nix` file with your username:

```bash
echo '"yourusername"' > ~/.config/roudix/hosts/roudix/username.nix
```

> This file is gitignored — it will never be overwritten by a `git pull`.

### 3. Replace hardware-configuration.nix

```bash
sudo cp /etc/nixos/hardware-configuration.nix ~/.config/roudix/hosts/roudix/hardware-configuration.nix
```

### 4. Create your local configs

**Never edit `configuration.nix` or `home/common.nix` directly** — they get overwritten on `git pull`.
Instead, create your local override files (all gitignored):

```bash
cp hosts/roudix/local.nix.example hosts/roudix/local.nix
cp home/local.nix.example home/local.nix
cp modules/system/boot.local.nix.example modules/system/boot.local.nix
```

Edit `hosts/roudix/local.nix` to match your hardware:

```nix
{ lib, ... }:
{
  roudix.desktop.type = "niri";               # "niri", "hyprland", "gnome" or "kde"
  hardware.myGpu      = "amd";                # "amd", "nvidia" or "intel"
  hardware.myCpu      = "intel";              # "intel" or "amd"
  hardware.myKernel   = "cachyos-lts-lto-v3"; # see below
  roudix.browsers     = [ "helium" ];         # "brave", "helium", "vivaldi", "firefox", "librewolf", "chromium" or []
  roudix.zen.enable   = false;                # set to true to also install Zen Browser

  # ── Locale / Timezone ───────────────────────────────────────────────────────
  time.timeZone                   = "Europe/Brussels"; # see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
  environment.sessionVariables.TZ = "Europe/Brussels"; # must match time.timeZone
  i18n.defaultLocale              = "en_US.UTF-8";     # system locale
  console.keyMap                  = "us";              # console keyboard layout
}
```

**Common timezone values:**

| Timezone | Region |
|----------|--------|
| `Europe/Brussels` | Belgium |
| `Europe/Paris` | France |
| `Europe/London` | United Kingdom |
| `Europe/Berlin` | Germany |
| `Europe/Amsterdam` | Netherlands |
| `America/New_York` | US East |
| `America/Los_Angeles` | US West |
| `Asia/Tokyo` | Japan |
| `UTC` | Universal |

**Common locale values:**

| Locale | Language |
|--------|----------|
| `en_US.UTF-8` | English (US) |
| `en_GB.UTF-8` | English (UK) |
| `fr_BE.UTF-8` | Français (Belgique) |
| `fr_FR.UTF-8` | Français (France) |
| `de_DE.UTF-8` | Deutsch |
| `nl_BE.UTF-8` | Nederlands (België) |
| `nl_NL.UTF-8` | Nederlands |
| `es_ES.UTF-8` | Español |
| `pt_BR.UTF-8` | Português (Brasil) |
| `it_IT.UTF-8` | Italiano |
| `ru_RU.UTF-8` | Русский |
| `ja_JP.UTF-8` | 日本語 |
| `zh_CN.UTF-8` | 中文 (简体) |
| `ko_KR.UTF-8` | 한국어 |

**Common console keymap values:**

| Keymap | Layout |
|--------|--------|
| `us` | English (US) QWERTY |
| `us-acentos` | English (US) International |
| `uk` | English (UK) QWERTY |
| `be-latin1` | Belge AZERTY |
| `fr` | Français AZERTY |
| `de` | Allemand QWERTZ |
| `nl` | Néerlandais QWERTY |
| `es` | Espagnol QWERTY |
| `dvorak` | Dvorak (US) |
| `colemak` | Colemak |

> **Note:** `environment.sessionVariables.TZ` must always match `time.timeZone` — they both control the timezone, one at the system level and one at the session level.

Edit `home/local.nix` for personal home-manager overrides (extra packages, dotfiles, aliases, fastfetch...):

```nix
{ pkgs, lib, osConfig, ... }:
{
  # home.packages = with pkgs; [ vlc telegram-desktop ];
}
```

> See `home/local.nix.example` for all available override options including fastfetch customization.

### KDE Plasma overrides (`home/local.nix`)

When using `roudix.desktop.type = "kde"`, you can override any plasma-manager setting in `home/local.nix`:

**Wallpaper**
```nix
programs.plasma.workspace.wallpaper = lib.mkForce "/home/youruser/Pictures/wallpaper.jpg";
```

**Icon theme**
```nix
programs.plasma.workspace.iconTheme = lib.mkForce "Papirus-Dark";
# Other values: "Papirus", "Papirus-Light", "breeze-dark", "breeze"
```

**Color scheme / Look & Feel**
```nix
programs.plasma.workspace.colorScheme = lib.mkForce "BreezeDark";
programs.plasma.workspace.lookAndFeel = lib.mkForce "org.kde.breezedark.desktop";
```

**Taskbar / Panels**
```nix
programs.plasma.panels = lib.mkForce [
  {
    location = "bottom";
    widgets = [
      { kickoff.icon = "/path/to/your/icon.svg"; }
      "org.kde.plasma.icontasks"
      "org.kde.plasma.marginsseperator"
      "org.kde.plasma.systemtray"
      "org.kde.plasma.digitalclock"
      "org.kde.plasma.showdesktop"
    ];
  }
];
```

> `lib.mkForce` is required to override the defaults set in `home/kde.nix`.

> All three `local.nix` files and `boot.local.nix` are listed in `.gitignore` — they will never be overwritten by a `git pull`.

**Available kernel variants:**

| Variant | Description |
|---------|-------------|
| `cachyos-latest` | Standard latest CachyOS kernel |
| `cachyos-latest-v3` | x86_64-v3 optimized (recommended for modern CPUs) |
| `cachyos-latest-lto` | LTO build for better performance |
| `cachyos-latest-lto-v3` | LTO + x86_64-v3 (best performance, modern CPUs only) |
| `cachyos-lts` | Long-term support CachyOS kernel |
| `cachyos-lts-v3` | LTS + x86_64-v3 optimized |
| `cachyos-lts-lto-v3` | LTS + LTO + x86_64-v3 (stable + performance) |
| `cachyos-rc` | Release candidate — bleeding edge, potentially unstable |

> **NVIDIA note:** Only GTX 20xx / RTX series and newer are supported. Open drivers enabled by default for RTX 20xx+ (Turing+). GTX 10xx/16xx are not supported.

> **Spicetify Comfy theme note:** After your first build, copy the color.ini manually:
> ```bash
> cp ~/.config/spicetify/Themes/Comfy/color.ini ~/.config/roudix/modules/home/spicetify/Comfy/color.ini
> ```
> Then run `rebuild` to apply.

### 5. Update the disk mount

In `hosts/roudix/local.nix`, add a `lib.mkForce` block with your own UUID (or skip if no secondary disk):

```bash
lsblk -f  # find your disk UUID
```

```nix
fileSystems."/mnt/gaming" = lib.mkForce {
  device = "/dev/disk/by-uuid/YOUR-UUID-HERE";
  fsType = "btrfs";
  options = [ "defaults" "nofail" ];
};
```

### 6. Configure Limine multi-boot (optional)

> Skip this step if you only have NixOS on your machine.

Limine can boot other operating systems on separate disks. `boot.local.nix` controls the extra entries — it is gitignored and never overwritten by `git pull`.

**Never edit `modules/system/boot.nix` directly** — it gets overwritten on `git pull`.

#### If you used the automated installer

The installer detected your other OSes automatically from the EFI NVRAM (`efibootmgr`) and wrote `boot.local.nix` for you — no manual action needed. You can review the result:

```bash
cat modules/system/boot.local.nix
```

#### If you are installing manually

**Get your PARTUUIDs:**

```bash
lsblk -o NAME,FSTYPE,SIZE,PARTLABEL,PARTUUID
```

Look for partitions with `vfat` filesystem type and `EFI system partition` label — those are your ESPs.

**Edit `modules/system/boot.local.nix`** and add your entries:

```nix
{
  extraEntries = ''
    /+Other systems and bootloaders
    //Windows
      protocol: efi
      path: uuid(YOUR-WINDOWS-ESP-PARTUUID):/EFI/Microsoft/Boot/bootmgfw.efi
    //CachyOS
      protocol: efi
      path: uuid(YOUR-CACHYOS-ESP-PARTUUID):/EFI/limine/BOOTX64.EFI
  '';
}
```

> **Tip:** The EFI path after the UUID depends on the bootloader used by the other OS. Common paths:
> - Windows: `/EFI/Microsoft/Boot/bootmgfw.efi`
> - CachyOS (Limine): `/EFI/limine/BOOTX64.EFI`
> - Arch/Manjaro (GRUB): `/EFI/grub/grubx64.efi`
> - Any distro (fallback): `/EFI/BOOT/BOOTX64.EFI`

If you have no other OS to add, just leave `extraEntries` empty:

```nix
{
  extraEntries = "";
}
```

> `boot.local.nix` is listed in `.gitignore` — it will never be overwritten by a `git pull`.

### 7. Update git config

In `modules/home/git.nix`:

```nix
settings = {
  user.name = "yourname";
  user.email = "your@email.com";
};
```

### 8. Enable/disable optional modules

In `hosts/roudix/local.nix`:

```nix
roudix.gaming.enable         = true;
roudix.flatpak.enable        = true;   # Flatpak + daily auto-update
roudix.fstrim.enable         = true;   # recommended for SSD/NVMe
roudix.virtualization.enable = false;  # enable for QEMU/KVM
roudix.vmGuest.enable        = true;   # enable only inside a VM
roudix.hosts.gtaFix.enable   = true;   # block BattlEye telemetry (GTA fix)
roudix.autoupdate.enable     = true;   # auto pull + nh os boot on changes
roudix.zen.enable            = false;  # install Zen Browser (disabled by default)
```

> **Reminder:** If you set `roudix.autoupdate.enable = true`, also configure the interval:
> ```nix
> roudix.autoupdate.interval = "1h"; # 1h, 6h, 12h, 24h...
> ```

### 9. Customize fastfetch (optional)

By default Roudix shows its ASCII logo in fastfetch. You can override it in `home/local.nix` without touching git:

```nix
# Use a custom image (requires kitty terminal)
programs.fastfetch.settings.logo = {
  type = "kitty-direct";
  source = "/home/youruser/Pictures/my-logo.png";
  padding = { top = 1; left = 3; };
  width = 38;
};

# Use a custom ASCII file
programs.fastfetch.settings.logo = {
  type = "file";
  source = "/home/youruser/.config/fastfetch/my-logo.txt";
  padding = { top = 1; left = 3; };
  width = 38;
};

# Override the entire fastfetch config (replaces everything)
programs.fastfetch.settings = lib.mkForce {
  "$schema" = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json";
  logo = { ... };
  display = { separator = "  "; color = "33"; };
  modules = [ ... ];
};
```

> `lib.mkForce` overwrites the entire Roudix default config. Without it, your keys are merged with the defaults.
> See `home/local.nix.example` for more examples.

### 10. Build

> **If flakes and nix-command are not enabled yet** (fresh NixOS install):

```bash
nix --extra-experimental-features 'nix-command flakes' shell nixpkgs#git -c sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

> **Otherwise:**

```bash
sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

Once built, use the fish aliases for all future operations.

---

## Auto-update

When `roudix.autoupdate.enable = true`, the system checks GitHub every hour (and 5 min after boot).
If new commits are detected on `main`, it pulls and runs `nh os boot path:...` — the new config applies on next reboot.
Your `local.nix` files, `username.nix`, `hardware-configuration.nix` and everything under `dotfiles/perso/` are gitignored and never touched by the pull.

To configure the interval or branch, override in `local.nix`:

```nix
{ ... }:
{
  roudix.autoupdate.enable   = true;
  roudix.autoupdate.interval = "6h";   # check every 6 hours instead of 1h
  roudix.autoupdate.branch   = "main"; # branch to track
}
```

Check the last run:

```bash
systemctl status roudix-autoupdate
journalctl -u roudix-autoupdate -n 20
```

---

## Aliases

| Alias | Action |
|-------|--------|
| `rebuild` | Apply configuration immediately |
| `update` | Update flake inputs + apply |
| `cleanup` | Remove old generations + garbage collect |
| `noctalia-reload` | Restart Quickshell without logging out |
| `roudix-switch <de>` | Switch desktop environment (applies on next reboot) |

---

## Updating

```bash
update
```
