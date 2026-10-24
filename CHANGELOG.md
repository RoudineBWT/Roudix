# Changelog

All notable changes to Roudix are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); entries are grouped by
**Added / Changed / Fixed / Removed**. Changes land on `dev`, move to `testing`
once they build, then to `main` — so an entry shows up here when it reaches `main`.

## [Unreleased]

### Added
- `Papirus-Roudix` and `Tela-Roudix` icon themes (`modules/system/desktop/icon-theme.nix`): only the "places" icons (folders, home...) recolored with the Roudix primary, everything else inherited from the stock Papirus-Dark / Tela-dark. Built by Nix from `assets/palette/Roudix.json`, and the new default (`roudix.iconTheme = "papirus"` / `"tela"`) on GNOME, KDE, Cinnamon and COSMIC, as a default the user can still change in the desktop's own settings (KDE users still on the stock Papirus-Dark are moved once). The bare compositors are unchanged.
- COSMIC as a desktop choice (`roudix.desktop.type = "cosmic"`, also in `roudix-switch`, `roudix-switcher` and both installers): cosmic-comp + cosmic-greeter, Roudix Kitsune wallpaper, keyboard layout from `roudix.keyboard*`, dock pinned like GNOME / KDE (browser(s), COSMIC Files, terminal, Roudix Store, Settings) and a **Roudix** folder in the app library for the Roudix apps (`X-Roudix`). All of it is a cosmic-config default (never overrides what the user changed). COSMIC's native theme is the Roudix colour scheme by default (`assets/cosmic/`, generated from `Roudix.json` by `scripts/gen-cosmic-theme`, shipped as system defaults, no Home Manager); the greeter follows the user's wallpaper (Kitsune by default). "Apply current theme to GNOME apps" is on by default (`com.system76.CosmicTk`), so GTK apps get the Roudix colours from COSMIC's own export, with no `gtk.extraCss`. `system76-scheduler` is off by default (SCX).
- `roudix-installer` (Python / GTK) can now convert an already installed NixOS: no
  disk page, config cloned to `~/.config/roudix`, applied with `nixos-rebuild boot`
  (the previous generation stays in the boot menu), privileged steps through
  polkit. `/etc/nixos` is copied to `/var/backups/roudix/nixos-<date>/` with a
  `RESTORE.txt`, `hardware-configuration.nix` is reused instead of regenerated over
  `/etc/nixos`, and a pre-flight warns about a small `/boot`, a bootloader change
  or an older `stateVersion`. `roudix-installer.sh` stays as the TTY fallback.
- *Simulate* button on the installer's summary page (the dry run, no longer an
  environment variable): generates the config in a temp dir, verifies every written
  option (as `roudix-installer.sh` did, the Python installer did not) and, on an
  installed NixOS, makes Nix evaluate the whole system.
- Releases: `scripts/release.sh` promotes `[Unreleased]` to a dated release
  (`v<YYYY.MM.DD>`) when `sync-main.yml` merges testing into main, then tags it and
  publishes a GitHub Release with those notes (feat/fix commit subjects as fallback
  if `[Unreleased]` is empty).
- `roudix-autoupdate` remembers the feat/fix commits each update brings: the
  "Rebuild scheduled" notification lists the first ones and `update --changes`
  shows them all, after the package diff.
