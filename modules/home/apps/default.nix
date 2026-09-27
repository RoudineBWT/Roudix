{ ... }:
{
  # Home-manager side of each app-selection option. Mirrors
  # modules/system/apps/ (same category folders), which only declares the
  # roudix.* options (e.g. roudix.discord, roudix.musicPlayer) — these
  # implement the actual home.packages/programs.* for whichever choice
  # osConfig.roudix.* holds.
  imports = [
    ./common-apps.nix
    ./browser
    ./communication
    ./media
    ./creation
    ./utilities
  ];
}
