{ config, lib, pkgs, ... }:

lib.mkIf (config.hardware.myGpu == "amd-legacy") {
  hardware.graphics.enable = true;
  hardware.graphics.enable32Bit = true;

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

  environment.systemPackages = with pkgs; [ amdgpu_top ];
}
