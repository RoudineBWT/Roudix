{ lib, ... }:
{
  # ── Music player: pick one, or none ─────────────────────────────────────
  # Read on the home-manager side (modules/home/common.nix) via osConfig —
  # same pattern as roudix.videoPlayer / roudix.torrentClient.
  #
  # Used to be two independent roudix.apps.{spotify,ytmdesktop}.enable
  # booleans (both true by default, so both got installed at once) —
  # promoted to a single enum so it's an actual choice, same as
  # videoPlayer/torrentClient.
  options.roudix.musicPlayer = lib.mkOption {
    type    = lib.types.enum [ "none" "spotify" "ytmdesktop" ];
    default = "spotify";
    description = ''
      "none"       : No music player installed.
      "spotify"    : Spotify, themed with Spicetify, Roudix default (see
                     roudix.spicetify.* for the theme/extensions).
      "ytmdesktop" : YouTube Music Desktop App — unofficial Electron-based
                     YouTube Music client.
    '';
  };
}
