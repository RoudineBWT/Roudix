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
      description = "GPU type to configure. 'amd' = discrete RDNA/GCN 3+, 'amd-igpu' = AMD APU (integrated), 'amd-legacy' = GCN 1.x/2.x, 'intel' = Intel iGPU/Arc (all generations, i915 or xe), 'vm' = virtual machines (virtio-gpu, QXL, VMware SVGA).";
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
}
