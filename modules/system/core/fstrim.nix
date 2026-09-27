{ config, lib, ... }:
{
  options.roudix.fstrim.enable = lib.mkOption {
    description = "Enable Roudix fstrim configurations (recommended for SSD/NVMe)";
    type = lib.types.bool;
    default = true;
  };

  config = lib.mkIf config.roudix.fstrim.enable {
    services.fstrim = {
      enable = true;
      interval = "daily";
    };
  };
}
