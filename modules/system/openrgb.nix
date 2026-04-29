{ pkgs, lib, config, ... }:
{
   config = lib.mkIf (config.roudix.rgb == "openrgb") {
  hardware.i2c.enable = true;
  environment.systemPackages = [ pkgs.openrgb-with-all-plugins ];

  services.hardware.openrgb = {
    enable = true;
    package = pkgs.openrgb-with-all-plugins;
  };

  # Éteint les LEDs une fois au boot puis s'arrête
  systemd.services.openrgb-apply = {
    description = "Turn off RGB LEDs at boot";
    after = [ "multi-user.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = pkgs.writeShellScript "openrgb-apply" ''
        NUM=$(${pkgs.openrgb-with-all-plugins}/bin/openrgb --noautoconnect --list-devices | grep -E '^[0-9]+: ' | wc -l)
        for i in $(seq 0 $((NUM - 1))); do
          ${pkgs.openrgb-with-all-plugins}/bin/openrgb --noautoconnect --device $i --mode static --color 000000
        done
      '';
    };
  };
 };
}
