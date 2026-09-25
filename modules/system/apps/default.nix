{ ... }:
{
  # App-selection modules: each exposes one or more roudix.* options
  # (e.g. roudix.discord, roudix.musicPlayer) letting the user pick between
  # alternatives, or a plain enable toggle for a category of apps.
  # Grouped by category; appimage/flatpak live in ../packaging (they're
  # app formats/runtimes, not apps themselves).
  imports = [
    ./apps.nix
    ./browser
    ./communication
    ./media
    ./creation
    ./utilities
  ];
}
