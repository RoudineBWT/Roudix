{ config, pkgs, lib, ... }:

{
  options.roudix.waydroid.enable = lib.mkOption {
    description = "Enable Roudix waydroid configurations";
    type = lib.types.bool;
    default = false;
  };

  config = lib.mkIf config.roudix.waydroid.enable {

  virtualisation.waydroid.enable = true;
  # Newer kernel versions may need
  virtualisation.waydroid.package = pkgs.waydroid-nftables;

  # Enable clipboard sharing
  environment.systemPackages = [ pkgs.wl-clipboard ];
  };
}
