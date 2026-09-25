{ pkgs, ... }:

# Points Helium at the system's Widevine CDM bundle so DRM-gated content
# (Netflix, Disney+, Spotify Web Player, etc.) plays back. This is only
# imported when "helium" is part of `roudix.browsers` (see common.nix).
#
# Chromium-family browsers look for a JSON pointer file at
# `$XDG_CONFIG_HOME/<AppName>/WidevineCdm/latest-component-updated-widevine-cdm`
# telling them where an already-installed Widevine component lives, instead
# of trying to download one at runtime (which fails on NixOS's read-only
# store). `pkgs.widevine-cdm` ships that component, so we just point Helium
# at it directly.
{
  xdg.configFile."net.imput.helium/WidevineCdm/latest-component-updated-widevine-cdm".text =
    builtins.toJSON {
      Path = "${pkgs.widevine-cdm}/share/google/chrome/WidevineCdm";
    };
}
