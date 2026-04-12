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

## Niri & Hyprland only

| Alias | Action |
|-------|--------|
| `roudix-shell-switch <shell>` | Switch graphical shell (applies on next reboot) |

### Usage

```fish
# Switch desktop environment
roudix-switch niri
roudix-switch hyprland
roudix-switch gnome
roudix-switch kde

# Switch graphical shell (Niri & Hyprland only)
roudix-shell-switch noctalia
roudix-shell-switch dms
roudix-shell-switch caelista # only for hyprland
```

Both `roudix-switch` and `roudix-shell-switch` edit `hosts/roudix/local.nix` automatically and run `nh os boot` — no manual rebuild needed. Changes apply on next reboot.
