{ config, lib, pkgs, inputs, ... }:

let
  cfg = config.roudix;

  browserDefs = {
    "brave"    = { package = pkgs.brave;                                     extras = []; };
    "helium"   = { package = inputs.helium.packages.${pkgs.system}.default;  extras = []; };
    "vivaldi"  = { package = pkgs.vivaldi;                                   extras = [ pkgs.vivaldi-ffmpeg-codecs ]; };
    "chromium" = { package = pkgs.chromium;                                  extras = []; };
    "firefox"  = { package = pkgs.firefox;                                   extras = []; };
    "librewolf"= { package = pkgs.librewolf;                                 extras = []; };
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

    zen.enable = lib.mkOption {
      type    = lib.types.bool;
      default = false;
      description = "Install Zen Browser (from zen-browser flake input).";
    };

  };

  config = {
    environment.systemPackages = selectedBrowserPkgs;
  };
}
