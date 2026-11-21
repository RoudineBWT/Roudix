{ lib, config, pkgs, ... }:
let
  cfg = config.roudix.pipewire;
in
{

  options.roudix.pipewire = {
    enable = lib.mkOption {
      description = "Enable Roudix pipewire configurations";
      type = lib.types.bool;
      default = true;
    };

    lowLatency.enable = lib.mkOption {
      description = ''
        Low-latency PipeWire clock (48 kHz, quantum 128, allowed 128-512).
        Off by default: PipeWire then runs with its upstream defaults, like
        Fedora does. Apps can still ask for more buffer (up to 512).
      '';
      type = lib.types.bool;
      default = false;
    };

    realtimeTweaks.enable = lib.mkOption {
      description = ''
        CachyOS-Settings-style realtime tweaks: realtime/nice limits for the
        "audio" group (PAM) and udev access to cpu_dma_latency, rtc0 and hpet
        for that group. The user must be in the "audio" group. Off by default
        (not needed for normal desktop audio).
      '';
      type = lib.types.bool;
      default = false;
    };

    usbNoAutosuspend.enable = lib.mkOption {
      description = ''
        Disable USB autosuspend globally (usbcore.autosuspend=-1). Can help
        USB audio interfaces/headsets that drop out after idle, but it costs
        battery on a laptop (and fights TLP's USB_AUTOSUSPEND). Off by default.
      '';
      type = lib.types.bool;
      default = false;
    };

    elgatoWave3Fix.enable = lib.mkOption {
      description = ''
        Elgato Wave:3 workaround: its microphone captures only silence when
        playback on the device starts before the capture. Disables the
        auto-created Wave:3 sink and lets a WirePlumber script start the capture
        first, then create the sink (jmansar/wavexlr-on-linux-cfg, MIT, see
        dotfiles/wireplumber/). Only the Wave:3 is touched; its nodes become
        "Wave3 Sink" and "wave3-source" (re-select them in your apps). Off by
        default.
      '';
      type = lib.types.bool;
      default = false;
    };
  };

  config = lib.mkIf cfg.enable (lib.mkMerge [
    # Upstream defaults, like Fedora: nothing else is tuned.
    {
      security.rtkit.enable = true;

      services.pipewire = {
        enable = true;
        alsa.enable = true;
        alsa.support32Bit = true; # Steam / Wine
        pulse.enable = true;
        # services.pipewire.jack.enable is deprecated (global LD_LIBRARY_PATH
        # impurity). JACK apps are started through the `pw-jack` wrapper
        # instead: `pw-jack <app>`.
      };
      environment.systemPackages = [ pkgs.pipewire.jack ];
    }

    (lib.mkIf cfg.lowLatency.enable {
      services.pipewire.extraConfig.pipewire."92-low-latency" = {
        "context.properties" = {
          "default.clock.rate" = 48000;
          "default.clock.quantum" = 128;
          "default.clock.min-quantum" = 128;
          "default.clock.max-quantum" = 512;
        };
      };
    })

    (lib.mkIf cfg.realtimeTweaks.enable {
      # Realtime limits for the audio group (CachyOS 20-audio.conf). NixOS only
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
    })

    (lib.mkIf cfg.usbNoAutosuspend.enable {
      boot.kernelParams = [ "usbcore.autosuspend=-1" ];
    })

    (lib.mkIf cfg.elgatoWave3Fix.enable {
      services.pipewire.wireplumber.extraScripts."wavedevicefix.lua" =
        builtins.readFile ../../../dotfiles/wireplumber/wavedevicefix.lua;

      services.pipewire.wireplumber.extraConfig."51-wave3" = {
        "wireplumber.components" = [{
          name = "wavedevicefix.lua";
          type = "script/lua";
          provides = "custom.wave3fix";
          arguments = { device = "wave3"; };
        }];
        "wireplumber.profiles".main."custom.wave3fix" = "required";
        "monitor.alsa.rules" = [
          {
            matches = [ { "node.name" = "~alsa_output.usb-Elgato_Systems_Elgato_Wave_3_*"; } ];
            actions.update-props."node.disabled" = true;
          }
          {
            matches = [ { "node.name" = "~alsa_input.usb-Elgato_Systems_Elgato_Wave_3_*"; } ];
            actions.update-props."node.name" = "wave3-source";
          }
        ];
      };
    })
  ]);

}
