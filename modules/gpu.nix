{ config, lib, pkgs, inputs, ... }:
{
  imports = [ "${inputs.glf-os}/modules/default/nvidia.nix" ];

  options.hardware.myGpu = lib.mkOption {
    type = lib.types.enum [ "amd" "nvidia" "intel" ];
    default = "amd";
    description = "GPU type to configure";
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
      glf.nvidia_config.enable = true;
      # optionnel pour laptop :
      # glf.nvidia_config.laptop = true;
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
