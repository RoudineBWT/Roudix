*[Version française](desktop.fr.md)*

# Desktop environments

Switch desktop at any time with `roudix-switch <de>` or the **Roudix Customizer** GUI (`roudix-switcher` package) — no separate host needed. The GUI has grown beyond just desktop switching: it now covers Desktop, Gaming (per-app toggles), Editor, Terminal, Browser, Login Shell, File Manager, Chat Client (Discord/Matrix) and Integration (keyring/portal stack) in one app.

| Value | Desktop | Notes |
|-------|---------|-------|
| `niri` | Niri + (Noctalia, DMS) | Default — scrollable tiling Wayland |
| `hyprland` | Hyprland + (Noctalia, DMS, Caelestia) | Dynamic tiling Wayland — launched via UWSM |
| `mangowc` | MangoWC + (Noctalia, DMS) | Wayland compositor |
| `umbriel` | Umbriel + Noctalia | Scrollable tiling — Noctalia's own native compositor, Noctalia-only (no shell switching) |
| `gnome` | GNOME 49.5 | |
| `kde` | KDE Plasma 6 | plasma-login-manager, KDE Connect |
| `cinnamon` | Cinnamon | X11 session + LightDM — classic desktop, suited to older hardware (GNOME 49 is Wayland-only) |

To change permanently, edit `hosts/roudix/local.nix`:

```nix
roudix.desktop.type = "niri"; # "niri", "hyprland", "mangowc", "gnome", "kde" or "cinnamon"
```

Or use the fish function — it edits the config and rebuilds in one step:

```fish
roudix-switch kde
```

> **Note:** `roudix-switch` uses `nh os boot` — changes apply on next reboot.

---

## Graphical shells (Niri, Hyprland & MangoWC only)

For Wayland compositors (Niri, Hyprland, MangoWC), you can switch the shell/bar stack independently from the compositor. For Hyprland, **one configuration tree** (`dotfiles/hyprland/`) contains the common binds and selects the shell from `roudix.desktop.shell`.

| Value | Shell | Hyprland |
|-------|-------|----------|
| `noctalia` | Noctalia | `dotfiles/hyprland/` |
| `dms` | DankMaterialShell | `dotfiles/hyprland/` |
| `caelestia` | Caelestia | `dotfiles/hyprland/` |

**Note:** Caelestia is only available on Hyprland. The shell is injected into the session through `ROUDIX_HYPR_SHELL`, so there are no separate `hyprland-dms/` or `hyprland-caelestia/` trees to keep in sync.

### Shell autostart

Startup depends on the selected shell and compositor, with exactly one startup mechanism per shell:

- **Hyprland + Noctalia:** `noctalia` from the `hyprland.start` Lua hook.
- **Hyprland + Caelestia:** `caelestia-shell` from the `hyprland.start` Lua hook.
- **Hyprland + DMS:** DMS user systemd service; Hyprland exports the session environment to systemd at startup.
- **MangoWC + Noctalia:** `noctalia` from MangoWC `autostart_sh`.
- **MangoWC + DMS:** DMS user systemd service, reached through `mango-session.target`; MangoWC therefore does not execute `dms run`.

DMS must not be started both by systemd and by the compositor: its official documentation recommends removing `dms run` when the systemd service is used. citeturn1search0turn1search2


To change it, edit `hosts/roudix/local.nix`:

```nix
roudix.desktop.shell = "noctalia"; # "noctalia", "dms" or "caelestia"
```

Then rebuild:

```fish
rebuild
```

Or use the fish function (available on Niri, Hyprland & MangoWC only) — it edits the config and rebuilds in one step:

```fish
roudix-shell-switch dms
```

> **Note:** `roudix-shell-switch` uses `nh os boot` — changes apply on next reboot.

---

## nixpkgs or latest version (flake)

Niri, MangoWC and Umbriel always come from their own flake. For the shell (and the greeter that goes with it), Roudix uses the **nixpkgs** version by default. To get the very latest version, built from the project's own flake, turn it on per component in `local.nix` — or from `roudix-switcher` / the installer, where the switch only appears for the shell you selected:

```nix
roudix.desktop.latest.noctalia  = true;  # Noctalia (+ noctalia-greeter)
roudix.desktop.latest.dms       = true;  # DankMaterialShell (+ dms-greeter)
roudix.desktop.latest.caelestia = true;  # Caelestia (the DMS greeter follows it)
```

Hyprland has no flake version in Roudix: it always comes from nixpkgs.

> **Heads up:** Roudix configurations are written for the **flake (latest) versions first**. On the nixpkgs versions, a configuration error saying that an option, a setting or a config key *does not exist* is **normal**: it was added after the version nixpkgs ships. Wait for nixpkgs to catch up, or set the component to `true`.

