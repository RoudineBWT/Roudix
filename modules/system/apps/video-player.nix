{ lib, ... }:
{
  # ── Video player: pick one, or none ─────────────────────────────────────
  # Read on the home-manager side (modules/home/common.nix) via osConfig —
  # same pattern as roudix.discord / roudix.matrixClient / roudix.telegram.
  #
  # Used to be two separate, unrelated things: Clapper was hardcoded
  # (always installed, no way to turn it off) on niri/hyprland/mangowc/
  # umbriel only, while mpv was a DE-agnostic opt-in boolean
  # (roudix.apps.mpv.enable). Both filled the same role — the video player
  # you get by default — so they're now one choice, applied on every
  # desktop.
  options.roudix.videoPlayer = lib.mkOption {
    type    = lib.types.enum [ "none" "clapper" "mpv" "celluloid" "vlc" ];
    default = "vlc";
    description = ''
      "none"      : No video player installed.
      "vlc"       : VLC — widest format/codec support, Roudix default (works
                    well out of the box on every desktop, GNOME/KDE
                    included).
      "clapper"   : Clapper + clapper-enhancers — modern GTK4 player (was
                    previously hardcoded on niri/hyprland/mangowc/umbriel).
      "mpv"       : mpv + yt-dlp — minimal, scriptable, URL/streaming
                    playback from the command line.
      "celluloid" : Celluloid — GTK front-end for mpv.
    '';
  };
}
