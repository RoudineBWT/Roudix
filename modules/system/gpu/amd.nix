{ config, lib, pkgs, ... }:

lib.mkIf (config.hardware.myGpu == "amd") {
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
}
