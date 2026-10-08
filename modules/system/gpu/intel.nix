{ config, lib, pkgs, ... }:

# Intel graphics, from old iGPUs to the latest generations:
#   - Gen8..Gen12 iGPUs (Broadwell .. Alder/Raptor Lake)     -> i915
#   - Arc Alchemist (DG2), Meteor/Arrow Lake (Xe-LPG)         -> i915 by default, xe optional
#   - Lunar Lake, Battlemage (Arc B-series)                   -> xe by default (kernel >= 6.12)
#   - Panther Lake (Xe3)                                      -> xe by default (kernel >= 6.17)
#
# The kernel decides which driver binds, so nothing is hard-coded here:
# both modules are shipped in the initrd and udev loads the right one.
# GPUs that are too new for the running kernel (or that you want to move
# from i915 to xe) are handed to xe with hardware.intelXeForceProbe.
let
  cfg = config.hardware;
  ids = cfg.intelXeForceProbe;
  # Optimus laptop with an Intel iGPU: hardware.myGpu is "nvidia", but the
  # iGPU still drives the screen and needs its own media / compute stack.
  hybridIgpu = cfg.myGpu == "nvidia" && cfg.nvidiaLaptop
    && config.roudix.nvidia_config.intelBusId != null;
in
{
  options.hardware.intelXeForceProbe = lib.mkOption {
    type = lib.types.listOf (lib.types.strMatching "[0-9a-fA-F]{4}");
    default = [ ];
    example = [ "e20b" ];
    description = ''
      PCI device IDs (4 hex digits, see `lspci -nn`) to hand to the xe
      driver instead of i915. Needed when your GPU is not enabled by
      default in the running kernel yet, or to try xe on Tiger Lake and
      newer iGPUs. Leave empty on Lunar Lake, Battlemage and Panther
      Lake with a recent kernel: they work out of the box.
    '';
  };

  config = lib.mkIf (cfg.myGpu == "intel" || hybridIgpu) {
    hardware.graphics = {
      enable = true;
      enable32Bit = true;
      extraPackages = with pkgs; [
        intel-media-driver      # VA-API (iHD): Gen8 up to Arc / Xe2 / Xe3
        vpl-gpu-rt              # oneVPL / QuickSync runtime (Gen12+, Arc)
        intel-compute-runtime   # OpenCL + Level Zero (Gen12+, Arc, Xe)
        intel-vaapi-driver      # i965 fallback for pre-Gen8 iGPUs
      ];
      extraPackages32 = with pkgs.driversi686Linux; [
        intel-media-driver
      ];
    };

    # GuC / HuC / GSC firmware is mandatory for xe and for Arc on i915.
    hardware.enableRedistributableFirmware = lib.mkDefault true;

    # availableKernelModules (not kernelModules): the initrd carries both
    # drivers and udev loads whichever one matches the PCI device, so early
    # KMS works whatever the generation. The one that doesn't match is
    # never bound.
    boot.initrd.availableKernelModules = [ "i915" "xe" ];

    boot.kernelParams = lib.optionals (ids != [ ]) [
      "i915.force_probe=${lib.concatMapStringsSep "," (i: "!" + i) ids}"
      "xe.force_probe=${lib.concatStringsSep "," ids}"
    ];

    assertions = [{
      assertion = ids == [ ]
        || lib.versionAtLeast config.boot.kernelPackages.kernel.version "6.8";
      message = "hardware.intelXeForceProbe needs a kernel >= 6.8 (xe driver). Pick a newer hardware.myKernel.";
    }];

    environment.systemPackages = with pkgs; [
      intel-gpu-tools          # intel_gpu_top
      nvtopPackages.intel      # nvtop, supports i915 and xe
    ];
  };
}
