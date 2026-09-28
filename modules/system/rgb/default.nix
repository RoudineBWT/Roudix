{ config, lib, pkgs, ... }:

{
  options.roudix.rgb = lib.mkOption {
    type = lib.types.enum [ "openlinkhub" "openrgb" "none" ];
    default = "none";
    description = "RGB control backend to use";
  };

  imports = [
    ./openlinkhub.nix
    ./openrgb.nix
  ];
}
