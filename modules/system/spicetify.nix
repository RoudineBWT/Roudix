{ lib, ... }:
{
  # ── Spicetify (Spotify theming) ──────────────────────────────────────────
  # Only meaningful when `roudix.apps.spotify.enable` is true — that option
  # gates whether `modules/home/spicetify.nix` even gets imported (which is
  # what actually installs Spotify + Spicetify). These just control WHAT
  # gets enabled once it is imported. Read on the home-manager side via
  # osConfig, same pattern as roudix.discord / roudix.matrixClient.
  options.roudix.spicetify = {
    theme = lib.mkOption {
      type = lib.types.enum [ "colorful" "comfy" ];
      default = "colorful";
      description = ''
        Local Spicetify theme to apply:
          "colorful" — sanoojes/spicetify-colorful, many color schemes
                       (default scheme: "noctalia")
          "comfy"    — the bundled Comfy theme (default scheme: "Comfy")
      '';
    };

    colorScheme = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = ''
        Color scheme name inside the chosen theme's `color.ini`. Leave
        `null` to use that theme's own default ("noctalia" for
        "colorful", "Comfy" for "comfy").
      '';
    };

    extensions = {
      adblock.enable = lib.mkOption {
        type    = lib.types.bool;
        default = true;
        description = "Enable the Spicetify adblock extension.";
      };

      hidePodcasts.enable = lib.mkOption {
        type    = lib.types.bool;
        default = true;
        description = "Enable the Spicetify hide-podcasts extension.";
      };
    };

    marketplace.enable = lib.mkOption {
      type    = lib.types.bool;
      default = true;
      description = ''
        Enable the Spicetify Marketplace custom app (browse/install more
        extensions and themes from inside Spotify itself).
      '';
    };
  };
}
