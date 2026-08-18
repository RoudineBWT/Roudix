{ config, pkgs, lib, ... }:
{
  options.roudix.undervolt.only-amd.enable = lib.mkOption {
    description = "Enable Roudix Amd Undervolting configurations";
    type = lib.types.bool;
    default = false;
  };

  config = lib.mkIf config.roudix.undervolt.only-amd.enable {

boot.kernelParams = [ "amdgpu.ppfeaturemask=0xffffffff" ];
environment.systemPackages = [ pkgs.lact ];
systemd.packages = [ pkgs.lact ];
systemd.services.lactd.wantedBy = [ "multi-user.target" ];
    };
}
