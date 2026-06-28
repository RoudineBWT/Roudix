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

  # amdgpu doit être chargé avant radeon dans l'initrd
  boot.initrd.kernelModules = [ "amdgpu" ];

  boot.kernelParams = [
    # Même fix veille que pour AMD moderne — aussi pertinent sur GCN legacy
    "mem_sleep_default=deep"
    "amdgpu.gpu_recovery=1"
    "amdgpu.lockup_timeout=1000"
    # Note : amdgpu.runpm=0 n'est pas nécessaire sur GCN 1.x/2.x car le runtime PM
    # n'est pas activé par défaut sur ces générations.
  ];

  environment.systemPackages = with pkgs; [ amdgpu_top ];
}
