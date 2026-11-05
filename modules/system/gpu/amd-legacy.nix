{ config, lib, pkgs, ... }:

# AMD GCN 1.x / 2.x: HD 7xxx (Southern Islands), R7/R9 2xx (Sea Islands) and
# the pre-Ryzen APUs built on the same cores: Kaveri / Godavari (A10-7800,
# A10-7850K, A8-7600, ...) are GCN 1.1 (CIK).
#
# Why amdgpu instead of the old radeon driver: Vulkan (Mesa RADV) only runs
# on top of the amdgpu kernel driver. radeon has no Vulkan at all. Both
# families are still flagged experimental in the kernel, hence the explicit
# si_support / cik_support switches below.
#
# NOT for TeraScale (HD 5xxx/6xxx, and APUs older than Kaveri such as the
# A10-5800K "Trinity"): amdgpu does not support them, they stay on radeon
# (OpenGL only, no Vulkan). Do not pick amd-legacy for those: radeon is
# blacklisted here.
lib.mkIf (config.hardware.myGpu == "amd-legacy") {
  hardware.graphics.enable = true;
  hardware.graphics.enable32Bit = true;

  # amdgpu needs the CIK/SI firmware blobs (kaveri_*.bin, bonaire_*.bin, ...)
  # from linux-firmware to initialise the GPU. With radeon blacklisted, a
  # missing blob means no GPU driver at all. Same default as amd-igpu.nix.
  hardware.enableRedistributableFirmware = lib.mkDefault true;

  boot.extraModprobeConfig = ''
    options amdgpu si_support=1
    options amdgpu cik_support=1
    options radeon si_support=0
    options radeon cik_support=0
  '';

  boot.blacklistedKernelModules = [ "radeon" ];

  # amdgpu must load before radeon in the initrd
  boot.initrd.kernelModules = [ "amdgpu" ];

  boot.kernelParams = [
    # Same sleep fix as modern AMD — also relevant on legacy GCN
    "mem_sleep_default=deep"
    "amdgpu.gpu_recovery=1"
    "amdgpu.lockup_timeout=1000"
    # Note: amdgpu.runpm=0 isn't needed on GCN 1.x/2.x since runtime PM
    # isn't enabled by default on these generations.
  ];

  # vulkan-tools: `vulkaninfo --summary` should list "(RADV KAVERI)" / "(RADV
  # BONAIRE)" ..., `vkcube` for a quick smoke test.
  environment.systemPackages = with pkgs; [ amdgpu_top vulkan-tools ];
}