- `roudix-switcher` now exposes options it was missing: password manager (`roudix.passwordManager`), Signal / ZapZap / Fluxer, the Umbriel effects (`roudix.umbriel.effects`), the Zen tweaks (`roudix.zen.tweaks.*`), the Gaming Mode HDR switch (`roudix.gaming.gamescopeSession.hdr.enable`) and the auto-update check interval (`roudix.autoupdate.interval`).
- Zen tweaks can target a chosen existing profile (`roudix.zen.tweaks.profile`, ~/.zen or ~/.config/zen) and Firefox gets the same tweaks as a user.js in a chosen profile (`roudix.firefox.tweaks.*`, ~/.mozilla/firefox or ~/.config/mozilla/firefox); `roudix-switcher` lists the profiles found. Umbriel effects are shown without icons.
- `roudix-hw-sync` (app and terminal) is translated like the other Roudix apps, via gettext
  (`po/<lang>.po`, compiled to `share/locale` by the package): French, Spanish, Brazilian
  Portuguese, Russian, Simplified Chinese, Hindi and Arabic, with the `.desktop` comment. The CLI's
  messages are translated too; the `--detect` key=value output stays untouched.
- `roudix-kernel-switcher` is translated the same way (same seven languages, `.desktop` comment
  included): kernel descriptions, group headings and every message of the app. Kernel names
  (`cachyos-lto-v3`, …) and the log file stay in English.

### Changed
- Roudix identity moved from Catppuccin Mocha Peach to the Roudix palette: logo
  (SVG + PNG), all app icons (switcher, store, config, hw-sync, kernel/scheduler
  switchers, installer), wallpapers SVG, installer CSS, ISO GRUB theme, fastfetch,
  `roudix-kitsune.png` (hue-remapped), the `*-mocha` / `sakura-roudix` Umbriel
  presets (names kept, colours now Roudix), Hyprland `colors.lua` and GTK (adw-gtk3) accent/surfaces now follow
  `assets/palette/Roudix.json`.
- README preview is now a slideshow (animated WebP: Umbriel, GNOME, KDE Plasma)
  built by `scripts/gen-preview-slideshow.py`; `assets/screenshot/preview.png` is
  now the Umbriel screenshot. The READMEs also state that compositor customization
  is left to the user (Roudix only ships the default Noctalia / DMS / Caelestia configs).

### Added
- GNOME Shell themes `Roudix-Dark` / `Roudix-Light`, generated from
  `assets/palette/Roudix.json` by `scripts/gen-gnome-shell-theme.py` (gnome-shell's
  own stylesheet recoloured, so layout tracks upstream) and shipped by
  `roudix-branding` (`share/themes/`). `Roudix-Dark` is the default shell theme on
  GNOME through the User Themes extension (now enabled by default); the shell keeps
  the Roudix orange whatever accent colour is picked in Settings.
- KDE Plasma colour schemes `RoudixDark` / `RoudixLight`, generated from
  `assets/palette/Roudix.json` by `scripts/gen-kde-colorscheme.py` and shipped by
  `roudix-branding` (`share/color-schemes/`). `RoudixDark` is now the default
  colour scheme on KDE (first login, and once for existing users still on the stock
  BreezeDark); `RoudixLight` is selectable in System Settings.
- Terminal colour schemes from the same palette: Konsole (`RoudixDark` /
  `RoudixLight` + default `Roudix` profile, always on KDE or when
  `roudix.terminal = "konsole"`), Ptyxis (`Roudix` palette, light + dark), and
  ghostty / kitty / alacritty / foot / wezterm through
  `modules/home/theming/terminal-theme.nix`. Theme files are managed by
  Roudix; the terminal's own config file is only created if absent, so existing
  configs are never overwritten.
- Definitive colour palette `assets/palette/Roudix.json` (dark + light), exposed to
  every Home Manager module through `modules/home/theming/palette.nix`
  (`config.roudix.palette.{dark,light,active,lib}` / `roudixPalette`), also
  installed as `~/.config/roudix/palette.json` and as a Noctalia colour scheme
  (`~/.config/noctalia/colorschemes/Roudix/Roudix.json`).
- `Justfile` (`just check`, `just ci`, …) and `scripts/ci-stubs.sh` to evaluate
  every host locally the same way CI does.
- `check-eval.yml`: every push / PR now evaluates all hosts and runs `ruff`
  (errors only), before the full build gate of the sync workflows.
- Issue templates (bug report, feature request).
