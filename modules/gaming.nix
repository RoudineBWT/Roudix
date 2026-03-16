{ pkgs, ... }:
{
  # ── Steam ────────────────────────────────────────────────────────────────
  programs.steam = {
    enable = true;
    remotePlay.openFirewall = true;       # Remote Play
    dedicatedServer.openFirewall = false; # Serveurs dédiés (optionnel)
    gamescopeSession.enable = true;       # Gamescope intégré à Steam
    extraCompatPackages = [
      pkgs.proton-ge-bin                  # Proton-GE pour meilleure compatibilité
    ];
    package = pkgs.steam.override {
      extraProfile = ''
        export TZ="Europe/Brussels"
        export TZDIR="/etc/zoneinfo"
      '';
    };
  };

  # ── Gamescope ────────────────────────────────────────────────────────────
  programs.gamescope = {
    enable = true;
    capSysNice = true; # Permet à gamescope de prioriser les processus
  };

  # ── GameMode ─────────────────────────────────────────────────────────────
  programs.gamemode = {
    enable = true;
    settings = {
      general = {
        renice = 10;
      };
      gpu = {
        apply_gpu_optimisations = "accept-responsibility";
        gpu_device = 0;
        amd_performance_level = "high"; # Change en "auto" si pas AMD
      };
    };
  };

  # ── Paquets système gaming ────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    vkbasalt        # Post-processing Vulkan (sharpening, etc.)
  ];

  # ── Support manettes ─────────────────────────────────────────────────────
  hardware.steam-hardware.enable = true; # Support contrôleurs Steam
  services.udev.packages = [ pkgs.game-devices-udev-rules ]; # Xbox, PS, etc.
}
