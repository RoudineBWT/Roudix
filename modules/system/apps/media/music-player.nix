{ lib, ... }:
{
  # ── Music player: pick one, or none ─────────────────────────────────────
  # Read on the home-manager side (modules/home/apps/media/music-player.nix) via osConfig —
  # same pattern as roudix.videoPlayer / roudix.torrentClient.
  #
  # Used to be two independent roudix.apps.{spotify,ytmdesktop}.enable
  # booleans (both true by default, so both got installed at once) —
  # promoted to a single enum so it's an actual choice, same as
  # videoPlayer/torrentClient.
  options.roudix.musicPlayer = lib.mkOption {
    type    = lib.types.enum [ "none" "spotify" "ytmdesktop" "sonora" ];
    default = "spotify";
    description = ''
      "none"       : No music player installed.
      "spotify"    : Spotify, themed with Spicetify, Roudix default (see
                     roudix.spicetify.* for the theme/extensions).
      "ytmdesktop" : YouTube Music Desktop App — unofficial Electron-based
                     YouTube Music client.
      "sonora"     : Sonora — native (Rust/GPUI) client that handles Spotify,
                     YouTube Music, Apple Music, Deezer and Subsonic in one
                     app (see roudix.sonora.provider). It doesn't bypass
                     anything: if a service requires a subscription, so
                     does Sonora.
    '';
  };

  # Only meaningful when roudix.musicPlayer == "sonora". Read on the
  # home-manager side via osConfig, like roudix.spicetify.*.
  options.roudix.sonora.provider = lib.mkOption {
    type    = lib.types.nullOr lib.types.str;
    default = null;
    example = "youtube";
    description = ''
      Streaming provider Sonora starts on, written to
      programs.sonora.settings.provider. `null` leaves it unset so Sonora asks
      / uses its own default. "youtube" (YouTube Music) is the value shown in
      Sonora's README; for Spotify and the others, check Sonora's settings
      reference for the exact string.
    '';
  };
}
