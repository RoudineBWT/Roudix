{ config, lib, ... }:
{
  options.hardware.myCpu = lib.mkOption {
    type = lib.types.enum [ "intel" "amd" ];
    default = "intel";
    description = "CPU type to configure";
  };

  config = lib.mkMerge [
    (lib.mkIf (config.hardware.myCpu == "intel") {
      hardware.cpu.intel.updateMicrocode = true;
      services.hardware.openrgb.motherboard = "intel";
      boot.kernelParams = [ "split_lock_detect=off" ];
      boot.kernelModules = [ "i2c-dev" "i2c-i801" ];
    })
    (lib.mkIf (config.hardware.myCpu == "amd") {
      hardware.cpu.amd.updateMicrocode = true;
      services.hardware.openrgb.motherboard = "amd";
      boot.kernelModules = [ "i2c-dev" "i2c-piix4" ];
    })
  ];
}
