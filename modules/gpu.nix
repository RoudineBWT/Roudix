{ config, lib, pkgs, ... }:
{
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
    })

    # ── NVIDIA ───────────────────────────────────────────────────
    (lib.mkIf (config.hardware.myGpu == "nvidia") {
      hardware.nvidia.modesetting.enable = true;
      hardware.nvidia.open = false;
      services.xserver.videoDrivers = [ "nvidia" ];
      hardware.graphics.enable = true;
      hardware.graphics.enable32Bit = true;
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
