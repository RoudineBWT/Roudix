{ config, pkgs, lib, inputs, ... }:
let
  game-performance = pkgs.writeShellScriptBin "game-performance" ''
    # Helper script to switch to the Roudix tuned gaming profile while a game
    # or Proton is running, then restore the previous profile afterwards.
    #
    # Parle directement à tuned-adm plutôt qu'à powerprofilesctl/tuned-ppd :
    # on évite la couche de compat PPD (connue pour des switches de profil
    # pas toujours fiables) et on cible directement le profil roudix-gaming
    # par son nom réel.
    set -u

    TUNED_ADM=${pkgs.tuned}/bin/tuned-adm
    GAME_PROFILE=roudix-gaming

    if ! command -v "$TUNED_ADM" &>/dev/null; then
        echo "Error: tuned-adm not found" >&2
        exec "$@"
    fi

    # Ne rien faire si tuned est down ou si le profil n'existe pas
    if ! "$TUNED_ADM" list 2>/dev/null | grep -q "$GAME_PROFILE"; then
        exec "$@"
    fi

    previous_profile=$("$TUNED_ADM" active 2>/dev/null | sed -n 's/^Current active profile: //p')

    restore_profile() {
        if [ -n "''${previous_profile:-}" ]; then
            "$TUNED_ADM" profile "$previous_profile" >/dev/null 2>&1 || true
        fi
    }
    trap restore_profile EXIT

    "$TUNED_ADM" profile "$GAME_PROFILE"

    # Empêche la mise en veille/écran de veille pendant que le jeu tourne,
    # sauf si explicitement désactivé
    if [ -n "''${GAME_PERFORMANCE_SCREENSAVER_ON:-}" ]; then
        "$@"
    else
        ${pkgs.systemd}/bin/systemd-inhibit --why "game-performance is running" -- "$@"
    fi
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
    settings = {
      cgroup_load = false;
      apply_cgroup = false;
      cgroup_realtime_workaround = lib.mkForce false;
    };
  };

  # ── Paquets système gaming ────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    vkbasalt          # Post-processing Vulkan (sharpening, etc.)
    game-performance  # Wrapper governor CPU performance (usage: game-performance %command%)
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
