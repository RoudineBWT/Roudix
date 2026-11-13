{ config, lib, pkgs, ... }:
let
  apps = config.roudix.gaming.apps;
in
{
  # Opt-in tools: not everyone owns a racing wheel, and GOverlay only edits
  # MangoHud / vkBasalt / ReShade configs.
  options.roudix.gaming.apps = {
    oversteer.enable = lib.mkOption {
      description = "Oversteer: configure Logitech, Thrustmaster, Fanatec... racing wheels (adds its udev rules).";
      type = lib.types.bool;
      default = false;
    };
    goverlay.enable = lib.mkOption {
      description = "GOverlay: GUI to configure MangoHud, vkBasalt and ReShade.";
      type = lib.types.bool;
      default = false;
    };
  };

  config = lib.mkMerge [
    (lib.mkIf apps.oversteer.enable {
      environment.systemPackages = [ pkgs.oversteer ];
      services.udev.packages = [ pkgs.oversteer ];
    })
    (lib.mkIf apps.goverlay.enable {
      environment.systemPackages = [ pkgs.goverlay ];
    })
  ];
}
