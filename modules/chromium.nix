{ config, lib, pkgs, inputs, system, ... }:

let
  cfg = config.roudix;

  browsers = {
    "brave"   = {
      package = pkgs.brave;
      extras  = [];
    };
    "helium"  = {
      package = inputs.helium.packages.${system}.default;
      extras  = [];
    };
    "vivaldi" = {
      package = pkgs.vivaldi;
      extras  = [ pkgs.vivaldi-ffmpeg-codecs ];
    };
  };

  selected = browsers.${cfg.chromium};

in {
  options.roudix.chromium = lib.mkOption {
    type = lib.types.enum [ "brave" "helium" "vivaldi" ];
    default = "brave";
    description = "Choose your favorite chromium base browser";
  };

  config = {
    environment.systemPackages = [ selected.package ] ++ selected.extras;
  };
}
