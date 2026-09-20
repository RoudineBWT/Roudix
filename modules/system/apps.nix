{ lib, ... }:
{
  # ── Optional "common apps" ────────────────────────────────────────────
  # The first five used to be hardcoded in `modules/home/common.nix`'s
  # package list, so they default to true (matching the previous
  # always-installed behaviour). The rest are new, opt-in additions and
  # default to false. Read on the home-manager side via osConfig.
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

    easyeffects.enable = lib.mkOption {
      type    = lib.types.bool;
      default = true;
      description = "Install EasyEffects + the rnnoise plugin (audio EQ / noise reduction).";
    };

    # ── New, opt-in apps (default false — not part of the base install) ──
    mpv.enable = lib.mkOption {
      type    = lib.types.bool;
      default = false;
      description = "Install mpv + yt-dlp (lightweight media player, with URL/streaming support).";
    };

    qbittorrent.enable = lib.mkOption {
      type    = lib.types.bool;
      default = false;
      description = "Install qBittorrent (torrent client).";
    };

    telegram.enable = lib.mkOption {
      type    = lib.types.bool;
      default = false;
      description = "Install Telegram Desktop.";
    };
  };
}
