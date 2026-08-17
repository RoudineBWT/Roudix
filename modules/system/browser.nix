{ config, lib, pkgs, inputs, brave-previews, ... }:

let
  cfg = config.roudix;

  browserDefs = {
    "brave"    = { package = pkgs.brave;                                     extras = []; };
    "brave-beta"    = { package = pkgs.brave-beta;                           extras = []; };
    "brave-nightly" = { package = pkgs.brave-nightly;                        extras = []; };
    "brave-origin" = { package = pkgs.brave-origin;                extras = []; };
    "brave-origin-beta" = { package = pkgs.brave-origin-beta;                extras = []; };
    "brave-origin-nightly" = { package = pkgs.brave-origin-nightly;          extras = []; };
    "helium"   = { package = inputs.helium.packages.${pkgs.system}.helium-appimage;  extras = []; };
    "vivaldi"  = { package = pkgs.vivaldi;                                   extras = [ pkgs.vivaldi-ffmpeg-codecs ]; };
    "chromium" = { package = pkgs.chromium;                                  extras = []; };
    "firefox"  = { package = pkgs.firefox;                                   extras = []; };
    "librewolf"= { package = pkgs.librewolf;                                 extras = []; };
    "google-chrome"       = { package = pkgs.google-chrome;                  extras = []; };
    "microsoft-edge"      = { package = pkgs.microsoft-edge;                 extras = []; };
    "ungoogled-chromium"  = { package = pkgs.ungoogled-chromium;             extras = []; };
  };

  # Collect packages for all selected browsers
  selectedBrowserPkgs = lib.concatMap
    (name:
      let b = browserDefs.${name}; in
      lib.optional (b.package != null) b.package ++ b.extras
    )
    cfg.browsers;

in {
  options.roudix = {

    browsers = lib.mkOption {
      type    = lib.types.listOf (lib.types.enum (lib.attrNames browserDefs));
      default = [ "brave" ];
      description = ''
        List of browsers to install.
        Example: [ "brave" "vivaldi" ]
        Use [] to skip all.
      '';
    };

    zen = {
      enable = lib.mkOption {
        type    = lib.types.bool;
        default = false;
        description = "Install Zen Browser (from zen-browser flake input).";
      };

      mods = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [];
        description = ''
          Mod IDs to install from the native Zen theme store
          (https://zen-browser.app/mods). Ignored if `zen.sine.enable = true`.
        '';
      };

      sine = {
        enable = lib.mkOption {
          type    = lib.types.bool;
          default = false;
          description = ''
            Enable the Sine mod loader (bootloader injected at build time,
            no read-only store conflict). Disables the native `zen.mods`
            option on this profile — upstream limitation, the two mod
            systems don't coexist on the same profile.
          '';
        };

        mods = lib.mkOption {
          type = lib.types.listOf lib.types.str;
          default = [];
          description = ''
            Mod IDs to install via the Sine store (falls back to the
            Zen theme store automatically if not found on Sine).
            Use this for mods only available on Sine.
          '';
        };
      };
    };

  };

  config = {
    environment.systemPackages = selectedBrowserPkgs;

    assertions = [
      {
        assertion = !(cfg.zen.sine.enable && cfg.zen.mods != []);
        message = ''
          roudix.zen: `mods` (Zen store) and `sine.enable` can't be used
          together on the same profile. Use `zen.sine.mods` instead when
          `sine.enable = true` (it falls back to the Zen theme store).
        '';
      }
    ];
  };
}
