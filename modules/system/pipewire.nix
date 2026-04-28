{ lib, config, options, pkgs, ... }:

let
  # nixpkgs >= 26.05 added `services.pipewire.extraLadspaPackages`,
  # which builds an aggregate `pipewire-ladspa-plugins` env and exports
  # LADSPA_PATH on the pipewire user service automatically. On stable
  # 25.11 (and earlier) the option does not exist and we fall back to
  # writing LADSPA_PATH directly on the systemd unit. Detected via
  # introspection of the resolved option tree so we work on both
  # channels without a hard nixpkgs bump.
  hasExtraLadspaPackages =
    options.services.pipewire ? extraLadspaPackages;
in
{

  options.roudix.pipewire.enable = lib.mkOption {
    description = "Enable Roudix pipewire configurations";
    type = lib.types.bool;
    default = true;
  };

  config = lib.mkIf config.roudix.pipewire.enable (lib.mkMerge [
   ({
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
      "default.clock.max-quantum" = 256;
    };
  };
      alsa = {
        enable = true;
        support32Bit = true;
      };

      extraConfig.pipewire."99-noise-suppression" = {
        "context.modules" = [{
          name = "libpipewire-module-filter-chain";
          # nofail keeps pipewire.service alive even if the LADSPA plugin
          # fails to load (transient Nix store unavailability, future
          # API changes in the SPA filter-graph loader, etc.). Without
          # this, a single failed dlopen takes down the whole audio
          # stack with "module is mandatory" -> restart-loop ->
          # start-limit-hit. Matches the upstream sample at
          # ${pipewire}/share/pipewire/filter-chain/source-rnnoise.conf.
          flags = [ "nofail" ];
          args = {
            "node.description" = "Noise Canceling Source";
            "media.name" = "Noise Canceling Source";
            "filter.graph" = {
              nodes = [{
                type = "ladspa";
                name = "rnnoise";
                # Short-name lookup. PipeWire's filter-graph LADSPA loader
                # appends ".so" and searches LADSPA_PATH (set on the
                # pipewire user service above). The 1.6.x SPA-based
                # filter-graph plugin REQUIRES this format — absolute
                # store paths fail with "spa.filter-graph: can't load
                # plugin type 'ladspa': No such file or directory".
                # rnnoise-plugin.ladspa is kept in the system closure
                # via the LADSPA_PATH interpolation (GC-safe).
                plugin = "librnnoise_ladspa";
                # Stereo variant: FL+FR ports must match the audio.position
                # below (2 channels). Using noise_suppressor_mono with two
                # channels triggered "pw.node: can't add port: -28,
                # No space left on device" because the LADSPA plugin
                # exposed a single port for two requested channels.
                label = "noise_suppressor_stereo";
                control = { "VAD Threshold (%)" = 50.0; };
              }];
            };
            # Filter-chain semantics (cf. upstream pipewire docs):
            #   capture.props  = stream that consumes the raw microphone;
            #                    node.passive=true keeps it idle until a
            #                    consumer attaches to the playback side, so
            #                    the host mic is not held open all the time.
            #                    Has no media.class -- it is an internal
            #                    filter input, NOT an Audio/Source.
            #   playback.props = the virtual node apps see; media.class
            #                    Audio/Source declares it as a microphone.
            # Inverting these (capture as Audio/Source, playback as
            # Audio/Sink) caused
            #   "pw.stream: media.class Audio/Source does not expect Input"
            #   "pw.stream: media.class Audio/Sink does not expect Output"
            # in the pipewire log on every session start.
            "capture.props" = {
              "node.name" = "effect_input.rnnoise";
              "node.passive" = true;
              "audio.rate" = 48000;
              "audio.position" = [ "FL" "FR" ];
            };
            "playback.props" = {
              "node.name" = "rnnoise_source";
              "node.description" = "Noise Canceling Source";
              "media.class" = "Audio/Source";
              "audio.rate" = 48000;
              "audio.position" = [ "FL" "FR" ];
            };
          };
        }];
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
   })

   # Plugin discovery for the LADSPA filter-graph. PipeWire 1.6 (shipped
   # in nixos-26.05+) requires plugins by SHORT NAME resolved through
   # LADSPA_PATH; absolute store paths in the conf are rejected with
   # "spa.filter-graph: can't load plugin type 'ladspa': No such file or
   # directory" (cf. upstream sample at
   # ${pipewire}/share/pipewire/filter-chain/source-rnnoise.conf).
   # PipeWire 1.4 (nixos-25.11 stable) tolerates absolute paths via raw
   # dlopen() but the short-name + LADSPA_PATH form works on both, so
   # we standardize on it.
   #
   # Two paths depending on nixpkgs version:
   #   * nixos-26.05+ : the upstream pipewire NixOS module exposes
   #     `services.pipewire.extraLadspaPackages`, builds a
   #     `pipewire-ladspa-plugins` aggregate env, and exports
   #     LADSPA_PATH on pipewire.service automatically. We must use
   #     this option — defining LADSPA_PATH ourselves would conflict
   #     with the upstream definition and abort the eval.
   #   * nixos-25.11 (stable) : the option does not exist. We fall back
   #     to setting LADSPA_PATH directly on the user systemd unit.
   #     Scoped so other LADSPA-using apps (Audacity, Carla) keep
   #     their own LADSPA_PATH expectations intact.
   # In both cases, Nix string interpolation on rnnoise-plugin.ladspa
   # pins the output in the system closure (GC-safe).
   (if hasExtraLadspaPackages then {
      services.pipewire.extraLadspaPackages = [ pkgs.rnnoise-plugin.ladspa ];
    } else {
      systemd.user.services.pipewire.environment.LADSPA_PATH =
        "${pkgs.rnnoise-plugin.ladspa}/lib/ladspa";
    })
  ]);

}
