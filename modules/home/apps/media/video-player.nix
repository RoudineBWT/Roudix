{ pkgs, osConfig, ... }:
let
  # Video player — was hardcoded (clapper, on niri/hyprland/mangowc/umbriel
  # only) or a DE-agnostic opt-in boolean (roudix.apps.mpv.enable); now one
  # DE-agnostic choice. Returns a *list* (clapper needs its enhancers
  # alongside it), unlike the single-package matrix/discord/telegram maps.
  # Option declared in modules/system/apps/media/video-player.nix
  videoPlayerType = osConfig.roudix.videoPlayer or "vlc";

  videoPlayerPackages = {
    clapper   = [ pkgs.clapper pkgs.clapper-enhancers ];
    mpv       = [ pkgs.mpv pkgs.yt-dlp ];
    celluloid = [ pkgs.celluloid ];
    vlc       = [ pkgs.vlc ];
    none      = [ ];
  }.${videoPlayerType};
in
{
  # Video player — VLC (default), clapper, mpv, celluloid, or none
  home.packages = videoPlayerPackages;
}
