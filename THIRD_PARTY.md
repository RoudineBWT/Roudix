# Licensing

Roudix is one repository with several licenses. The rule of thumb: **the root
[`LICENSE`](LICENSE) (MIT) covers Roudix's own code and configuration, unless a
directory or file says otherwise.**

| What | License | Where |
|------|---------|-------|
| Roudix's own code and configuration (Nix modules, hosts, dotfiles, scripts, installer, GUI tools other than the store) | MIT | [`LICENSE`](LICENSE) |
| **Roudix Store** | **GPL-2.0-only** | [`pkgs/roudix-store/COPYING`](pkgs/roudix-store/COPYING) |
| Third-party components | their own, see below | |

## Roudix Store (GPL-2.0-only)

The store's UI and AppStream catalog code are derived from Nobara's
[dnf-app-center](https://github.com/Nobara-Project/dnf-app-center) (GPL-2.0), so
it stays under the GPL-2.0 and cannot be relicensed. It is a separate program:
the MIT-licensed parts of this repository only install and configure it (the
`roudix.store.*` options), they do not include its code.

## Third-party components

These keep their own licenses and are **not** relicensed by this repository.

| Component | Path | License |
|-----------|------|---------|
| `sakura-overdrive` shaders, adapted from *flowering-vine* by Barrulus | `modules/home/desktop/umbriel/_effects/sakura-overdrive/` | MIT, © 2026 Barrulus — see `LICENSE-Barrulus-MIT.txt` in that directory |
| Spicetify "Colorful" theme | `modules/home/apps/media/spicetify/Colorful/` | MIT, © 2024 Sanooj Es — see `LICENSE` in that directory |
| EasyEffects impulse responses (`.irs`) | `dotfiles/easyeffects/irs/` | Third-party files that keep their original authors' terms; not covered by the MIT license above |

Packages and flake inputs that Roudix pulls in at build time (nixpkgs, Hyprland,
Niri, Noctalia, …) are not part of this repository and remain under their own
licenses.
