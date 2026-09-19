{ config, lib, pkgs, ... }:

lib.mkIf (config.hardware.myGpu == "amd") {
  hardware.graphics.enable = true;
  hardware.graphics.enable32Bit = true;

  environment.systemPackages = with pkgs; [
    rocmPackages.rocm-smi
    amdgpu_top
    rocmPackages.clr
    mesa
  ];

  systemd.tmpfiles.rules = [
    "L+ /opt/rocm/hip - - - - ${pkgs.rocmPackages.clr}"
  ];

  boot.initrd.kernelModules = [ "amdgpu" ];

  boot.kernelParams = [
    # Forces S3 deep sleep instead of S0ix (Modern Standby).
    # S0ix is often buggy with amdgpu on Linux kernels → freezes on wake.
    # Safe on all AMD cards (ignored if the BIOS only supports S0ix).
    "mem_sleep_default=deep"

    # Enables automatic GPU recovery after a hang/timeout.
    # Avoids a full freeze by letting the driver reset itself.
    # Applies to all modern RDNA/GCN cards.
    "amdgpu.gpu_recovery=1"

    # Reduces the delay before the kernel detects and tries to recover a
    # GPU hang (in ms). Default is 10000ms (10s) → the screen stays black
    # a long time before recovery. 1000ms = fast reaction without being
    # too aggressive.
    "amdgpu.lockup_timeout=1000"

    # Disables the GPU's runtime PM (power management) between frames.
    # Some AMD cards freeze on wake due to a bad power-gate state.
    # Slightly higher idle power draw, but a reliable fix on RDNA2/RDNA3.
    "amdgpu.runpm=0"

    # Disables the scatter-gather display engine.
    # Known RDNA2/RDNA3 bug under Wayland: random display freezes,
    # sometimes with a full GPU hang. Very common on RX 6xxx/7xxx.
    "amdgpu.sg_display=0"
  ];
}
