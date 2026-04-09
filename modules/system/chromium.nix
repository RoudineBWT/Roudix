{ config, lib, pkgs, inputs, ... }:

let
  cfg = config.roudix;

  browsers = {
    "brave"   = { package = pkgs.brave; extras = []; };
    "helium"  = { package = inputs.helium.packages.${pkgs.system}.default; extras = []; };
    "vivaldi" = { package = pkgs.vivaldi; extras = [ pkgs.vivaldi-ffmpeg-codecs ]; };
    "none"    = { package = null; extras = []; };
  };

  selected = browsers.${cfg.chromium};

in {
  options.roudix.chromium = lib.mkOption {
    type = lib.types.enum [ "brave" "helium" "vivaldi" "none" ];
    default = "brave";
    description = "Choose your favorite chromium base browser. Use 'none' to skip.";
  };

  config = lib.mkIf (cfg.chromium != "none") {
    environment.systemPackages = [ selected.package ] ++ selected.extras;
  };
}
