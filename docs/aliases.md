*[Version française](aliases.fr.md)*

# Aliases & functions

## Available everywhere

| Alias | Action |
|-------|--------|
| `rebuild` | Apply configuration immediately |
| `update` | Pull the config, rebuild + switch, update Flatpaks (see [below](#update)) |
| `cleanup` | Remove old generations + garbage collect |
| `noctalia-reload` | Restart Noctalia without logging out |
| `dms-reload` | Restart Quickshell without logging out |
| `caelista-reload` | Restart Quickshell without logging out |
| `roudix-switch <de>` | Switch desktop environment (applies on next reboot) |
| `roudix-kernel-switch <kernel>` | Switch kernel variant (applies on next reboot) |

### `update`

Manual counterpart of [auto-update](autoupdate.md): same repository, same tracked branch, same fast-forward-only rule (your local commits are never touched). It runs as your normal user and uses `sudo` only where needed.

1. `git pull --ff-only` of the tracked branch (skipped if you are on another branch, e.g. a feature branch)
2. `nh os switch` (or `nh os boot` with `--boot`)
3. Flatpak update, user and system (never fatal)

The `flake.lock` you get from git is the one CI already built and validated, so a plain `update` does **not** bump flake inputs.

| Option | Effect |
|--------|--------|
| `-i`, `--inputs [name…]` | Also bump flake inputs locally (all of them, or only the named ones). If the build fails, `flake.lock` is restored |
| `-b`, `--boot` | Apply on next boot instead of switching now |
| `-c`, `--check` | Only report whether new commits are available |
| `--no-inputs` | Skip the input bump (useful with `roudix.update.bumpInputs = true`) |
| `--no-pull` / `--no-flatpak` | Skip the pull / the Flatpak update |

```fish
update                    # pull + rebuild + switch
update --inputs           # bump every input, then rebuild
update --inputs nixpkgs   # bump only nixpkgs
```

On a machine that tracks `dev` and always wants fresh inputs, set `roudix.update.bumpInputs = true;` in `local.nix`: a plain `update` then behaves like `update --inputs`.

> After `update --inputs`, `flake.lock` is a local modification: commit and push it (or `git checkout flake.lock`), otherwise the next auto-update pull may refuse to run when CI has touched the lock in the meantime.

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
roudix-switch umbriel
roudix-switch gnome
roudix-switch kde

# Switch kernel variant — list depends on hardware.myGpu, see docs/installation.md
# AMD/Intel (xddxdd):
roudix-kernel-switch cachyos-latest-v3
roudix-kernel-switch cachyos-lts-lto-v3
roudix-kernel-switch cachyos-bore
# Nvidia (Chaotic-Nyx — smaller set, needed for the nvidia_cachyos binary cache):
roudix-kernel-switch cachyos
roudix-kernel-switch cachyos-lts
# Plain nixpkgs kernels — available on both GPU paths, outside the CachyOS overlay
# (on Nvidia these fall back to a locally-rebuilt Nvidia module, no nvidia_cachyos cache):
roudix-kernel-switch zen
roudix-kernel-switch nixpkgs-lts
roudix-kernel-switch nixpkgs-latest
roudix-kernel-switch nixpkgs-testing

# Switch graphical shell (Niri, Hyprland & MangoWC only)
roudix-shell-switch noctalia
roudix-shell-switch dms
roudix-shell-switch caelestia # only for hyprland
```

All three commands edit `hosts/roudix/local.nix` automatically and run `nh os boot` — no manual rebuild needed. Changes apply on next reboot.

> **Note:** `roudix-kernel-switch` writes to `hardware.myKernel` or `hardware.myKernelChaotic` automatically depending on your current `hardware.myGpu` — pass the variant name matching the list for your GPU (see table above).
