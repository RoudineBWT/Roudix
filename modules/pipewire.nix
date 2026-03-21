{ lib, config, pkgs, ... }:
{
  options.roudix.pipewire.enable = lib.mkOption {
    description = "Enable Roudix PipeWire configurations";
    type = lib.types.bool;
    default = true;
  };

  # ── PipeWire ─────────────────────────────────────────────────────────────
  config = lib.mkIf config.roudix.pipewire.enable {
  # Disable USB autosuspend to avoid audio dropouts on USB devices
  boot.kernelParams = [ "usbcore.autosuspend=-1" ];

  # Allow PipeWire to run with realtime priority
  security.rtkit.enable = true;

  services.pipewire = {
    enable = true;
    alsa = {
      enable = true;
      support32Bit = true;
    };
    pulse.enable = true;
    jack.enable = true;
    wireplumber.enable = true;

    extraConfig.pipewire."92-low-latency" = {
      "context.properties" = {
        "default.clock.rate" = 48000;
        "default.clock.quantum" = 256;
        "default.clock.min-quantum" = 256;
        "default.clock.max-quantum" = 256;
      };
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
