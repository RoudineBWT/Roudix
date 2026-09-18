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

      plugins = lib.mkOption {
        type = lib.types.listOf (lib.types.enum [
          "vkcapture"
          "pipewire-audio-capture"
          "background-removal"
          "move-transition"
          "multi-rtmp"
          "gstreamer"
          "composite-blur"
          "advanced-scene-switcher"
          "input-overlay"
          "waveform"
        ]);
        default = [ "vkcapture" "pipewire-audio-capture" ];
        description = ''
          Plugins OBS à installer (voir `modules/home/common.nix` pour le
          wrapOBS correspondant). Chaque entrée correspond à un attribut
          `pkgs.obs-studio-plugins.*` :
            vkcapture               → capture Vulkan/OpenGL rapide (jeux)
            pipewire-audio-capture  → capture audio par application (Pipewire)
            background-removal      → fond virtuel par IA, sans fond vert
            move-transition          → transitions/animations de sources
            multi-rtmp                → streamer vers plusieurs plateformes à la fois
            gstreamer                  → sources/sorties supplémentaires via GStreamer
            composite-blur            → filtres de flou/verre dépoli
            advanced-scene-switcher  → changement de scène automatisé
            input-overlay              → overlay clavier/souris/manette
            waveform                    → source waveform/spectre audio
          [] pour installer OBS sans aucun plugin.
        '';
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