> If a flake module does not expose a `package` option (possible for DMS, MangoWC and the DMS greeter), the nixpkgs version cannot be applied: Roudix stays on the flake version and prints a warning at build time.

---

## Personal compositor overrides

Niri and Umbriel are configured natively in Nix (`programs.niri.settings` / `programs.umbriel.settings`) — real, typed attrsets, not a generated text file. That means overrides are just Nix: add a key that doesn't exist yet and it merges in automatically; touch a key the repo already sets (same output, same keybind) and you need `lib.mkForce`, or Nix will refuse to build with a "conflicting definitions" error.

MangoWC and Hyprland stay text-based (see below).

You can put overrides directly in `home/local.nix`, but if you're customizing one compositor a lot, a dedicated file keeps things tidier — `home/local.nix` auto-imports `home/niri-custom.nix`, `home/umbriel-custom.nix` and `home/mango-custom.nix` if they exist (copy the matching `*.example` file to get started; they're gitignored like `local.nix`).

**Niri**

```nix
# Change a monitor niri-flake already sets (needs lib.mkForce)
# — run `niri msg outputs` in-session for the real connector name
programs.niri.settings.outputs."Lenovo Group Limited Legion 27Q-10 UNA07260".mode =
  lib.mkForce { width = 3840; height = 2160; refresh = 144.0; };

# Remap a bind the repo already defines (needs lib.mkForce)
programs.niri.settings.binds."Mod+T" = lib.mkForce {
  action.spawn = [ "alacritty" ];
};

# Add a bind that doesn't exist yet (no mkForce needed)
programs.niri.settings.binds."Mod+Shift+V".action.spawn = [ "pavucontrol" ];

# Add a window rule — lists CONCATENATE across files, so this just adds on
# top of the repo's rules, no mkForce needed
programs.niri.settings.window-rules = [
  { matches = [ { app-id = "mpv"; } ]; open-floating = true; }
];
```

**Umbriel**

```nix
# Change an output (needs lib.mkForce — run `umbriel outputs` for the real name)
programs.umbriel.settings.output."DP-1".mode = lib.mkForce "3840x2160@144";

# Remap a bind the repo already defines
programs.umbriel.settings.keybinds."Mod+C" = lib.mkForce "spawn:some-command";

# Add a bind that doesn't exist yet
programs.umbriel.settings.keybinds."Mod+Shift+V" = "spawn:pavucontrol";

# Add a window rule
programs.umbriel.settings.window_rule = [
  { match.app_id = "^mpv$"; default_floating = true; }
];
```

**MangoWC** still sources a personal override file generated by home-manager at the very end of its config — **never touched by `git pull`** — because it has no typed Nix schema in practice:

- MangoWC → `~/.config/mango/user.conf`

```nix
xdg.configFile."mango/user.conf".text = lib.mkForce ''
  monitorrule=name:DP-1,width:2560,height:1440,refresh:144,x:0,y:0,scale:1,vrr:1,rr:0,tearing:1
'';
```

Since it's one big text blob rather than a few Nix lines, it fits better in its own file — see `home/mango-custom.nix.example`.

**Hyprland now uses the modular Lua configuration in `dotfiles/hyprland/`.** The entry point is `dotfiles/hyprland/hyprland.lua`, which loads the `config/` modules for monitors, layouts, animations, binds, window rules and shell integrations. Nix copies this tree as-is to `~/.config/hypr/`.

The current configuration targets Hyprland 0.55+ and uses the native `dwindle`, `master` and `scrolling` layouts. The Nix module generates a small `config/nix-plugins.lua` loader before the entry point; `borders-plus-plus` is included by Roudix. The `dynamic_cursors` block remains optional and only applies when that plugin is present.

### Customizing Hyprland

Machine-specific values (the `DP-1`/`DP-3` outputs, primary monitor, default applications, keyboard, etc.) live under `dotfiles/hyprland/config/`. Edit them directly if you keep your Hyprland setup in the Roudix repository.

For personal overrides without changing tracked files, use `home/local.nix` with `xdg.configFile."hypr/..."` and `lib.mkForce`.

> After changing the Lua configuration, run `rebuild`. A session restart may be required for shell or environment changes.

> See `home/niri-custom.nix.example`, `home/umbriel-custom.nix.example`, `home/mango-custom.nix.example` and `home/local.nix.example` for the full list of examples.

---

## GNOME overrides

When using `roudix.desktop.type = "gnome"`, extension management goes in `hosts/roudix/local.nix` and appearance overrides go in `home/local.nix`.

**Add extensions on top of the defaults** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [
  pop-shell
];
```

**Disable a default extension by UUID** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.disabledExtensions = [
  "arcmenu@arcmenu.com"
];
```

