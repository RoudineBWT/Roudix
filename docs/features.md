# Features

*[Version française](features.fr.md)*

## Kernel & Performance

- CachyOS kernel with NTSync enabled (`ntsync` module)
- Two kernel providers, selected automatically by `hardware.myGpu`:
  - AMD/Intel → [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel), 32 variants (`hardware.myKernel`)
  - Nvidia → Chaotic-Nyx, 4 variants (`hardware.myKernelChaotic`) — ships `nvidia_cachyos`, a precompiled driver matched to their kernel, so no local Nvidia module rebuild on kernel bumps
- Plain nixpkgs kernels also selectable on both providers, outside the CachyOS overlay entirely — `zen` (`linuxPackages_zen`), `nixpkgs-lts`, `nixpkgs-latest`, `nixpkgs-testing` (RC/mainline). On Nvidia these fall back to a locally-rebuilt Nvidia module (no `nvidia_cachyos` cache)
- ZRAM enabled (100% RAM, zstd, swappiness 150)
- zswap disabled
- CPU microcode auto-configured (Intel or AMD)
- Intel: `split_lock_detect=off` applied automatically
- ananicy-cpp enabled (process priority daemon, CachyOS rules)
- SCX scheduler support — live switching, no reboot required (bpfland, lavd, flash, p2dq, rusty…) via the Kernel Switcher GUI — a single password prompt via `scx-switch` handles ananicy-cpp stop/start and scheduler switching in one shot — **note:** SCX is not persistent across reboots; after a reboot ananicy-cpp restarts automatically and the scheduler must be re-applied via the Kernel Switcher GUI

## Boot

- Limine bootloader (default) — modern, fast, multi-disk support — or systemd-boot, selectable via `roudix.boot.bootloader`
- Automatic UEFI entry rename to "Roudix"
- Multi-OS boot menu (Windows, other Linux distros on separate ESPs)
- Boot label shows Roudix name + NixOS release version

## Gaming

- Steam + Proton-GE + Proton-CachyOS (x86_64-v3) + Gamescope (gamescope-wsi, session disabled by default)
- OBS capture env vars pre-configured (`OBS_VKCAPTURE` via `environment.sessionVariables`)
- Custom horizontal MangoHud overlay (`Powered By Roudix` label)
- Controller support (Steam Hardware + game-devices-udev-rules)
- 32-bit support for Wine/Steam
- `game-performance` wrapper — switches to a dedicated `tuned-adm` performance profile for the duration of a game, tracked via a `systemd-run --user --scope` cgroup (so it survives Steam re-forking/detaching) and restored on exit (usage: `game-performance %command%` in Steam launch options) — GameMode is disabled on purpose (incompatible with ananicy-cpp here)
- `ffmpegthumbnailer` available system-wide (video thumbnails in file managers)
- `protonup-qt` on KDE, `protonplus` on other DEs
- Heroic, Lutris, Faugus Launcher, Prism Launcher (Minecraft, or Modrinth App as an alternative — `roudix.gaming.apps.modrinth.enable`) and Vintage Story (via roudix-caches)
- Each gaming app individually toggleable via `roudix.gaming.apps.<lutris|heroic|faugus|prismlauncher|vintagestory|mangohud>.enable` (all `true` by default)

## Desktop (Niri)

