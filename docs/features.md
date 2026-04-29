# Features

## Kernel & Performance

- CachyOS kernel with NTSync enabled (`ntsync` module)
- 36 kernel variants available (set in `hosts/roudix/local.nix`)
- ZRAM enabled (100% RAM, zstd, swappiness 150)
- zswap disabled
- CPU microcode auto-configured (Intel or AMD)
- Intel: `split_lock_detect=off` applied automatically
- ananicy-cpp enabled (process priority daemon, CachyOS rules)
- SCX scheduler support — live switching, no reboot required (bpfland, lavd, flash, p2dq, rusty…) via the Kernel Switcher GUI — a single password prompt via `scx-switch` handles ananicy-cpp stop/start and scheduler switching in one shot — **note:** SCX is not persistent across reboots; after a reboot ananicy-cpp restarts automatically and the scheduler must be re-applied via the Kernel Switcher GUI

## Boot

- Limine bootloader — modern, fast, multi-disk support
- Automatic UEFI entry rename to "Roudix"
- Multi-OS boot menu (Windows, other Linux distros on separate ESPs)
- Boot label shows Roudix name + NixOS release version

## Gaming

- Steam + Proton-GE + Gamescope session
- Millennium Steam client patcher
- OBS capture env vars pre-configured (`OBS_VKCAPTURE`, `TZ`)
- Custom horizontal MangoHud overlay
- Controller support (Steam Hardware + game-devices-udev-rules)
- 32-bit support for Wine/Steam
- `game-performance` wrapper — switches CPU governor to performance for the duration of a game (usage: `game-performance %command%` in Steam launch options)
- `protonup-qt` on KDE, `protonplus` on other DEs
- Heroic (via roudix-caches), Lutris + Faugus Launcher (via glf-os)

## Desktop (Niri)

- Niri scrollable tiling Wayland compositor
- Noctalia modern shell
- xdg-desktop-portal-gnome + gtk (screencast + remote desktop portals configured)
- Capitaine Cursors White
- adw-gtk3 + Papirus icons + Papirus Folders
- Discord with Vencord
- Element Desktop with gnome-libsecret / kwallet6 (auto-detected per DE)
- GNOME Polkit agent
- GDM display manager

## Desktop (MangoWC)

- MangoWC Wayland compositor
- Noctalia / DankMaterialShell
- xdg-desktop-portal-gtk
- Capitaine Cursors White (24 px)
- GNOME Polkit agent
- Ly display manager (Noctalia & DMS)
- adw-gtk3 + Papirus icons + Papirus Folders
- Zoom open animation + official bezier curves
- VRR + tearing enabled on gaming monitor (DP-1 1440p@240)
- Screenshots with grim + slurp + satty (annotation) — 3 keybinds
- rofi window switcher (Alt+Tab)
- XDG Desktop Portal env vars pre-configured (Pipewire screen capture, OBS, Discord Go Live)
- force_tearing + indleinhibit_when_focus on all gaming apps (Steam, Heroic, Minecraft, Lutris, Bottles)
- Unfocused window opacity (0.85)
- Hotarea overview (corner mouse gesture)
- Floating snap + drag tile-to-tile

## Desktop (Hyprland)

- Hyprland dynamic tiling Wayland compositor launched via UWSM
- Noctalia modern shell
- xdg-desktop-portal-hyprland + gtk portal
- Capitaine Cursors White
- GNOME Polkit agent (started via systemd user service)
- swww wallpaper daemon
- Screenshots with grim + slurp + satty (annotation) — 3 keybinds

## Desktop (GNOME)

- GNOME 49.5 (follows nixos-unstable branch)
- Curated extension set (blur, tiling, vitals, arcmenu...) — enabled via dconf
- ArcMenu with Roudix logo as menu button icon
- Bloat removed via `environment.gnome.excludePackages`
- Papirus-Dark icon theme
- adw-gtk3-dark GTK theme (dark mode by default)
- Capitaine Cursors White
- Roudix wallpaper (light/dark based on system theme)
- `color-scheme = prefer-dark` applied via dconf
- Extension settings (ArcMenu, Dash to Dock, Dash to Panel, Blur My Shell...) pre-configured via `gnome-extensions.nix`
- Add/remove extensions without editing core files via `roudix.gnome.extraExtensions` / `roudix.gnome.disabledExtensions`
- Override wallpaper, theme, icons, cursor in `home/local.nix`

## Desktop (KDE)

- KDE Plasma 6 with plasma-login-manager (Plasma 6.6+, nixpkgs unstable)
- KDE Connect enabled
- xdg-desktop-portal-kde
- Papirus-Dark icon theme
- Breeze Dark look & feel + color scheme
- Roudix Dark wallpaper on login screen and desktop
- Curated packages: partitionmanager, kcalc, digikam, vlc...
- Bloat removed (Discover excluded)
- Override wallpaper, panels, icon theme in `home/local.nix`

## Music

- Spotify patched with Spicetify
- Comfy theme (local, customized)
- Adblock + hide podcasts extensions

## Browser

- Configurable browser list via `roudix.browsers` option
- Supports `brave`, `helium` (via helium-nix flake), `vivaldi` (with ffmpeg codecs), `firefox`, `librewolf`, `chromium`, or `[]` for none
- Zen Browser available separately via `roudix.zen.enable = true` (disabled by default)

## Other

- OBS Studio with pipewire + vkcapture plugins
- GPU Screen Recorder
- RGB controller selectable via `roudix.rgb` — `openlinkhub` (Corsair iCUE Link / Commander, auto-updated via CI), `openrgb` (multi-brand: Razer, ASUS, MSI…), or `none`
- OpenLinkHub web UI available at [http://127.0.0.1:27003](http://127.0.0.1:27003) once the service is running
- DDR4/DDR5 RAM RGB control via OpenLinkHub — enable with `roudix.memory.enable = true`, configure `roudix.memory.type`, `roudix.memory.smBus`, and `roudix.memory.sku` (see `installation.md`)
- PipeWire with rnnoise stereo noise suppression (nofail, LADSPA_PATH compat 25.11/26.05)
- Flatpak with Flathub remote + daily auto-update (via nix-flatpak)
- Blueman Bluetooth manager
- QEMU/KVM + Virt-Manager (optional)
- VM guest optimizations module (clipboard sharing, auto-resize, QEMU agent, Spice)
