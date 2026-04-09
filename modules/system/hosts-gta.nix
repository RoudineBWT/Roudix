{ config, lib, ... }:
{
  options.roudix.hosts.gtaFix.enable = lib.mkOption {
    description = "Block BattlEye telemetry hosts (GTA Online single-player fix)";
    type = lib.types.bool;
    default = false;
  };

  config = lib.mkIf config.roudix.hosts.gtaFix.enable {
    networking.extraHosts = ''
      127.0.0.1 paradise-s1.battleye.com
      127.0.0.1 test-s1.battleye.com
      127.0.0.1 paradiseenhanced-s1.battleye.com
    '';
  };
}
