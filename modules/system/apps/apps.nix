{ lib, ... }:
{
  # ── Optional "common apps" ────────────────────────────────────────────
  # These used to be hardcoded in `modules/home/apps/common-apps.nix`'s package
  # list, so they default to true (matching the previous always-installed
  # behaviour). Read on the home-manager side via osConfig.
  # (mpv, qbittorrent and spotify/ytmdesktop used to live here too —
  # they're now roudix.videoPlayer / roudix.torrentClient /
  # roudix.musicPlayer, since all three gained real alternatives instead
  # of a plain on/off.)
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

    signal.enable = lib.mkOption {
      type    = lib.types.bool;
      default = false;
      description = "Install Signal Desktop (`pkgs.signal-desktop`).";
    };

    zapzap.enable = lib.mkOption {
      type    = lib.types.bool;
      default = false;
      description = "Install ZapZap, an unofficial native-feeling WhatsApp desktop client (`pkgs.zapzap`).";
    };

    fluxer.enable = lib.mkOption {
      type    = lib.types.bool;
      default = false;
      description = ''
        Install Fluxer, a self-hostable Discord alternative, from the
        nix-gaming-edge flake's prebuilt `fluxer-desktop` package (not in
        nixpkgs yet). Independent of `roudix.discord` and
        `roudix.gaming.enable` — people can want both Discord and Fluxer.
      '';
    };
  };
}
