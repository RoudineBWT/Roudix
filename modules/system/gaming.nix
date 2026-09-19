{ config, pkgs, lib, inputs, ... }:
let
  game-performance = pkgs.writeShellScriptBin "game-performance" ''
    #!${pkgs.runtimeShell}
    # Bazzite/CachyOS-style wrapper for tuned-adm, a simple proven structure
    # (no systemd-run --scope: a classic trap is enough).

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
    # Without this, roudix-game-performance fails silently as soon as
    # it's invoked from the Launch Options: Steam's FHS sandbox only
    # bind-mounts a whitelist of /etc files (not /etc/tuned), so tuned-adm
    # crashes with a FileNotFoundError on tuned-main.conf.
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
  # Disabled: incompatible with ananicy-cpp in this setup. game-performance
  # (via systemd-run --scope) now handles process tracking reliably
  # without going through GameMode.
  #programs.gamemode = {
  #  enable = true;
  #  settings = {
  #    general = {
  #      renice = 10;
  #    };
  #  };
  #};

  # ── Ananicy-CPP (replaces GameMode, opt-in) ──────────────────────────────
  # If roudix.gaming.ananicy.enable = true: starts at boot, stopped by
  # scx-switch when an SCX scheduler is enabled, restarted automatically
  # on the next reboot (original behavior).
  # If false (default): ananicy-cpp isn't even installed. The SCX
  # scheduler chosen via roudix-kernel-switcher persists across reboots
  # instead (see scx-restore-default in scx.nix).
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

  # ── System gaming packages ────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    vkbasalt          # Post-processing Vulkan (sharpening, etc.)
    game-performance  # tuned CPU performance wrapper — binary: roudix-game-performance
                      # Steam Launch Options: /run/current-system/sw/bin/roudix-game-performance %command%
                      # (full path required: Steam doesn't always inherit the current profile's up-to-date PATH)
    gamescope-wsi
    #millennium-steam
  ];

  # ── Controller support ─────────────────────────────────────────────────────
  hardware.steam-hardware.enable = true;
  services.udev.packages = [ pkgs.game-devices-udev-rules ];

  environment.sessionVariables = {
    OBS_VKCAPTURE = "1";
  };
  };
}
