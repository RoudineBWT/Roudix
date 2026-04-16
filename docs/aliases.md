# Aliases & functions

## Available everywhere

| Alias | Action |
|-------|--------|
| `rebuild` | Apply configuration immediately |
| `update` | Update flake inputs + apply |
| `cleanup` | Remove old generations + garbage collect |
| `noctalia-reload` | Restart Quickshell without logging out |
| `dms-reload` | Restart Quickshell without logging out |
| `caelista-reload` | Restart Quickshell without logging out |
| `roudix-switch <de>` | Switch desktop environment (applies on next reboot) |
| `roudix-kernel-switch <kernel>` | Switch kernel variant (applies on next reboot) |

## Niri, Hyprland & MangoWC only

| Alias | Action |
|-------|--------|
| `roudix-shell-switch <shell>` | Switch graphical shell (applies on next reboot) |

### Usage

```fish
# Switch desktop environment
roudix-switch niri
roudix-switch hyprland
roudix-switch mangowc
roudix-switch gnome
roudix-switch kde

# Switch kernel variant — see docs/installation.md for the full list
roudix-kernel-switch cachyos-latest-v3
roudix-kernel-switch cachyos-lts-lto-v3
roudix-kernel-switch cachyos-bore

# Switch graphical shell (Niri, Hyprland & MangoWC only)
roudix-shell-switch noctalia
roudix-shell-switch dms
roudix-shell-switch caelestia # only for hyprland
```

All three commands edit `hosts/roudix/local.nix` automatically and run `nh os boot` — no manual rebuild needed. Changes apply on next reboot.
