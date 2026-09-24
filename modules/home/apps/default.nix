{ ... }:
{
  # Home-manager side of each app-selection option. Mirrors
  # modules/system/apps/, which only declares the roudix.* options
  # (e.g. roudix.discord, roudix.musicPlayer) — these implement the
  # actual home.packages/programs.* for whichever choice osConfig.roudix.*
  # holds.
  imports = [
    ./common-apps.nix
    ./browser.nix
    ./discord.nix
    ./telegram.nix
    ./matrix.nix
    ./mail-client.nix
    ./music-player.nix
    ./video-player.nix
    ./torrent-client.nix
    ./password-manager.nix
    ./editor.nix
    ./terminal.nix
    ./content-creation.nix
  ];
}
