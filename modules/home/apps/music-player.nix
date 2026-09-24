{ pkgs, osConfig, lib, ... }:
let
  # Music player — was two independent roudix.apps.{spotify,ytmdesktop}.enable
  # booleans (both true by default); now a choice. "spotify" installs
  # nothing here itself — it's installed via ./spicetify.nix
  # (programs.spicetify), imported below only for that choice. Option
  # declared in modules/system/apps/music-player.nix
  musicPlayerType = osConfig.roudix.musicPlayer or "spotify";

  musicPlayerPackage = {
    ytmdesktop = pkgs.ytmdesktop;
    spotify    = null; # installed via ./spicetify.nix instead
    none       = null;
  }.${musicPlayerType};
in
{
  # Spotify + Spicetify (roudix.musicPlayer == "spotify")
  imports = lib.optional (musicPlayerType == "spotify") ./spicetify.nix;

  # Music player — Spotify (via spicetify.nix, above), ytmdesktop, or none
  home.packages = lib.optional (musicPlayerPackage != null) musicPlayerPackage;
}
