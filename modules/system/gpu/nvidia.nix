{ config, lib, pkgs, ... }:
with lib;
let
  cfg = config.roudix.nvidia_config;

  # nvidia_cachyos est fourni par Chaotic-Nyx, précompilé et matché au kernel
  # Chaotic sélectionné via hardware.myKernelChaotic (voir modules/system/kernel.nix)
  # => pas de rebuild local du module à chaque bump de kernel.
  nvidiaDriverPackage =
    # "zen" : pas de module précompilé côté Chaotic-Nyx pour linux-zen, donc on
    # laisse nixpkgs builder localement le module nvidia contre le kernel choisi
    # (config.boot.kernelPackages == pkgs.linuxPackages_zen, cf. kernel.nix).
    # Pour toutes les autres variantes on garde le module nvidia_cachyos précompilé.
    if config.hardware.myKernelChaotic == "zen" then
      config.boot.kernelPackages.nvidiaPackages.stable
    else
      let
        drivers = {
          "cachyos"          = pkgs.nvidia_cachyos;
          "cachyos-lts"      = pkgs.nvidia_cachyos-lts;
          "cachyos-server"   = pkgs.nvidia_cachyos-server;
          "cachyos-hardened" = pkgs.nvidia_cachyos-hardened;
        };
      in
        drivers.${config.hardware.myKernelChaotic};
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
    {
      warnings = lib.optional
        (config.hardware.myGpu == "nvidia"
          && config.hardware.myKernelChaotic == "zen"
          && !config.hardware.nvidiaOpen)
        "hardware.myKernelChaotic = \"zen\" with a closed-source NVIDIA driver (hardware.nvidiaOpen = false): the kernel module is not available from any binary cache (nixpkgs only caches the open module for zen; Chaotic-Nyx doesn't build zen at all) and will be compiled locally on every driver bump.";
    }
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
