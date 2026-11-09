{ lib, config, ... }:
{
  imports = [
    ./amd.nix
    ./amd-legacy.nix
    ./amd-igpu.nix
    ./nvidia.nix
    ./intel.nix
    ./vm.nix
    ./mesa-git.nix
  ];

  options = {
    hardware.myGpu = lib.mkOption {
      type = lib.types.enum [ "amd" "amd-igpu" "nvidia" "amd-legacy" "intel" "vm" ];
      default = "amd";
      description = "GPU type to configure. 'amd' = discrete RDNA/GCN 3+, 'amd-igpu' = AMD APU (integrated), 'amd-legacy' = GCN 1.x/2.x via amdgpu (HD 7xxx, R7/R9 2xx, and Kaveri/Godavari APUs like the A10-7800 — needed for Vulkan; NOT for TeraScale HD 5xxx/6xxx), 'intel' = Intel iGPU/Arc (all generations, i915 or xe), 'vm' = virtual machines (virtio-gpu, QXL, VMware SVGA).";
    };

    hardware.nvidiaOpen = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Use open NVIDIA drivers. Enable for Turing/RTX 20xx and newer. Unsupported for GTX 10xx/16xx.";
    };

    hardware.nvidiaKernelSource = lib.mkOption {
      type = lib.types.enum [ "chaotic" "xddxdd" ];
      default = "chaotic";
      description = ''
        Where the kernel comes from on nvidia hosts (hardware.myGpu = "nvidia").

        "chaotic" (default): Chaotic-Nyx kernels (hardware.myKernelChaotic),
                  with the precompiled nvidia_cachyos module matched to the
                  kernel — no local Nvidia module build on kernel bumps.
        "xddxdd": xddxdd/nix-cachyos-kernel and the nixpkgs kernels, i.e. the
                  same list as AMD/Intel (hardware.myKernel). The Nvidia
                  module is not precompiled for these kernels and is built
                  locally on every kernel / driver bump.

        Ignored on non-nvidia hosts.
      '';
    };

    hardware.nvidiaBeta = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = ''
        Use the beta NVIDIA driver (nvidiaPackages.beta) instead of the stable
        one, for people who want to test it. The module is always built
        locally (no precompiled nvidia_cachyos for the beta branch), so
        expect a longer build on every driver bump. Only used when
        hardware.myGpu = "nvidia".
      '';
    };

    hardware.nvidiaLaptop = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Enable NVIDIA laptop mode (PRIME support)";
    };
  };
}
