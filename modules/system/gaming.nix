{ config, pkgs, lib, inputs, ... }:
let
  game-performance = pkgs.writeShellScriptBin "game-performance" ''
    #!${pkgs.runtimeShell}
    # Wrapper "à la Bazzite/CachyOS" pour tuned-adm, structure simple éprouvée
    # (pas de systemd-run --scope : un trap classique suffit).

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

    # Launch the game with or without systemd-inhibit
    if [ -n "''${GAME_PERFORMANCE_SCREENSAVER_ON:-}" ]; then
        "$@"
    else
        ${pkgs.systemd}/bin/systemd-inhibit --why "game-performance is running" -- "$@"
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

  options.roudix.gaming.apps = {
    lutris.enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Installer Lutris.";
    };
    heroic.enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Installer Heroic Games Launcher (Epic/GOG/Amazon).";
    };
    faugus.enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Installer Faugus Launcher.";
    };
    prismlauncher.enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Installer Prism Launcher (Minecraft).";
    };
    vintagestory.enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Installer Vintage Story.";
    };
    mangohud.enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Installer MangoHud (overlay de perfs en jeu).";
    };
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
    # Sans ça, roudix-game-performance échoue silencieusement dès qu'il est
    # invoqué depuis les Launch Options : le sandbox FHS de Steam ne
    # bind-mount qu'une liste blanche de fichiers /etc (pas /etc/tuned),
    # donc tuned-adm plante avec un FileNotFoundError sur tuned-main.conf.
    package = pkgs.steam.override {
      extraBwrapArgs = [
        "--ro-bind-try /etc/tuned /etc/tuned"
      ];
    };
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
    game-performance  # Wrapper tuned CPU performance — binaire : roudix-game-performance
                      # Steam Launch Options : /run/current-system/sw/bin/roudix-game-performance %command%
                      # (chemin complet requis : Steam n'hérite pas toujours du PATH à jour du profil courant)
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
