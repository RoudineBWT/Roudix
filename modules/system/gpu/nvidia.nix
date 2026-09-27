{ config, lib, pkgs, ... }:
with lib;
let
  cfg = config.roudix.nvidia_config;

  # nvidia_cachyos is provided by Chaotic-Nyx, precompiled and matched to
  # the Chaotic kernel selected via hardware.myKernelChaotic (see
  # modules/system/boot/kernel.nix) => no local module rebuild on every kernel
  # bump. Variants outside the Chaotic-Nyx cache: no precompiled
  # nvidia_cachyos module for these nixpkgs kernels (linux-zen, default
  # LTS, latest mainline).
  nixpkgsKernelVariants = [ "zen" "nixpkgs-lts" "nixpkgs-latest" ];

  nvidiaDriverPackage =
    # "zen" / "nixpkgs-lts" / "nixpkgs-latest": no precompiled module on
    # Chaotic-Nyx's side for these nixpkgs kernels, so nixpkgs builds the
    # nvidia module locally against the chosen kernel
    # (config.boot.kernelPackages == pkgs.linuxPackages_zen /
    # linuxPackages / linuxPackages_latest, see kernel.nix). All other
    # variants keep the precompiled nvidia_cachyos module.
    if builtins.elem config.hardware.myKernelChaotic nixpkgsKernelVariants then
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
          && builtins.elem config.hardware.myKernelChaotic nixpkgsKernelVariants
          && !config.hardware.nvidiaOpen)
        "hardware.myKernelChaotic = \"${config.hardware.myKernelChaotic}\" with a closed-source NVIDIA driver (hardware.nvidiaOpen = false): the kernel module is not available from any binary cache (nixpkgs only caches the open module for zen/nixpkgs kernels; Chaotic-Nyx doesn't build these at all) and will be compiled locally on every driver bump.";
    }
    # Active nvidia_config quand myGpu == "nvidia"
    (mkIf (config.hardware.myGpu == "nvidia") {
      roudix.nvidia_config = {
        enable = true;
        laptop = config.hardware.nvidiaLaptop;
      };
      hardware.nvidia.open = mkForce config.hardware.nvidiaOpen;
    })

    # Effective configuration when nvidia_config.enable = true
    (mkIf cfg.enable {
      # Replaces roudix.graphics.enable = true (absent outside roudix-OS)
      hardware.graphics = {
        enable = true;
        enable32Bit = true;
        # diagnostics on the same pkgs as the rest of the system
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

      # NVreg_PreserveVideoMemoryAllocations=1 is required for
      # hibernation: the proprietary driver dumps VRAM to
      # NVreg_TemporaryFilePath before suspend/hibernate to restore GPU
      # state on wake. Without it → blackscreen / corrupted GPU state on
      # RTX 4000/5000.
      boot.extraModprobeConfig = ''
        options nvidia NVreg_PreserveVideoMemoryAllocations=1
        options nvidia NVreg_TemporaryFilePath=/var/tmp
      '';

      # nixpkgs unstable no longer generates these units automatically
      # when hardware.nvidia.powerManagement.enable = true — declared
      # explicitly to avoid a blackscreen on resume from
      # sleep/hibernation.
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
