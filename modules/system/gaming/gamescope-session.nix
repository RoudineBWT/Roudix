{ config, lib, pkgs, username, ... }:
let
  cfg         = config.roudix.gaming.gamescopeSession;
  desktopType = config.roudix.desktop.type;

  # ── Per-desktop glue ──────────────────────────────────────────────────────
  # What the Gaming Mode wrapper needs to know about each desktop:
  #   env   : XDG_* variables the display manager would have set for it
  #           (our session is "Steam", so the DM set those of "Steam");
  #   start : command that runs the session and returns when it ends;
  #   quit  : soft logout that ends only the desktop, never the whole
  #           logind session (the wrapper lives in it).
  # hyprland and mangowc aren't wired yet (see the assertion below).
  desktops = {
    niri = {
      env   = "XDG_CURRENT_DESKTOP=niri XDG_SESSION_DESKTOP=niri DESKTOP_SESSION=niri";
      start = "/run/current-system/sw/bin/niri-session";
      quit  = "/run/current-system/sw/bin/niri msg action quit --skip-confirmation";
    };
    umbriel = {
      env   = "XDG_CURRENT_DESKTOP=Umbriel XDG_SESSION_DESKTOP=umbriel DESKTOP_SESSION=umbriel";
      start = "/run/current-system/sw/bin/start-umbriel";
      quit  = "/run/current-system/sw/bin/umbriel msg session-quit:skip-confirmation";
    };
    gnome = {
      env   = "XDG_CURRENT_DESKTOP=GNOME XDG_SESSION_DESKTOP=gnome DESKTOP_SESSION=gnome";
      start = "${pkgs.gnome-session}/bin/gnome-session";
      quit  = "${pkgs.gnome-session}/bin/gnome-session-quit --logout --no-prompt";
    };
    kde = {
      env   = "XDG_CURRENT_DESKTOP=KDE XDG_SESSION_DESKTOP=plasma DESKTOP_SESSION=plasma";
      start = "${pkgs.kdePackages.plasma-workspace}/libexec/plasma-dbus-run-session-if-needed ${pkgs.kdePackages.plasma-workspace}/bin/startplasma-wayland";
      quit  = "${pkgs.kdePackages.qttools}/bin/qdbus org.kde.Shutdown /Shutdown org.kde.Shutdown.logout";
    };
  };
  desk = desktops.${desktopType} or null;

  # time.timeZone is nullable (ISO installer...) but TZ needs a string.
  tz = if config.time.timeZone != null then config.time.timeZone else "UTC";

  # The scripts live next to this file as real .sh files (lintable with
  # shellcheck); @name@ placeholders are filled in here, at eval time.
  fill = file: subs:
    lib.replaceStrings
      (lib.mapAttrsToList (n: _: "@${n}@") subs)
      (lib.attrValues subs)
      (builtins.readFile file);

  # Steam's Decky needs its CEF remote-debugging port, off by default on a
  # desktop Steam client. The flag file is also (re)created at each launch
  # because ~/.steam/steam doesn't exist yet on a fresh install when the
  # activation script runs.
  deckySetup = ''
    if [ -d "$HOME/.steam/steam" ]; then
      touch "$HOME/.steam/steam/.cef-enable-remote-debugging"
    fi
  '';

  launcher = pkgs.writeShellApplication {
    name = "roudix-steam-gamescope";
    runtimeInputs = [ pkgs.coreutils pkgs.gnugrep pkgs.drm_info pkgs.jq pkgs.mangohud ];
    text = fill ./gamescope-session/launcher.sh {
      inherit tz;
      decky_setup = if cfg.decky.enable then deckySetup else ":";
      extra_args  = lib.escapeShellArgs cfg.extraArgs;
    };
  };

  sessionWrapper = pkgs.writeShellApplication {
    name = "roudix-gaming-session";
    runtimeInputs = [ pkgs.coreutils pkgs.procps pkgs.psmisc ];
    text = fill ./gamescope-session/session.sh {
      desktop_env   = desk.env;
      desktop_start = desk.start;
      launcher      = "${launcher}/bin/roudix-steam-gamescope";
    };
  };

  # Name imposed by Steam: it calls this binary from "Switch to Desktop".
  steamosSessionSelect = pkgs.writeShellApplication {
    name = "steamos-session-select";
    runtimeInputs = [ pkgs.coreutils pkgs.procps ];
    text = fill ./gamescope-session/steamos-session-select.sh { };
  };

  returnToGamingMode = pkgs.writeShellApplication {
    name = "roudix-return-to-gaming-mode";
    runtimeInputs = [ pkgs.coreutils pkgs.libnotify ];
    text = fill ./gamescope-session/return-to-gaming-mode.sh {
      desktop_quit = desk.quit;
    };
  };

  returnToGamingModeItem = pkgs.makeDesktopItem {
    name = "roudix-return-to-gaming-mode";
    desktopName = "Return to Gaming Mode";
    comment = "Close the desktop and go back to Steam Big Picture";
    exec = "roudix-return-to-gaming-mode";
    icon = "steam";
    categories = [ "Game" ];
  };

  # Added next to the desktop's own session (sessionPackages is a plain list
  # that merges) instead of replacing nixpkgs' "steam" session with mkForce:
  # nothing here disturbs the sessions the desktop modules declare, and
  # programs.steam.gamescopeSession stays off. GDM/Plasma login/noctalia-
  # greeter/dms-greeter all read their session list from sessionPackages.
  sessionFile =
    (pkgs.writeTextDir "share/wayland-sessions/roudix-gaming-mode.desktop" ''
      [Desktop Entry]
      Name=Steam (Gaming Mode)
      Comment=Steam Big Picture in a gamescope session, switchable to the desktop
      Exec=${sessionWrapper}/bin/roudix-gaming-session
      Type=Application
    '').overrideAttrs
      (_: {
        passthru.providedSessions = [ "roudix-gaming-mode" ];
      });

  deckyPkg      = pkgs.callPackage ../../../pkgs/decky-loader { };
  deckyStateDir = "/var/lib/decky-loader";
  userCfg       = config.users.users.${username};
