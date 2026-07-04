{ config, lib, pkgs, ... }:

lib.mkIf (config.hardware.myGpu == "intel") {
  hardware.graphics = {
    enable = true;
    enable32Bit = true;
    extraPackages = with pkgs; [
      intel-media-driver
      intel-vaapi-driver
    ];
  };

  boot.initrd.kernelModules = [ "i915" ];
}
