{ config, pkgs, lib, inputs, ... }:
{
  options.hardware.myKernel = lib.mkOption {
    type = lib.types.enum [
      "cachyos-latest"
      "cachyos-latest-v3"
      "cachyos-latest-lto"
      "cachyos-latest-lto-v3"
      "cachyos-bore"
      "cachyos-lts"
      "cachyos-lts-v3"
      "cachyos-lts-lto-v3"
      "cachyos-rc"
    ];
    default = "cachyos-latest-v3";
    description = "CachyOS kernel variant to use";
  };

  config = {
    nixpkgs.overlays = [ inputs.nix-cachyos-kernel.overlays.pinned ];
    boot.kernelPackages = pkgs.linuxKernel.packagesFor (
      {
        "cachyos-latest"        = pkgs.cachyosKernels.linux-cachyos-latest;
        "cachyos-latest-v3"     = pkgs.cachyosKernels.linux-cachyos-latest-x86_64-v3;
        "cachyos-latest-lto"    = pkgs.cachyosKernels.linux-cachyos-latest-lto;
        "cachyos-latest-lto-v3" = pkgs.cachyosKernels.linux-cachyos-latest-lto-x86_64-v3;
        "cachyos-bore" = pkgs.cachyosKernels.linux-cachyos-bore;
        "cachyos-lts" = pkgs.cachyosKernels.linux-cachyos-lts;
        "cachyos-lts-v3" = pkgs.cachyosKernels.linux-cachyos-lts-x86_64-v3;
        "cachyos-lts-lto-v3" = pkgs.cachyosKernels.linux-cachyos-lts-lto-x86_64-v3;
        "cachyos-rc"            = pkgs.cachyosKernels.linux-cachyos-rc;
      }.${config.hardware.myKernel}
    );
  };
}
