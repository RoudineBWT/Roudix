{ config, pkgs, lib, inputs, ... }:
{
  options.roudix.gaming.enable = lib.mkOption {
    description = "Enable Roudix gaming configurations";
    type = lib.types.bool;
    default = true;
  };
  config = lib.mkIf config.roudix.gaming.enable {
  # ── Steam ────────────────────────────────────────────────────────────────
  programs.steam = {
    enable = true;
    remotePlay.openFirewall = true;       # Remote Play
    dedicatedServer.openFirewall = false; # Serveurs dédiés (optionnel)
    gamescopeSession = { # Gamescope intégré à Steam
      enable = true;
      args = [ "--prefer-output" "DP-1" ]; # remplace DP-x par ton écran principal
    };
    extraCompatPackages = [
      pkgs.proton-ge-bin                  # Proton-GE pour meilleure compatibilité
      inputs.nix-proton-cachyos.packages.${pkgs.stdenv.hostPlatform.system}.proton-cachyos # Proton-GE pour meilleure performance
    ];
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
        gpu_device = 1;
        amd_performance_level = "high"; # Change en "auto" si pas AMD
      };
    };
  };

  security.polkit.extraConfig = ''
    polkit.addRule(function(action, subject) {
      if (action.id == "com.feralinteractive.GameMode" &&
          subject.isInGroup("gamemode")) {
        return polkit.Result.YES;
      }
    });
  '';

  # ── Paquets système gaming ────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    vkbasalt        # Post-processing Vulkan (sharpening, etc.)
  ];

  # ── Support manettes ─────────────────────────────────────────────────────
  hardware.steam-hardware.enable = true; # Support contrôleurs Steam
  services.udev.packages = [ pkgs.game-devices-udev-rules ]; # Xbox, PS, etc.

  };
}