**Combine both — e.g. swap ArcMenu for another launcher** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [ pop-shell ];
roudix.gnome.disabledExtensions = [ "arcmenu@arcmenu.com" ];
```

**Changing the look by hand (recommended)**

Roudix ships GNOME's look (wallpaper, dark theme, icons, cursor, extension settings) as *defaults*. Change anything in Settings, Tweaks or an extension's preferences and it is yours: a rebuild never reverts it. Roudix updates only change the defaults of settings you have not touched.

**Forcing a value from your config** (`home/local.nix`)

If you would rather pin a value declaratively, set it through home-manager. Unlike the manual route above, it is re-applied on **every** rebuild and overrides what you change in the UI:
```nix
dconf.settings."org/gnome/desktop/background".picture-uri =
  "file:///home/youruser/Pictures/my-wallpaper.png";
dconf.settings."org/gnome/desktop/background".picture-uri-dark =
  "file:///home/youruser/Pictures/my-wallpaper-dark.png";
dconf.settings."org/gnome/desktop/interface".color-scheme = "prefer-light"; # or "prefer-dark"
dconf.settings."org/gnome/desktop/interface".icon-theme = "Papirus";
dconf.settings."org/gnome/desktop/interface".cursor-theme = "capitaine-cursors";
dconf.settings."org/gnome/desktop/interface".cursor-size = 32;
```
No `lib.mkForce` needed: home-manager no longer defines these keys.

**Getting the Roudix defaults back** for a setting (or a whole section)
```sh
dconf reset /org/gnome/desktop/interface/icon-theme
dconf reset -f /org/gnome/shell/extensions/dash-to-panel/
```

> See `hosts/roudix/local.nix.example` and `home/local.nix.example` for all available GNOME override options.

---

## KDE Plasma overrides

When using `roudix.desktop.type = "kde"`:

Roudix applies its KDE look **once**, never on every rebuild, so anything you change in System Settings stays:

- **Dark theme, icons, cursor**: applied at first login only, guarded by `~/.local/state/roudix/kde-theme-seeded`. To get the Roudix look back on purpose: `rm ~/.local/state/roudix/kde-theme-seeded` and log out/in.
- **NumLock on startup, lock-screen wallpaper**: plain KConfig defaults in `/etc/xdg`, which sit below your `~/.config` and never override it.
- **Wallpaper and panel**: applied by plasma-manager at first login, then only re-run if Roudix itself changes their definition in an update.

**Pinning values from your config** (`home/local.nix`)

Anything you set through plasma-manager is re-applied on **every** rebuild, so use it only for what you want to be declarative:

**Wallpaper**
```nix
programs.plasma.workspace.wallpaper = lib.mkForce "/home/youruser/Pictures/wallpaper.jpg";
```

**Color scheme / icons / cursor**
```nix
programs.plasma.workspace.colorScheme = "BreezeDark";
programs.plasma.workspace.iconTheme = "Papirus-Dark";
programs.plasma.workspace.cursor.theme = "capitaine-cursors-white";
```

**Taskbar / Panels**
```nix
programs.plasma.panels = lib.mkForce [
  {
    location = "bottom";
    widgets = [
      { kickoff.icon = "/path/to/your/icon.svg"; }
      "org.kde.plasma.icontasks"
      "org.kde.plasma.marginsseparator"
      "org.kde.plasma.systemtray"
      "org.kde.plasma.digitalclock"
      "org.kde.plasma.showdesktop"
    ];
  }
];
```

> `lib.mkForce` is only needed for `wallpaper` and `panels`, which are still defined in `home/desktop/kde/default.nix`.

## Cinnamon defaults

Cinnamon ships the Roudix Kitsune wallpaper by default, on the desktop and on the LightDM login screen, uses the Roudix logo as the menu icon, and pins the default browser (first of `roudix.browsers`), Roudix Store and Settings in the panel. GTK4 / libadwaita apps follow the dark theme. These are defaults: they only apply to what the user has not changed. Panel pins (browser, Nemo, Roudix Store, Settings) and the menu icon are applet defaults, shipped as patched copies of two applets: nothing of Cinnamon is rebuilt.

The login screen (slick-greeter) has no settings app. Change its wallpaper with:

```bash
roudix-lightdm-wallpaper ~/Pictures/wallpaper.jpg   # no rebuild needed
roudix-lightdm-wallpaper --reset                    # back to Kitsune
```

Override the pinned apps in `hosts/roudix/local.nix`:

```nix
roudix.desktop.cinnamon.pinnedApps = [ "firefox.desktop" "io.roudix.store.desktop" "cinnamon-settings.desktop" ];
```
