{ config, lib, pkgs, ... }:

# AMD integrated GPU (APU): Ryzen with Radeon Graphics, Ryzen G-series,
# Ryzen 6000/7040/8040/AI 300 laptops, Steam Deck-class hardware...
#
# Differs from amd.nix (discrete RDNA/GCN cards) on purpose:
#   - no ROCm / OpenCL by default (unsupported on most APUs, big closure)
#   - no amdgpu.runpm=0 (runtime PM concerns discrete cards, not APUs)
#   - no mem_sleep_default=deep: recent AMD laptops only expose S0ix
#     (s2idle) and forcing S3 is a regression there. Opt back in through
#     hardware.amdIgpuQuirks = [ "deep-sleep" ] if your BIOS offers a
#     working S3.
let
  cfg = config.hardware;
  # Optimus laptop with an AMD iGPU: myGpu is "nvidia" but the APU still
  # drives the screen and needs firmware + the amdgpu module in the initrd.
  hybridIgpu = cfg.myGpu == "nvidia" && cfg.nvidiaLaptop
    && config.roudix.nvidia_config.amdgpuBusId != null;
  quirkParams = {
    # Scatter/gather display off: display buffers come from the BIOS VRAM
    # carve-out instead of system RAM. Fixes white screens / flicker /
    # freezes seen on some APUs. Costs a bit of VRAM headroom.
    sg-display = "amdgpu.sg_display=0";
    # Panel Self Refresh off: fixes freezes, stutter and flicker on some
    # eDP laptop panels. Slightly higher idle power draw.
    psr = "amdgpu.dcdebugmask=0x10";
    # Force S3 instead of s2idle. Ignored when the BIOS has no S3.
    deep-sleep = "mem_sleep_default=deep";
  };
in
{
  options.hardware = {
    amdIgpuQuirks = lib.mkOption {
      type = lib.types.listOf (lib.types.enum (builtins.attrNames quirkParams));
      default = [ ];
      example = [ "psr" ];
      description = ''
        Opt-in workarounds for AMD APUs, applied only when
        hardware.myGpu = "amd-igpu". Enable one only if you hit the
        matching symptom: "sg-display" (white screen / flicker),
        "psr" (laptop panel freezes or flicker), "deep-sleep" (force S3).
      '';
    };

    amdIgpuGttGiB = lib.mkOption {
      type = lib.types.nullOr lib.types.ints.positive;
      default = null;
      example = 24;
      description = ''
        Maximum amount of system RAM (GiB) the iGPU may map as GTT.
        null keeps the kernel default (about half of the RAM). Raise it
        for large games or local LLMs on a machine with plenty of RAM.
        Must stay below the installed RAM.
      '';
    };

    amdIgpuCompute = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = ''
        Install OpenCL / ROCm userspace for the APU (rocm-smi, HIP).
        ROCm only officially supports a handful of APUs; others usually
        need HSA_OVERRIDE_GFX_VERSION.
      '';
    };
  };

  config = lib.mkIf (cfg.myGpu == "amd-igpu" || hybridIgpu) {
    hardware.graphics.enable = true;
    hardware.graphics.enable32Bit = true;

    # amdgpu needs linux-firmware blobs (PSP, SMU, VCN, DMCUB) to even
    # initialise an APU.
    hardware.enableRedistributableFirmware = lib.mkDefault true;

    boot.initrd.kernelModules = [ "amdgpu" ];

    boot.kernelParams =
      [ "amdgpu.gpu_recovery=1" ]
      ++ map (q: quirkParams.${q}) cfg.amdIgpuQuirks
      # ttm.pages_limit counts 4 KiB pages: 1 GiB = 262144 pages
      ++ lib.optional (cfg.amdIgpuGttGiB != null)
        "ttm.pages_limit=${toString (cfg.amdIgpuGttGiB * 262144)}";

    hardware.amdgpu.opencl.enable = cfg.amdIgpuCompute;

    environment.systemPackages =
      [ pkgs.amdgpu_top ]
      ++ lib.optional cfg.amdIgpuCompute pkgs.rocmPackages.rocm-smi;

    systemd.tmpfiles.rules = lib.optional cfg.amdIgpuCompute
      "L+ /opt/rocm/hip - - - - ${pkgs.rocmPackages.clr}";
  };
}
