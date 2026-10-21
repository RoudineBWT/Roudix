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
  Hyprland `colors.lua` and GTK (adw-gtk3) accent/surfaces now follow
  `assets/palette/Roudix.json`.

### Added
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
