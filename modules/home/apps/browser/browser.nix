{ inputs, lib, osConfig, ... }:
let
  # ── Zen Browser variant ────────────────────────────────────────────────
  # `homeModules.<n>` bakes the channel in at import time (it can't be
  # switched via a config option inside `programs.zen-browser`), so we pick
  # which HM module to import based on `roudix.zen.variant`. Options
  # declared in modules/system/apps/browser/browser.nix
  zenVariant = osConfig.roudix.zen.variant or "twilight";
  zenHomeModules = {
    beta     = inputs.zen-browser.homeModules.beta;
    twilight = inputs.zen-browser.homeModules.twilight;
  };
in
{
  imports = [
    # Zen Browser HM module — imported unconditionally (lazy), only builds
    # anything when `programs.zen-browser.enable` is actually true below.
    # Which channel gets imported is driven by `roudix.zen.variant`.
    zenHomeModules.${zenVariant}
  ]
  # Widevine CDM pointer for Helium (DRM playback), only when helium is
  # actually one of the selected browsers.
  ++ lib.optional (lib.elem "helium" osConfig.roudix.browsers) ./helium-widevine.nix;

  # Note: Zen Browser is not added as a raw home.packages entry — see
  # `programs.zen-browser` below, driven by `osConfig.roudix.zen.*`.
  programs.zen-browser = lib.mkIf osConfig.roudix.zen.enable {
    enable = true;
    profiles.default = {
      sine = {
        enable = osConfig.roudix.zen.sine.enable;
        mods   = osConfig.roudix.zen.sine.mods;
      };
      mods = lib.mkIf (!osConfig.roudix.zen.sine.enable) osConfig.roudix.zen.mods;
    };
  };
}