- Niri scrollable tiling Wayland compositor — provided via [niri-flake](https://github.com/epireyn/niri-flake) (epireyn), using `niri-unstable` by default, with the `niri.cachix.org` binary cache pre-configured
- Config is Nix-native (`programs.niri.settings`), split by topic (general, animations, input, layout, outputs, binds, rules) and validated at build time via `niri validate` — a broken config fails the build instead of the compositor at login
- Noctalia/DMS live theme sync (matugen/DMS-generated colors, alt-tab, blur) is preserved by appending an `include` to the generated config rather than baking it in statically
- Noctalia (v5) modern shell
- xdg-desktop-portal-gnome + gtk (screencast + remote desktop portals configured)
- Bibata Modern Ice cursor (24 px)
- adw-gtk3 + Papirus icons + Papirus Folders
- Element Desktop with gnome-libsecret / kwallet6 (auto-detected per DE)
- GNOME Polkit agent
- DMS Greeter (greetd)

## Desktop (MangoWC)

- MangoWC Wayland compositor
- Noctalia / DankMaterialShell
- xdg-desktop-portal-gtk
- Bibata Modern Ice cursor (24 px)
- GNOME Polkit agent
- Ly display manager
- adw-gtk3 + Papirus icons + Papirus Folders
- Zoom open animation + official bezier curves
- VRR + tearing enabled on gaming monitor (DP-1 1440p@240)
- Screenshots with grim + slurp + satty (annotation) — 3 keybinds
- rofi window switcher (Alt+Tab)
- XDG Desktop Portal env vars pre-configured (Pipewire screen capture, OBS, Discord Go Live)
- force_tearing + idleinhibit_when_focus on all gaming apps (Steam, Heroic, Minecraft, Lutris, Bottles)
- Unfocused window opacity (0.85)
- Hotarea overview (corner mouse gesture)
- Floating snap + drag tile-to-tile

## Desktop (Umbriel)

- Umbriel scrollable tiling Wayland compositor — Noctalia's own native compositor, provided via [noctalia-dev/umbriel](https://github.com/noctalia-dev/umbriel) (Noctalia-only, no shell switching)
- Config is Nix-native (`programs.umbriel.settings`), split by topic (general, appearance, animation, input, layout, outputs, binds, rules) and validated at build time (`validateConfig = true`)
- Noctalia's live theme sync (matugen-generated colors) preserved via Umbriel's native `include.files` mechanism, no static color snapshot
- Bibata Modern Ice cursor (24 px)
- adw-gtk3 + Papirus icons + Papirus Folders
- Hot corners (overview on mouse-to-corner) and a workspace overview (Mod+O)
- Scratchpad support (move/toggle/restore a floating window on demand)
- Per-workspace layout overrides (e.g. no gap on the gaming workspace)

## Desktop (Hyprland)

- Hyprland dynamic tiling Wayland compositor launched via UWSM
- Noctalia modern shell
- xdg-desktop-portal-hyprland + gtk portal
- Bibata Modern Ice cursor (24 px)
- GNOME Polkit agent (started via systemd user service)
- swww wallpaper daemon
- Screenshots with grim + slurp + satty (annotation) — 3 keybinds

## Desktop (GNOME)

- GNOME 50.x (follows nixos-unstable branch)
- Curated extension set (blur, tiling, vitals, arcmenu...) — enabled via dconf
- ArcMenu with Roudix logo as menu button icon
- Bloat removed via `environment.gnome.excludePackages`
- Papirus-Dark icon theme
- adw-gtk3-dark GTK theme (dark mode by default)
- Bibata Modern Ice cursor (24 px)
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

- Spotify patched with Spicetify (toggle via `roudix.apps.spotify.enable`)
- Local theme, "colorful" by default (or "comfy") — see toggles below
- Adblock + hide podcasts extensions

## Optional common apps

GIMP, Inkscape, SongRec and EasyEffects (+ rnnoise-plugin) ship by default but
can each be turned off individually via `roudix.apps.<name>.enable` (`gimp`,
`inkscape`, `songrec`, `easyeffects`) — same as `roudix.apps.spotify.enable`
above.

Also available, opt-in (off by default): a torrent client via
`roudix.torrentClient` — `"qbittorrent"` (feature-rich, Qt-based),
`"fragments"` (minimal GNOME/libadwaita client), `"deluge"` (plugin-based) or
`"none"` (default).

## Spicetify

- Theme: `roudix.spicetify.theme` — `"colorful"` (default, sanoojes/spicetify-colorful) or `"comfy"` (bundled Comfy theme)
- Color scheme: `roudix.spicetify.colorScheme` — `null` (default) uses the theme's own default ("noctalia" for colorful, "Comfy" for comfy)
- Extensions toggleable individually: `roudix.spicetify.extensions.adblock.enable`, `roudix.spicetify.extensions.hidePodcasts.enable` (both default `true`)
- Marketplace custom app: `roudix.spicetify.marketplace.enable` (default `true`)

## Browser

- Configurable browser list via `roudix.browsers` option
- Supports `brave`, `helium` (via helium-nix flake), `vivaldi` (with ffmpeg codecs), `firefox`, `librewolf`, `chromium`, or `[]` for none
- Zen Browser available separately via `roudix.zen.enable = true` (disabled by default); channel selectable via `roudix.zen.variant` — `"twilight"` (default) or `"beta"`

## Other

- Discord selectable via `roudix.discord` — `"vencord"` (patched client, default), `"vanilla"` (unpatched) or `"none"` (not installed)
- Telegram selectable via `roudix.telegram` — `"telegram"` (official Telegram Desktop), `"ayugram"` (unofficial fork: ghost mode, anti-recall, local message history...) or `"none"` (default, not installed)
- Code editor selectable via `roudix.editor` — `"zed"` (default), `"vscode"`, `"neovim"` or `"none"` (manage your own, e.g. AppImage/Flatpak)
- Graphical (Wayland) keyboard layout via `roudix.keyboardLayout` / `roudix.keyboardVariant` (XKB, e.g. `"be"` / `"intl"`) — independent from `console.keyMap`, which only covers the TTY before the graphical session starts; has no effect on GNOME/KDE, which manage their own layout
- Keyring + xdg-desktop-portal stack for "bare" compositors (Niri, Hyprland, MangoWC, Umbriel) selectable via `roudix.desktopIntegration` — `"gnome"` (gnome-keyring + xdg-desktop-portal-gtk/-gnome, default) or `"kde"` (KWallet + xdg-desktop-portal-kde); no effect on GNOME/KDE sessions, which keep their native stack
- `nix-ld` enabled system-wide — run unpatched dynamic binaries without a FHS environment (pre-configured with common libraries: glibc, openssl, zlib, libGL, X11, libxkbcommon, dbus, glib and more)
- OBS Studio, individually toggleable via `roudix.contentCreation.obs.enable` (default `true`), plugins toggled one by one via `roudix.contentCreation.obs.plugins.<name>.enable` (`vkcapture` + `pipewireAudioCapture` on by default; also available: `backgroundRemoval`, `moveTransition`, `aitumMultistream`, `gstreamer`, `compositeBlur`, `advancedSceneSwitcher`, `inputOverlay`, `waveform`)
- Video editor selectable via `roudix.contentCreation.videoEditor` — `"kdenlive"` (default), `"davinci-resolve"` (free), `"davinci-resolve-studio"` (paid, needs a license), `"shotcut"` or `"none"`; DaVinci Resolve gets an AMD OpenCL ICD automatically when `hardware.myGpu = "amd"`
- `v4l2loopback` virtual camera set up automatically for OBS/DaVinci (`roudix.contentCreation.virtualCamera.enable`, default `true`)
- Chatterino2 Twitch chat client, opt-in via `roudix.contentCreation.streaming.chatterino.enable`
- Whole content-creation group toggleable via `roudix.contentCreation.enable`
- GPU Screen Recorder
- Mesa Git option for AMD — enable experimental/bleeding-edge Mesa via `roudix.mesa.useGit = true` in `local.nix` (default: stable nixpkgs Mesa) — ⚠️ **experimental**, the build may fail depending on nixpkgs state
- AMD GPU stability kernel params applied automatically (`mem_sleep_default=deep`, `amdgpu.gpu_recovery=1`, `amdgpu.lockup_timeout=1000`, `amdgpu.runpm=0`, `amdgpu.sg_display=0`) — fixes random freezes and wake-from-sleep issues on RDNA2/RDNA3
- RGB controller selectable via `roudix.rgb` — `openlinkhub` (Corsair iCUE Link / Commander, auto-updated via CI), `openrgb` (multi-brand: Razer, ASUS, MSI…), or `none`
- OpenLinkHub web UI available at [http://127.0.0.1:27003](http://127.0.0.1:27003) once the service is running
- DDR4/DDR5 RAM RGB control via OpenLinkHub — enable with `roudix.memory.enable = true`, configure `roudix.memory.type`, `roudix.memory.smBus`, and `roudix.memory.sku` (see `installation.md`)
- PipeWire with rnnoise stereo noise suppression (nofail, LADSPA_PATH compat 26.05/26.11)
- Flatpak with Flathub remote + daily auto-update (via nix-flatpak)
- Blueman Bluetooth manager
- Matrix client — configurable via `roudix.matrixClient` (`element`, `cinny`, or `none`) — Element auto-selects kwallet6 on KDE, gnome-libsecret elsewhere
- Video player selectable via `roudix.videoPlayer` — `"vlc"` (widest format support, default), `"clapper"` (modern GTK4 player), `"mpv"` (+ yt-dlp, minimal/streaming), `"celluloid"` (GTK front-end for mpv) or `"none"`; applies on every desktop (used to be Clapper hardcoded on bare compositors only, plus a separate DE-agnostic mpv toggle)
- AppImage support enabled via `appimage.nix`
- Waydroid (Android container) — optional, `roudix.waydroid.enable = true`
- QEMU/KVM + Virt-Manager (optional)
- VM guest optimizations module (clipboard sharing, auto-resize, QEMU agent, Spice)
