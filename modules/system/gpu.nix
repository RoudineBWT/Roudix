{ config, lib, pkgs, inputs, ... }:
# NOTE: Only GTX 20xx and newer are supported.
# Older GPUs (GTX 16xx and below) are not supported.
{
  imports = [ "${inputs.glf-os}/modules/default/nvidia.nix" ];

  options = {
    hardware.myGpu = lib.mkOption {
      type = lib.types.enum [ "amd" "nvidia" "amd-legacy" "intel" "vm" ];
      default = "amd";
      description = "GPU type to configure. Use 'vm' for virtual machines (virtio-gpu, QXL, VMware SVGA).";
    };

    hardware.nvidiaOpen = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Use open NVIDIA drivers. Enable for Turing/RTX 20xx and newer. Unsupported for GTX 10xx/16xx.";
    };

    hardware.nvidiaLaptop = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Enable NVIDIA laptop mode (PRIME support)";
    };
  };

  config = lib.mkMerge [
    # ── AMD ──────────────────────────────────────────────────────
    (lib.mkIf (config.hardware.myGpu == "amd") {
      hardware.graphics.enable = true;
      hardware.graphics.enable32Bit = true;
      environment.systemPackages = with pkgs; [
        rocmPackages.rocm-smi
        amdgpu_top
        rocmPackages.clr
      ];
      systemd.tmpfiles.rules = [
        "L+ /opt/rocm/hip - - - - ${pkgs.rocmPackages.clr}"
      ];
      boot.initrd.kernelModules = [ "amdgpu" ];
    })

    # ── AMD legacy (GCN 1.x / 2.x — HD 7xxx, R9 2xx) ──────────────────────
    (lib.mkIf (config.hardware.myGpu == "amd-legacy") {
      hardware.graphics.enable = true;
      hardware.graphics.enable32Bit = true;

      boot.extraModprobeConfig = ''
        options amdgpu si_support=1
        options amdgpu cik_support=1
        options radeon si_support=0
        options radeon cik_support=0
      '';

      boot.blacklistedKernelModules = [ "radeon" ];

      # amdgpu doit être chargé avant radeon dans l'initrd
      boot.initrd.kernelModules = [ "amdgpu" ];

      environment.systemPackages = with pkgs; [ amdgpu_top ];
    })

    # ── NVIDIA ───────────────────────────────────────────────────
    (lib.mkIf (config.hardware.myGpu == "nvidia") {
      hardware.graphics.enable = true;
      hardware.graphics.enable32Bit = true;

      glf.nvidia_config = {
        enable = true;
         laptop = config.hardware.nvidiaLaptop; # for laptop (PRIME support)
      };

      # Override open setting from GLF OS config
      hardware.nvidia.open = lib.mkForce config.hardware.nvidiaOpen;
    })

    # ── Intel ────────────────────────────────────────────────────
    (lib.mkIf (config.hardware.myGpu == "intel") {
      hardware.graphics.enable = true;
      hardware.graphics.enable32Bit = true;
      hardware.graphics.extraPackages = with pkgs; [
        intel-media-driver
        vaapiIntel
      ];
      boot.initrd.kernelModules = [ "i915" ];
    })

    # ── VM ────────────────────────────────────────────────────────
    (lib.mkIf (config.hardware.myGpu == "vm") {
      hardware.graphics.enable = true;
      hardware.graphics.enable32Bit = true;
      # virtio-gpu / QXL / VMware SVGA — no vendor-specific drivers needed
    })
  ];
}
