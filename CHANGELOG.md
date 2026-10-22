# Changelog

All notable changes to Roudix are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); entries are grouped by
**Added / Changed / Fixed / Removed**. Changes land on `dev`, move to `testing`
once they build, then to `main` — so an entry shows up here when it reaches `main`.

## [Unreleased]

### Changed
- Roudix identity moved from Catppuccin Mocha Peach to the Roudix palette: logo
  (SVG + PNG), all app icons (switcher, store, config, hw-sync, kernel/scheduler
  switchers, installer), wallpapers SVG, installer CSS, ISO GRUB theme, fastfetch,
  `roudix-kitsune.png` (hue-remapped), the `*-mocha` / `sakura-roudix` Umbriel
  presets (names kept, colours now Roudix), Hyprland `colors.lua` and GTK (adw-gtk3) accent/surfaces now follow
  `assets/palette/Roudix.json`.

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
