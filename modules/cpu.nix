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
    })
    (lib.mkIf (config.hardware.myCpu == "amd") {
      hardware.cpu.amd.updateMicrocode = true;
      services.hardware.openrgb.motherboard = "amd";
    })
  ];
}
