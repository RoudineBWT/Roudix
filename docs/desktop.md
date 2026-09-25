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

To change permanently, edit `hosts/roudix/local.nix`:

```nix
roudix.desktop.type = "niri"; # "niri", "hyprland", "mangowc", "gnome" or "kde"
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

Shell startup is owned by the compositor, so only the selected shell is started:

- **Hyprland:** `noctalia` / `dms run` / `caelestia-shell` from the `hyprland.start` Lua hook.
- **MangoWC:** `noctalia` / `dms run` from MangoWC `autostart_sh`.
- The selected shell's Home Manager systemd autostart is disabled to prevent duplicate instances.

This follows the current Noctalia compositor-autostart guidance and DMS guidance for Hyprland/MangoWC.

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

**Wallpaper** (`home/local.nix`)
```nix
dconf.settings."org/gnome/desktop/background".picture-uri =
  lib.mkForce "file:///home/youruser/Pictures/my-wallpaper.png";
dconf.settings."org/gnome/desktop/background".picture-uri-dark =
  lib.mkForce "file:///home/youruser/Pictures/my-wallpaper-dark.png";
```

**Light/dark mode** (`home/local.nix`)
```nix
dconf.settings."org/gnome/desktop/interface".color-scheme =
  lib.mkForce "prefer-light"; # or "prefer-dark"
```

**Icon theme** (`home/local.nix`)
```nix
dconf.settings."org/gnome/desktop/interface".icon-theme =
  lib.mkForce "Papirus";
# Other values: "Papirus-Dark", "Papirus-Light", "hicolor"
```

**Cursor** (`home/local.nix`)
```nix
dconf.settings."org/gnome/desktop/interface".cursor-theme =
  lib.mkForce "capitaine-cursors";
dconf.settings."org/gnome/desktop/interface".cursor-size =
  lib.mkForce 32;
```

> See `hosts/roudix/local.nix.example` and `home/local.nix.example` for all available GNOME override options.

---

## KDE Plasma overrides

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

> `lib.mkForce` is required to override the defaults set in `home/desktop/kde/default.nix`.
