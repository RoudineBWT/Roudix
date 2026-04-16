{ config, pkgs, lib, inputs, ... }:
{
  options.hardware.myKernel = lib.mkOption {
    type = lib.types.enum [
      # Latest
      "cachyos-latest"
      "cachyos-latest-v2"
      "cachyos-latest-v3"
      "cachyos-latest-v4"
      "cachyos-latest-zen4"
      "cachyos-latest-lto"
      "cachyos-latest-lto-v2"
      "cachyos-latest-lto-v3"
      "cachyos-latest-lto-v4"
      "cachyos-latest-lto-zen4"
      # LTS
      "cachyos-lts"
      "cachyos-lts-v2"
      "cachyos-lts-v3"
      "cachyos-lts-v4"
      "cachyos-lts-zen4"
      "cachyos-lts-lto"
      "cachyos-lts-lto-v2"
      "cachyos-lts-lto-v3"
      "cachyos-lts-lto-v4"
      "cachyos-lts-lto-zen4"
      # Variants
      "cachyos-bmq"
      "cachyos-bmq-lto"
      "cachyos-bore"
      "cachyos-bore-lto"
      "cachyos-deckify"
      "cachyos-deckify-lto"
      "cachyos-eevdf"
      "cachyos-eevdf-lto"
      "cachyos-hardened"
      "cachyos-hardened-lto"
      "cachyos-rc"
      "cachyos-rc-lto"
      "cachyos-rt-bore"
      "cachyos-rt-bore-lto"
      "cachyos-server"
      "cachyos-server-lto"
    ];
    default = "cachyos-latest-v3";
    description = "CachyOS kernel variant to use";
  };

  config = {
    nixpkgs.overlays = [ inputs.nix-cachyos-kernel.overlays.pinned ];

    # Binary cache
    nix.settings.substituters = [ "https://attic.xuyh0120.win/lantian" ];
    nix.settings.trusted-public-keys = [ "lantian:EeAUQ+W+6r7EtwnmYjeVwx5kOGEBpjlBfPlzGlTNvHc=" ];

    boot.kernelPackages =
      let
        kernels = {
          # Latest
          "cachyos-latest"         = pkgs.cachyosKernels.linux-cachyos-latest;
          "cachyos-latest-v2"      = pkgs.cachyosKernels.linux-cachyos-latest-x86_64-v2;
          "cachyos-latest-v3"      = pkgs.cachyosKernels.linux-cachyos-latest-x86_64-v3;
          "cachyos-latest-v4"      = pkgs.cachyosKernels.linux-cachyos-latest-x86_64-v4;
          "cachyos-latest-zen4"    = pkgs.cachyosKernels.linux-cachyos-latest-zen4;
          "cachyos-latest-lto"     = pkgs.cachyosKernels.linux-cachyos-latest-lto;
          "cachyos-latest-lto-v2"  = pkgs.cachyosKernels.linux-cachyos-latest-lto-x86_64-v2;
          "cachyos-latest-lto-v3"  = pkgs.cachyosKernels.linux-cachyos-latest-lto-x86_64-v3;
          "cachyos-latest-lto-v4"  = pkgs.cachyosKernels.linux-cachyos-latest-lto-x86_64-v4;
          "cachyos-latest-lto-zen4"= pkgs.cachyosKernels.linux-cachyos-latest-lto-zen4;
          # LTS
          "cachyos-lts"            = pkgs.cachyosKernels.linux-cachyos-lts;
          "cachyos-lts-v2"         = pkgs.cachyosKernels.linux-cachyos-lts-x86_64-v2;
          "cachyos-lts-v3"         = pkgs.cachyosKernels.linux-cachyos-lts-x86_64-v3;
          "cachyos-lts-v4"         = pkgs.cachyosKernels.linux-cachyos-lts-x86_64-v4;
          "cachyos-lts-zen4"       = pkgs.cachyosKernels.linux-cachyos-lts-zen4;
          "cachyos-lts-lto"        = pkgs.cachyosKernels.linux-cachyos-lts-lto;
          "cachyos-lts-lto-v2"     = pkgs.cachyosKernels.linux-cachyos-lts-lto-x86_64-v2;
          "cachyos-lts-lto-v3"     = pkgs.cachyosKernels.linux-cachyos-lts-lto-x86_64-v3;
          "cachyos-lts-lto-v4"     = pkgs.cachyosKernels.linux-cachyos-lts-lto-x86_64-v4;
          "cachyos-lts-lto-zen4"   = pkgs.cachyosKernels.linux-cachyos-lts-lto-zen4;
          # Variants
          "cachyos-bmq"            = pkgs.cachyosKernels.linux-cachyos-bmq;
          "cachyos-bmq-lto"        = pkgs.cachyosKernels.linux-cachyos-bmq-lto;
          "cachyos-bore"           = pkgs.cachyosKernels.linux-cachyos-bore;
          "cachyos-bore-lto"       = pkgs.cachyosKernels.linux-cachyos-bore-lto;
          "cachyos-deckify"        = pkgs.cachyosKernels.linux-cachyos-deckify;
          "cachyos-deckify-lto"    = pkgs.cachyosKernels.linux-cachyos-deckify-lto;
          "cachyos-eevdf"          = pkgs.cachyosKernels.linux-cachyos-eevdf;
          "cachyos-eevdf-lto"      = pkgs.cachyosKernels.linux-cachyos-eevdf-lto;
          "cachyos-hardened"       = pkgs.cachyosKernels.linux-cachyos-hardened;
          "cachyos-hardened-lto"   = pkgs.cachyosKernels.linux-cachyos-hardened-lto;
          "cachyos-rc"             = pkgs.cachyosKernels.linux-cachyos-rc;
          "cachyos-rc-lto"         = pkgs.cachyosKernels.linux-cachyos-rc-lto;
          "cachyos-rt-bore"        = pkgs.cachyosKernels.linux-cachyos-rt-bore;
          "cachyos-rt-bore-lto"    = pkgs.cachyosKernels.linux-cachyos-rt-bore-lto;
          "cachyos-server"         = pkgs.cachyosKernels.linux-cachyos-server;
          "cachyos-server-lto"     = pkgs.cachyosKernels.linux-cachyos-server-lto;
        };
      in
        pkgs.linuxKernel.packagesFor kernels.${config.hardware.myKernel};
  };
}
