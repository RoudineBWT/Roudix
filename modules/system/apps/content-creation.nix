{ config, lib, pkgs, ... }:
let
  cfg = config.roudix.contentCreation;
in
{
  options.roudix.contentCreation = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Enable Roudix content-creation tooling (OBS, video editor, virtual camera).";
    };

    obs = {
      enable = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Install OBS Studio.";
      };

      # One boolean per plugin (like roudix.gaming.apps.<id>.enable) rather
      # than a list: each one gets toggled independently in local.nix, and
      # that's what the wrapOBS in `modules/home/apps/content-creation.nix` consumes.
      # Maps to `pkgs.obs-studio-plugins.*`.
      plugins = {
        vkcapture.enable = lib.mkOption {
          type = lib.types.bool;
          default = true;
          description = "Fast Vulkan/OpenGL game capture — obs-vkcapture.";
        };
        pipewireAudioCapture.enable = lib.mkOption {
          type = lib.types.bool;
          default = true;
          description = "Per-app audio capture via Pipewire — obs-pipewire-audio-capture.";
        };
        backgroundRemoval.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "AI virtual background, no green screen needed — obs-backgroundremoval.";
        };
        moveTransition.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Animated source moves/transitions — obs-move-transition.";
        };
        aitumMultistream.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = ''
            Stream to several platforms at once — obs-aitum-multistream.
            Actively maintained successor to obs-multi-rtmp from the Aitum
            team (also known for obs-vertical-canvas): independent
            encoders/bitrate per platform, more polished UI.
          '';
        };
        gstreamer.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Extra sources/outputs via GStreamer — obs-gstreamer.";
        };
        compositeBlur.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Blur/frosted-glass filters — obs-composite-blur.";
        };
        advancedSceneSwitcher.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Automated scene switching — advanced-scene-switcher.";
        };
        inputOverlay.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "On-screen keyboard/mouse/gamepad overlay — input-overlay.";
        };
        waveform.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Audio waveform/spectrum source — waveform.";
        };
      };
    };

    videoEditor = lib.mkOption {
      type = lib.types.enum [ "kdenlive" "davinci-resolve" "davinci-resolve-studio" "shotcut" "none" ];
      default = "kdenlive";
      description = ''
        Video editor installed (see `modules/home/apps/content-creation.nix`).
        "davinci-resolve" is the free edition; "davinci-resolve-studio" is
        the paid one (same package, requires a Blackmagic license) — both
        are "unfree" and already covered by `nixpkgs.config.allowUnfree`
        (modules/system/nix/common.nix). "shotcut" as a lighter alternative,
        "none" to install none.
      '';
    };

    virtualCamera.enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = ''
        Loads the `v4l2loopback` kernel module, required for OBS's "Start
        Virtual Camera" (or any virtual-webcam tool) to actually have a
        /dev/videoN to write to. Without it the button fails silently.
      '';
    };

    streaming.chatterino.enable = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Install Chatterino2 (fast, lightweight third-party Twitch chat client).";
    };
  };

  config = lib.mkIf cfg.enable {
    boot.extraModulePackages = lib.mkIf cfg.virtualCamera.enable [
      config.boot.kernelPackages.v4l2loopback
    ];
    boot.kernelModules = lib.mkIf cfg.virtualCamera.enable [ "v4l2loopback" ];
    # video_nr=9 to avoid clobbering a real webcam on /dev/video0.
    boot.extraModprobeConfig = lib.mkIf cfg.virtualCamera.enable ''
      options v4l2loopback video_nr=9 card_label="OBS Virtual Camera" exclusive_caps=1
    '';

    # DaVinci Resolve needs an OpenCL ICD to use the AMD GPU (ROCm is
    # already installed by modules/system/gpu/amd.nix) instead of falling
    # back to a very slow CPU-only render.
    hardware.graphics.extraPackages = lib.mkIf
      (lib.hasPrefix "davinci-resolve" cfg.videoEditor && (config.hardware.myGpu or "") == "amd")
      [ pkgs.rocmPackages.clr.icd ];
  };
}
