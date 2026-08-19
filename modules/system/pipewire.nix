{ lib, config, options, pkgs, ... }:
{

  options.roudix.pipewire.enable = lib.mkOption {
    description = "Enable Roudix pipewire configurations";
    type = lib.types.bool;
    default = true;
  };

  config = lib.mkIf config.roudix.pipewire.enable {
      boot.kernelParams = [ "usbcore.autosuspend=-1" ];
      security.rtkit.enable = true;

      services.pipewire = {
        enable = true;
        jack.enable = true;
        pulse.enable = true;

        extraConfig.pipewire."92-low-latency" = {
          "context.properties" = {
            "default.clock.rate" = 48000;
            "default.clock.quantum" = 256;
            "default.clock.min-quantum" = 256;
            "default.clock.max-quantum" = 1024;
          };
        };

        alsa = {
          enable = true;
          support32Bit = true;
        };

        wireplumber.extraConfig = {
          "10-disable-camera" = {
            "wireplumber.profiles" = {
              main = {
                "monitor.libcamera" = "disabled";
              };
            };
          };
        };
      };
    };

  }
