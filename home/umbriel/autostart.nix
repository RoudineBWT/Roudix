{ pkgs, config, lib, ... }:

let
  noctalia = lib.getExe config.programs.noctalia.package;
in
{
  programs.umbriel.settings.general.autostart = [
    noctalia
    "${pkgs.xwayland-satellite}/bin/xwayland-satellite"
    "${pkgs.swww}/bin/swww-daemon"
    "${pkgs.discord}/bin/discord"
    "${pkgs.openrgb}/bin/openrgb"
  ];
}
