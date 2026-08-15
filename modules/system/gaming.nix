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
  # État persisté par scx-switch (voir scx.nix) — même fichier, lu ici pour
  # capturer/restaurer l'état "avant jeu" sans dupliquer la logique ananicy /
  # scx-loader / polkit, qui vit déjà entièrement dans scx-switch.
  scxStateFile = "/var/lib/scx-switch/last-scheduler";

  scx-performance = pkgs.writeShellScriptBin "scx-performance" ''
    # Helper script pour activer scx_lavd (latence, gaming) le temps du jeu,
    # via scx-switch (scx.nix), puis restaurer l'état exact d'avant (autre
    # scheduler persistant, ou ananicy-cpp / CFS par défaut) à la sortie.
    if ! command -v scx-switch &>/dev/null; then
        echo "Error: scx-switch not found (voir scx.nix)" >&2
        exec "$@"
    fi

    STATE_FILE="${scxStateFile}"

    # Capture l'état avant de basculer : un scheduler persistant s'il y en
    # avait un (ananicy off), sinon vide (ananicy actif ou CFS/EEVDF par défaut).
    PREV_SCHEDULER=""
    PREV_MODE=""
    if [ -f "$STATE_FILE" ]; then
        read -r PREV_SCHEDULER PREV_MODE < "$STATE_FILE" || true
    fi

    restore_previous() {
        if [ -n "$PREV_SCHEDULER" ]; then
            pkexec scx-switch set "$PREV_SCHEDULER" "$PREV_MODE" &>/dev/null
        else
            pkexec scx-switch unset &>/dev/null
        fi
    }
    trap restore_previous EXIT

    pkexec scx-switch set lavd &>/dev/null

    # Pas de "exec" ici : on a besoin que le shell survive à la commande
    # pour que le trap EXIT (restauration) se déclenche après coup. Avec
    # exec, ce process shell est remplacé et le trap ne se déclenche jamais.
    ${pkgs.systemd}/bin/systemd-inhibit \
        --why "scx-performance is running" \
        -- "$@"
    exit $?
  '';
  steamCompatTools = with pkgs; [
     proton-ge-bin
     proton-cachyos-x86_64-v3
   ];
in
{
  options.roudix.gaming.enable = lib.mkOption {
    description = "Enable Roudix gaming configurations";
    type = lib.types.bool;
    default = true;
  };

  options.roudix.gaming.ananicy.enable = lib.mkOption {
    description = ''
      Active ananicy-cpp au boot (opt-in, désactivé par défaut). Si false,
      roudix-kernel-switcher peut faire persister un scheduler SCX choisi
      manuellement après reboot via scx-restore-default, au lieu de
      retomber sur CFS/EEVDF à chaque démarrage.
    '';
    type = lib.types.bool;
    default = false;
  };

  config = lib.mkIf config.roudix.gaming.enable {

    nixpkgs.overlays = [
      #inputs.millennium.overlays.default
      inputs.nix-gaming-edge.overlays.default
    ];
  # ── Steam ────────────────────────────────────────────────────────────────
  programs.steam = {
    enable = true;
    remotePlay.openFirewall = true;
    dedicatedServer.openFirewall = false;
    gamescopeSession = {
      enable = false;
      args = [ "--prefer-output" "DP-1" ];
    };
    extraCompatPackages = steamCompatTools;
  };

  # ── Gamescope ────────────────────────────────────────────────────────────
  programs.gamescope = {
    enable = true;
    capSysNice = true;
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

  # ── Ananicy-CPP (remplace GameMode, opt-in) ──────────────────────────────
  # Si roudix.gaming.ananicy.enable = true : démarre au boot, stoppé par
  # scx-switch quand un scheduler SCX est activé, redémarré automatiquement
  # au reboot suivant (comportement d'origine).
  # Si false (défaut) : ananicy-cpp n'est même pas installé. Le scheduler SCX
  # choisi via roudix-kernel-switcher persiste après reboot à la place
  # (voir scx-restore-default dans scx.nix).
  services.ananicy = lib.mkIf config.roudix.gaming.ananicy.enable {
    enable = true;
    package = pkgs.ananicy-cpp;
    rulesProvider = pkgs.ananicy-rules-cachyos;
  };

  # ── Paquets système gaming ────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    vkbasalt          # Post-processing Vulkan (sharpening, etc.)
    game-performance  # Wrapper governor CPU performance (usage: game-performance %command%)
    scx-performance   # Wrapper scheduler SCX gaming (usage: scx-performance %command%)
    gamescope-wsi
    #millennium-steam
  ];

  # ── Support manettes ─────────────────────────────────────────────────────
  hardware.steam-hardware.enable = true;
  services.udev.packages = [ pkgs.game-devices-udev-rules ];

  environment.sessionVariables = {
    OBS_VKCAPTURE = "1";
  };
  };
}
