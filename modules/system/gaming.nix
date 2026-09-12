{ config, pkgs, lib, inputs, ... }:
let
  game-performance = pkgs.writeShellScriptBin "game-performance" ''
    #!${pkgs.runtimeShell}
    # Wrapper "à la CachyOS" (game-performance de cachyos-settings), réécrit
    # pour tuned-adm au lieu de powerprofilesctl, et sans dépendre de
    # GameMode (incompatible avec ananicy-cpp chez nous).
    #
    # powerprofilesctl launch fonctionne en interne via un scope systemd
    # (cgroup), qui n'est "terminé" que lorsque TOUS les process du cgroup
    # ont quitté — pas juste le process de premier niveau. C'est ce qui
    # manquait à la version précédente (trap bash sur la sortie de "$@") :
    # Steam peut forker/détacher avant que le vrai jeu démarre, faisant
    # revenir le profil en "balanced" après 2 secondes. On réplique donc le
    # même mécanisme avec systemd-run --scope, qui bloque naturellement
    # jusqu'à ce que le cgroup entier soit vide.

    TUNED_ADM=${pkgs.tuned}/bin/tuned-adm
    GAME_PROFILE=roudix-gaming
    FALLBACK_PROFILE=balanced

    if ! command -v "$TUNED_ADM" &>/dev/null; then
        echo "Error: tuned-adm not found" >&2
        exec "$@"
    fi

    # Don't fail if the profile doesn't exist, just run the command
    if ! "$TUNED_ADM" list | grep -q "$GAME_PROFILE"; then
        exec "$@"
    fi

    # Save the current profile before changing it
    CURRENT_PROFILE=$("$TUNED_ADM" active | awk '{print $NF}')

    # Function to restore profile on exit
    restore_profile() {
        "$TUNED_ADM" profile "''${CURRENT_PROFILE:-$FALLBACK_PROFILE}" &>/dev/null
    }

    # Set trap to restore profile when script exits
    trap restore_profile EXIT INT TERM

    # Set performance profile and launch the game
    "$TUNED_ADM" profile "$GAME_PROFILE"

    # Scope systemd dédié : bloque jusqu'à ce que tout le cgroup se vide,
    # pas juste le process de premier niveau (le "%command%" de Steam)
    if [ -n "''${GAME_PERFORMANCE_SCREENSAVER_ON:-}" ]; then
        ${pkgs.systemd}/bin/systemd-run --user --scope --quiet -- "$@"
    else
        ${pkgs.systemd}/bin/systemd-inhibit --why "game-performance is running" -- \
            ${pkgs.systemd}/bin/systemd-run --user --scope --quiet -- "$@"
    fi

    # Store exit code to return it properly
    EXIT_CODE=$?

    # The trap will automatically restore the profile here
    exit $EXIT_CODE
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
  # Désactivé : incompatible avec ananicy-cpp chez nous. game-performance
  # (via systemd-run --scope) gère maintenant le tracking du process de
  # façon fiable sans passer par GameMode.
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
    settings = {
      cgroup_load = false;
      apply_cgroup = false;
      cgroup_realtime_workaround = lib.mkForce false;
    };
  };

  # ── Paquets système gaming ────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    vkbasalt          # Post-processing Vulkan (sharpening, etc.)
    game-performance  # Wrapper tuned CPU performance (usage: game-performance %command%)
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
