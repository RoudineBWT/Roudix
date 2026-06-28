{ lib, config, ... }:
{
  imports = [
    ./amd.nix
    ./amd-legacy.nix
    ./nvidia.nix
    ./intel.nix
    ./vm.nix
  ];

  options = {
    hardware.myGpu = lib.mkOption {
      type = lib.types.enum [ "amd" "nvidia" "amd-legacy" "intel" "vm" ];
      default = "amd";
      description = "GPU type to configure. Use 'vm' for virtual machines (virtio-gpu, QXL, VMware SVGA).";
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
