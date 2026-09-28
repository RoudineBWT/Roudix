{ pkgs, osConfig, lib, inputs, ... }:
let
  # Music player — was two independent roudix.apps.{spotify,ytmdesktop}.enable
  # booleans (both true by default); now a choice. "spotify" installs
  # nothing here itself — it's installed via ./spicetify.nix
  # (programs.spicetify), imported below only for that choice. "sonora"
  # is installed by its own flake's home-manager module (programs.sonora),
  # also only for that choice. Option declared in
  # modules/system/apps/media/music-player.nix
  musicPlayerType = osConfig.roudix.musicPlayer or "spotify";
  sonoraProvider  = osConfig.roudix.sonora.provider or null;

  musicPlayerPackage = {
    ytmdesktop = pkgs.ytmdesktop;
    spotify    = null; # installed via ./spicetify.nix instead
    sonora     = null; # installed via programs.sonora (inputs.sonora HM module) below
    none       = null;
  }.${musicPlayerType};
in
{
  imports =
    # Spotify + Spicetify (roudix.musicPlayer == "spotify")
    lib.optional (musicPlayerType == "spotify") ./spicetify.nix
    # Sonora (roudix.musicPlayer == "sonora"): module options are only
    # defined when imported, hence the conditional import.
    ++ lib.optional (musicPlayerType == "sonora") inputs.sonora.homeManagerModules.default;

  # Music player — Spotify (via spicetify.nix, above), ytmdesktop, Sonora
  # (below) or none
  home.packages = lib.optional (musicPlayerPackage != null) musicPlayerPackage;
}
// lib.optionalAttrs (musicPlayerType == "sonora") {
  programs.sonora = {
    enable = true;
    # Only set when the user picked a provider (roudix.sonora.provider);
    # otherwise Sonora keeps its own default.
    settings = lib.optionalAttrs (sonoraProvider != null) { provider = sonoraProvider; };
  };
}
