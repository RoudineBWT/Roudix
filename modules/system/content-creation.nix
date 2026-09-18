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
        description = "Installer OBS Studio.";
      };

      # Un booléen par plugin (comme roudix.gaming.apps.<id>.enable) plutôt
      # qu'une liste : chacun se coche/décoche indépendamment dans
      # local.nix, et c'est ce que consomme le wrapOBS de
      # `modules/home/common.nix`. Correspond à `pkgs.obs-studio-plugins.*`.
      plugins = {
        vkcapture.enable = lib.mkOption {
          type = lib.types.bool;
          default = true;
          description = "Capture Vulkan/OpenGL rapide (jeux) — obs-vkcapture.";
        };
        pipewireAudioCapture.enable = lib.mkOption {
          type = lib.types.bool;
          default = true;
          description = "Capture audio par application via Pipewire — obs-pipewire-audio-capture.";
        };
        backgroundRemoval.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Fond virtuel par IA, sans fond vert — obs-backgroundremoval.";
        };
        moveTransition.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Transitions/animations de sources — obs-move-transition.";
        };
        aitumMultistream.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = ''
            Streamer vers plusieurs plateformes à la fois — obs-aitum-multistream.
            Successeur activement maintenu d'obs-multi-rtmp par l'équipe
            Aitum (déjà connue pour obs-vertical-canvas) : encodeurs/bitrate
            indépendants par plateforme, interface plus soignée.
          '';
        };
        gstreamer.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Sources/sorties supplémentaires via GStreamer — obs-gstreamer.";
        };
        compositeBlur.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Filtres de flou/verre dépoli — obs-composite-blur.";
        };
        advancedSceneSwitcher.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Changement de scène automatisé — advanced-scene-switcher.";
        };
        inputOverlay.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Overlay clavier/souris/manette à l'écran — input-overlay.";
        };
        waveform.enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Source waveform/spectre audio — waveform.";
        };
      };
    };

    videoEditor = lib.mkOption {
      type = lib.types.enum [ "kdenlive" "davinci-resolve" "davinci-resolve-studio" "shotcut" "none" ];
      default = "kdenlive";
      description = ''
        Éditeur vidéo installé (voir `modules/home/common.nix`).
        "davinci-resolve" = édition gratuite ; "davinci-resolve-studio" =
        édition payante (même paquet, nécessite une licence Blackmagic) —
        les deux sont "unfree" et déjà couverts par
        `nixpkgs.config.allowUnfree` (modules/system/common.nix).
        "shotcut" en alternative légère, "none" pour n'en installer aucun.
      '';
    };

    virtualCamera.enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = ''
        Charge le module noyau `v4l2loopback`, requis pour que "Start
        Virtual Camera" d'OBS (ou n'importe quel outil de webcam virtuelle)
        ait un /dev/videoN à écrire. Sans ça le bouton échoue silencieusement.
      '';
    };

    streaming.chatterino.enable = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Installer Chatterino2 (client de chat Twitch tiers, léger et rapide).";
    };
  };

  config = lib.mkIf cfg.enable {
    boot.extraModulePackages = lib.mkIf cfg.virtualCamera.enable [
      config.boot.kernelPackages.v4l2loopback
    ];
    boot.kernelModules = lib.mkIf cfg.virtualCamera.enable [ "v4l2loopback" ];
    # video_nr=9 pour éviter d'écraser une vraie webcam sur /dev/video0.
    boot.extraModprobeConfig = lib.mkIf cfg.virtualCamera.enable ''
      options v4l2loopback video_nr=9 card_label="OBS Virtual Camera" exclusive_caps=1
    '';

    # DaVinci Resolve a besoin d'un ICD OpenCL pour utiliser le GPU AMD
    # (ROCm est déjà installé par modules/system/gpu/amd.nix) au lieu de
    # retomber sur un rendu CPU très lent.
    hardware.graphics.extraPackages = lib.mkIf
      (lib.hasPrefix "davinci-resolve" cfg.videoEditor && (config.hardware.myGpu or "") == "amd")
      [ pkgs.rocmPackages.clr.icd ];
  };
}