in
{
  options.roudix.gaming.gamescopeSession = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = ''
        Console-like "Steam (Gaming Mode)" session: pick it on the login
        screen to boot straight into Steam Big Picture inside gamescope.
        "Switch to Desktop" in Steam opens your normal desktop, and the
        "Return to Gaming Mode" app (or `roudix-return-to-gaming-mode`) goes
        back, without passing through the login screen.

        Supported desktops: niri, umbriel, gnome, kde (asserted at build).
        Based on GLF-OS' gamescope module.
      '';
    };

    extraArgs = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      example = [ "--prefer-output" "DP-1" ];
      description = ''
        Extra gamescope arguments for the Gaming Mode session, appended to
        the defaults (VRR, HDR, MangoApp, detected refresh rate).
      '';
    };

    decky.enable = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = ''
        Decky Loader (plugins for Steam's Big Picture / Steam Deck UI).
        Packaged in pkgs/decky-loader, vendored from Jovian-NixOS. No binary
        cache exists for it: the first rebuild compiles it locally (pnpm
        frontend + Python). Works on its own, but its UI lives in Big
        Picture, so it's mostly useful with the Gaming Mode session.
      '';
    };
  };

  config = lib.mkMerge [
    (lib.mkIf (config.roudix.gaming.enable && cfg.enable) (lib.mkMerge [
      {
        assertions = [
          {
            assertion = desk != null;
            message = ''
              roudix.gaming.gamescopeSession.enable: roudix.desktop.type = "${desktopType}" isn't supported yet.
              Supported: ${lib.concatStringsSep ", " (lib.attrNames desktops)}.
            '';
          }
        ];
      }
      (lib.mkIf (desk != null) {
        programs.gamescope.enable = true;

        environment.systemPackages = [
          steamosSessionSelect
          returnToGamingMode
          returnToGamingModeItem
        ];

        # Steam looks for steamos-session-select inside its FHS sandbox.
        programs.steam.extraPackages = [ steamosSessionSelect ];

        services.displayManager.sessionPackages = [ sessionFile ];
      })
    ]))

    (lib.mkIf (config.roudix.gaming.enable && cfg.decky.enable) {
      users.users.decky = {
        group = "decky";
        home = deckyStateDir;
        isSystemUser = true;
      };
      users.groups.decky = { };

      # Decky Loader has to run as root (it drops to the unprivileged user
      # to run plugins); running it unprivileged is unsupported upstream.
      systemd.services.decky-loader = {
        description = "Steam Deck Plugin Loader";
        wantedBy = [ "multi-user.target" ];
        after = [ "network.target" ];
        environment = {
          UNPRIVILEGED_USER = "decky";
          UNPRIVILEGED_PATH = deckyStateDir;
          PLUGIN_PATH = "${deckyStateDir}/plugins";
        };
        preStart = ''
          mkdir -p "${deckyStateDir}"
          chown -R decky: "${deckyStateDir}"
        '';
        serviceConfig = {
          ExecStart = "${deckyPkg}/bin/decky-loader";
          KillMode = "process";
          TimeoutStopSec = 45;
        };
      };

      # Open Steam's CEF debug port (Decky injects through it). Only if Steam
      # already ran once; the Gaming Mode launcher covers the fresh-install case.
      system.activationScripts.deckyLoaderCefDebug.text = ''
        if [ -d "${userCfg.home}/.steam/steam" ]; then
          touch "${userCfg.home}/.steam/steam/.cef-enable-remote-debugging"
          chown ${username}:${userCfg.group} "${userCfg.home}/.steam/steam/.cef-enable-remote-debugging"
        fi
      '';
    })
  ];
}
