{ config, pkgs, lib, inputs, ... }:
let
  game-performance = pkgs.writeShellScriptBin "game-performance" ''
    # Helper script to enable the performance gov with proton or others
    if ! command -v ${pkgs.power-profiles-daemon}/bin/powerprofilesctl &>/dev/null; then
        echo "Error: powerprofilesctl not found" >&2
        exit 1
    fi

    # Don't fail if the CPU driver doesn't support performance power profile
    if ! ${pkgs.power-profiles-daemon}/bin/powerprofilesctl list | grep -q 'performance:'; then
        exec "$@"
    fi

    # Set performance governors, as long the game is launched
    if [ -n "$GAME_PERFORMANCE_SCREENSAVER_ON" ]; then
        exec ${pkgs.power-profiles-daemon}/bin/powerprofilesctl launch -p performance \
            -r "Launched with game-performance utility" -- "$@"
    else
        exec ${pkgs.systemd}/bin/systemd-inhibit \
            --why "game-performance is running" \
            ${pkgs.power-profiles-daemon}/bin/powerprofilesctl launch \
            -p performance -r "Launched with game-performance utility" -- "$@"
    fi
  '';
in
{
  options.roudix.gaming.enable = lib.mkOption {
    description = "Enable Roudix gaming configurations";
    type = lib.types.bool;
    default = true;
  };
  config = lib.mkIf config.roudix.gaming.enable {

  # nixpkgs.overlays = [ inputs.millennium.overlays.default ];
  # ── Steam ────────────────────────────────────────────────────────────────
  programs.steam = {
    enable = true;
    remotePlay.openFirewall = true;       # Remote Play
    dedicatedServer.openFirewall = false; # Serveurs dédiés (optionnel)
    gamescopeSession = { # Gamescope intégré à Steam
      enable = true;
      args = [ "--prefer-output" "DP-1" ]; # remplace DP-x par ton écran principal
    };
    package = pkgs.steam.override {
            extraEnv = {
              TZ = ":/etc/localtime";
              OBS_VKCAPTURE = "1";
            };
    };
    extraCompatPackages = [
      pkgs.proton-ge-bin                  # Proton-GE pour meilleure compatibilité
    ];
  };

  # ── Gamescope ────────────────────────────────────────────────────────────
  programs.gamescope = {
    enable = true;
    capSysNice = true; # Permet à gamescope de prioriser les processus
  };

  # ── GameMode ─────────────────────────────────────────────────────────────
  #programs.gamemode = {
  #  enable = true;
  #  settings = {
  #    general = {
  #      renice = 10;
  #    };
  #  };
  #};

  # ── Ananicy-CPP (remplace GameMode) ──────────────────────────────────────
  services.ananicy = {
    enable = true;
    package = pkgs.ananicy-cpp;
    rulesProvider = pkgs.ananicy-rules-cachyos;
  };

  # ── Paquets système gaming ────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    vkbasalt          # Post-processing Vulkan (sharpening, etc.)
    game-performance  # Wrapper governor CPU performance (usage: game-performance %command%)
    scx.full
    # millennium-steam
  ];


  # ── Support manettes ─────────────────────────────────────────────────────
  hardware.steam-hardware.enable = true; # Support contrôleurs Steam
  services.udev.packages = [ pkgs.game-devices-udev-rules ]; # Xbox, PS, etc.

  };
}
