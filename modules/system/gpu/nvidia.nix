{ config, lib, pkgs, ... }:
with lib;
let
  cfg = config.roudix.nvidia_config;
  nvidiaDriverPackage = config.boot.kernelPackages.nvidiaPackages.mkDriver {
    version = "595.84";
    sha256_64bit = "sha256-mcQE5SExvye8ptoCaNzOPr7cenOrF0BxqZXPGmxeugY=";
    sha256_aarch64 = "sha256-GloNdDFfmXFVu4FAlNNk2qzqLOuw2N5CKatKkcSrQxk=";
    openSha256 = "sha256-pEmA2tUcOKwUPKy6N0QvS49Pdut4/7Phs/JhjdyBcNY=";
    settingsSha256 = "sha256-QrnBM+sdWO4GanO62rxpHmRrjYkYpl5RD6fIiHq4C4A=";
    persistencedSha256 = "sha256-50xYdgx7EEThbaMp4QS8GADbxj0mhBXh8QQN0tWMwRg=";
  };
in
{
  options.roudix.nvidia_config = {
    enable = mkOption {
      type = types.bool;
      default = false;
      description = "Enable nvidia support";
    };
    laptop = mkOption {
      type = types.bool;
      default = false;
      description = "Enable nvidia laptop management";
    };
    intelBusId = mkOption {
      type = types.nullOr types.str;
      default = null;
    };
    nvidiaBusId = mkOption {
      type = types.nullOr types.str;
      default = null;
    };
    amdgpuBusId = mkOption {
      type = types.nullOr types.str;
      default = null;
    };
  };

  config = mkMerge [
    # Active nvidia_config quand myGpu == "nvidia"
    (mkIf (config.hardware.myGpu == "nvidia") {
      roudix.nvidia_config = {
        enable = true;
        laptop = config.hardware.nvidiaLaptop;
      };
      hardware.nvidia.open = mkForce config.hardware.nvidiaOpen;
    })

    # Configuration effective quand nvidia_config.enable = true
    (mkIf cfg.enable {
      # Remplace roudix.graphics.enable = true (absent hors roudix-OS)
      hardware.graphics = {
        enable = true;
        enable32Bit = true;
        # diagnostics sur le même pkgs que le reste du système
        extraPackages = with pkgs; [
          libva-utils
          vulkan-tools
        ];
      };

      environment.variables = {
        __GL_SHADER_DISK_CACHE_SIZE = "12000000000";
        MESA_SHADER_CACHE_MAX_SIZE = "12G";
      };

      services.xserver.videoDrivers = [ "nvidia" ];

      hardware.nvidia = {
        package = nvidiaDriverPackage;
        open = true;
        nvidiaSettings = true;
        modesetting.enable = true;

        prime = {
          intelBusId = optionalString (cfg.intelBusId != null) cfg.intelBusId;
          nvidiaBusId = optionalString (cfg.nvidiaBusId != null) cfg.nvidiaBusId;
          amdgpuBusId = optionalString (cfg.amdgpuBusId != null) cfg.amdgpuBusId;
        };

        dynamicBoost.enable = cfg.laptop;
        powerManagement.enable = true;
        powerManagement.finegrained = false;
      };

      # Fix Nvidia 3000 Dec 2025
      boot.blacklistedKernelModules = [ "nouveau" "nova_core" ];

      # NVreg_PreserveVideoMemoryAllocations=1 requis pour la hibernation :
      # le driver propriétaire dump la VRAM dans NVreg_TemporaryFilePath
      # avant suspend/hibernate pour restaurer l'état GPU au réveil.
      # Sans ça → blackscreen / état GPU corrompu sur RTX 4000/5000.
      boot.extraModprobeConfig = ''
        options nvidia NVreg_PreserveVideoMemoryAllocations=1
        options nvidia NVreg_TemporaryFilePath=/var/tmp
      '';

      # nixpkgs unstable ne génère plus ces units automatiquement quand
      # hardware.nvidia.powerManagement.enable = true — on les déclare
      # explicitement pour éviter un blackscreen à la sortie de veille/hibernation.
      systemd.services.nvidia-suspend = {
        description = "NVIDIA system suspend actions";
        wantedBy = [ "systemd-suspend.service" ];
        before = [ "systemd-suspend.service" ];
        serviceConfig = {
          Type = "oneshot";
          ExecStart = "${nvidiaDriverPackage}/bin/nvidia-sleep.sh suspend";
        };
      };

      systemd.services.nvidia-hibernate = {
        description = "NVIDIA system hibernate actions";
        wantedBy = [ "systemd-hibernate.service" ];
        before = [ "systemd-hibernate.service" ];
        serviceConfig = {
          Type = "oneshot";
          ExecStart = "${nvidiaDriverPackage}/bin/nvidia-sleep.sh hibernate";
        };
      };

      systemd.services.nvidia-resume = {
        description = "NVIDIA system resume actions";
        wantedBy = [ "systemd-suspend.service" "systemd-hibernate.service" ];
        after = [ "systemd-suspend.service" "systemd-hibernate.service" ];
        serviceConfig = {
          Type = "oneshot";
          ExecStart = "${nvidiaDriverPackage}/bin/nvidia-sleep.sh resume";
        };
      };
    })
  ];
}
