{ lib, ... }:
{
  # ── Optional "common apps" ────────────────────────────────────────────
  # These used to be hardcoded in `modules/home/common.nix`'s package
  # list, so they default to true (matching the previous always-installed
  # behaviour). Read on the home-manager side via osConfig.
  # (mpv and qbittorrent used to live here too — they're now
  # roudix.videoPlayer / roudix.torrentClient, since both gained real
  # alternatives instead of a plain on/off.)
  options.roudix.apps = {
    gimp.enable = lib.mkOption {
      type    = lib.types.bool;
      default = true;
      description = "Install GIMP (image editor).";
    };

    inkscape.enable = lib.mkOption {
      type    = lib.types.bool;
      default = true;
      description = "Install Inkscape (vector graphics editor).";
    };

    spotify.enable = lib.mkOption {
      type    = lib.types.bool;
      default = true;
      description = "Install Spotify, themed with Spicetify (see roudix.spicetify.* for the theme/extensions).";
    };

    songrec.enable = lib.mkOption {
      type    = lib.types.bool;
      default = true;
      description = "Install SongRec (Shazam-like song recognition).";
    };

    ytmdesktop.enable = lib.mkOption {
      type    = lib.types.bool;
      default = true;
      description = "Install YTMDesktop (YouTube Music desktop app).";
    };

    easyeffects.enable = lib.mkOption {
      type    = lib.types.bool;
      default = true;
      description = "Install EasyEffects + the rnnoise plugin (audio EQ / noise reduction).";
    };
  };
}
