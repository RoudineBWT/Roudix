{ config, lib, pkgs, inputs, ... }:
# NOTE: Only GTX 20xx and newer are supported.
# Older GPUs (GTX 16xx and below) are not supported.
{
  imports = [ "${inputs.glf-os}/modules/default/nvidia.nix" ];

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

  config = lib.mkMerge [
    # ── AMD ──────────────────────────────────────────────────────
    (lib.mkIf (config.hardware.myGpu == "amd") {
      hardware.graphics.enable = true;
      hardware.graphics.enable32Bit = true;

      environment.systemPackages = with pkgs; [
        rocmPackages.rocm-smi
        amdgpu_top
        rocmPackages.clr
        mesa
      ];

      systemd.tmpfiles.rules = [
        "L+ /opt/rocm/hip - - - - ${pkgs.rocmPackages.clr}"
      ];

      boot.initrd.kernelModules = [ "amdgpu" ];

      boot.kernelParams = [
        # Force S3 deep sleep au lieu de S0ix (Modern Standby).
        # S0ix est souvent buggé avec amdgpu sur les kernels Linux → freeze au réveil.
        # Safe sur toutes les cartes AMD (ignoré si le BIOS ne supporte que S0ix).
        "mem_sleep_default=deep"

        # Active la récupération automatique du GPU après un hang/timeout.
        # Evite le freeze complet en laissant le driver se reset tout seul.
        # Valable pour toutes les cartes RDNA/GCN modernes.
        "amdgpu.gpu_recovery=1"

        # Réduit le délai avant que le kernel détecte et tente de récupérer un GPU hang (en ms).
        # Par défaut 10000ms (10s) → l'écran reste noir longtemps avant récupération.
        # 1000ms = réaction rapide sans être trop aggressif.
        "amdgpu.lockup_timeout=1000"

        # Désactive le runtime PM (power management) du GPU entre les frames.
        # Certaines cartes AMD freezent au réveil à cause d'un mauvais état de power gate.
        # Légèrement plus de conso idle, mais fix fiable sur RDNA2/RDNA3.
        "amdgpu.runpm=0"

        # Désactive le scatter-gather display engine.
        # Bug connu RDNA2/RDNA3 sous Wayland : freezes aléatoires de l'affichage,
        # parfois accompagnés d'un hang GPU complet. Très fréquent sur RX 6xxx/7xxx.
        "amdgpu.sg_display=0"
      ];
    })

    # ── AMD legacy (GCN 1.x / 2.x — HD 7xxx, R9 2xx) ──────────────────────
    (lib.mkIf (config.hardware.myGpu == "amd-legacy") {
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
    })

    # ── NVIDIA ───────────────────────────────────────────────────
    (lib.mkIf (config.hardware.myGpu == "nvidia") {
      hardware.graphics.enable = true;
      hardware.graphics.enable32Bit = true;

      glf.nvidia_config = {
        enable = true;
        laptop = config.hardware.nvidiaLaptop;
      };

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
      boot.initrd.kernelModules = [ "i915" ];
    })

    # ── VM ────────────────────────────────────────────────────────
    (lib.mkIf (config.hardware.myGpu == "vm") {
      hardware.graphics.enable = true;
      hardware.graphics.enable32Bit = true;
      # virtio-gpu / QXL / VMware SVGA — no vendor-specific drivers needed
    })
  ];
}
