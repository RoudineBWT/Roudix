{ ... }:
{
  # App-selection modules: each exposes one or more roudix.* options
  # (e.g. roudix.discord, roudix.musicPlayer) letting the user pick between
  # alternatives, or a plain enable toggle for a category of apps.
  imports = [
    ./apps.nix
    ./appimage.nix
    ./flatpak.nix
    ./browser.nix
    ./discord.nix
    ./telegram.nix
    ./matrix.nix
    ./mail-client.nix
    ./music-player.nix
    ./video-player.nix
    ./torrent-client.nix
    ./password-manager.nix
    ./filemanager.nix
    ./editor.nix
    ./terminal.nix
    ./spicetify.nix
    ./content-creation.nix
  ];
}
