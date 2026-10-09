{ lib, config, options, pkgs, ... }:
{

  options.roudix.pipewire.enable = lib.mkOption {
    description = "Enable Roudix pipewire configurations";
    type = lib.types.bool;
    default = true;
  };

  config = lib.mkIf config.roudix.pipewire.enable {
      # Keeps USB audio interfaces / headsets from dropping out after idle.
      # Not on laptops: it would fight TLP's USB_AUTOSUSPEND and cost battery.
      boot.kernelParams = lib.optional (!config.roudix.laptop.enable) "usbcore.autosuspend=-1";
      security.rtkit.enable = true;

      # ── CachyOS-Settings audio tweaks ───────────────────────────────────
      # Realtime limits for the audio group (20-audio.conf). NixOS only
      # grants them to @pipewire, and the user isn't in that group.
      security.pam.loginLimits = [
        { domain = "@audio"; item = "rtprio"; type = "-"; value = 99; }
        { domain = "@audio"; item = "nice";   type = "-"; value = -11; }
      ];

      # cpu_dma_latency / RTC / HPET access for the audio group
      # (99-cpu-dma-latency.rules, 40-hpet-permissions.rules)
      services.udev.extraRules = ''
        DEVPATH=="/devices/virtual/misc/cpu_dma_latency", OWNER="root", GROUP="audio", MODE="0660"
        KERNEL=="rtc0", GROUP="audio"
        KERNEL=="hpet", GROUP="audio"
      '';

      # Desktop: the HDA codec never powers down (avoids crackle after idle).
      # Laptop: TLP decides, see SOUND_POWER_SAVE_ON_AC in power/laptop.nix.
      boot.extraModprobeConfig = lib.mkIf (!config.roudix.laptop.enable) ''
        options snd_hda_intel power_save=0
      '';

      services.pipewire = {
        enable = true;
        jack.enable = true;
        pulse.enable = true;

        extraConfig.pipewire."92-low-latency" = {
          "context.properties" = {
            "default.clock.rate" = 48000;
            "default.clock.quantum" = 256;
            # Default stays 256; apps may still ask for lower latency (64)
            # or a bigger buffer (1024) instead of being pinned to 256.
            "default.clock.min-quantum" = 64;
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
