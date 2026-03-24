{ config, lib, pkgs, inputs, ... }:
# NOTE: Only GTX 10xx and newer are supported.
# Older GPUs (GTX 900 and below) are not supported.
{
  imports = [ "${inputs.glf-os}/modules/default/nvidia.nix" ];

  options = {
    hardware.myGpu = lib.mkOption {
      type = lib.types.enum [ "amd" "nvidia" "intel" ];
      default = "amd";
      description = "GPU type to configure";
    };

    hardware.nvidiaOpen = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Use open NVIDIA drivers. Enable for Turing/RTX 20xx and newer. Disable for GTX 10xx/16xx.";
    };
  };

  config = lib.mkMerge [
    # ── AMD ──────────────────────────────────────────────────────
    (lib.mkIf (config.hardware.myGpu == "amd") {
      hardware.graphics.enable = true;
      hardware.graphics.enable32Bit = true;
      environment.systemPackages = with pkgs; [
        rocmPackages.rocm-smi
        amdgpu_top
        rocmPackages.clr
      ];
      systemd.tmpfiles.rules = [
        "L+ /opt/rocm/hip - - - - ${pkgs.rocmPackages.clr}"
      ];
    })

    # ── NVIDIA ───────────────────────────────────────────────────
    (lib.mkIf (config.hardware.myGpu == "nvidia") {
      hardware.graphics.enable = true;
      hardware.graphics.enable32Bit = true;

      glf.nvidia_config = {
        enable = true;
        # laptop = true; # uncomment for laptop (PRIME support)
      };

      # Override open setting from GLF OS config
      hardware.nvidia.open = lib.mkForce config.hardware.nvidiaOpen;
    })

    # ── Intel ────────────────────────────────────────────────────
    (lib.mkIf (config.hardware.myGpu == "intel") {
      hardware.graphics.enable = true;
      hardware.graphics.enable32Bit = true;
      hardware.graphics.extraPackages = with pkgs; [
        intel-media-driver
        vaapiIntel
      ];
    })
  ];
}
