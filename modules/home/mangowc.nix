{ pkgs, inputs, config, lib, osConfig, dotfiles, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  mangowcDir = if shellType == "dms"
               then dotfiles + "/mangowc-dms"
               else dotfiles + "/mangowc";

  terminalCmd = osConfig.roudix.terminal or "ghostty";
  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";
  browserCmd = osConfig.roudix.browser.default or null;
in
{
  imports = [
    ./mangohud.nix
    ./papirus-icon.nix
    ./tela-icon.nix
  ];

  config = lib.mkIf (osConfig.roudix.desktop.type == "mangowc") {

    # ── Session target ──────────────────────────────────────────────────────
    # graphical-session.target est "static" (RefuseManualStart=yes) : il ne peut
    # être atteint que via un target qui lui est BindsTo. mango n'a pas ce
    # mécanisme intégré ici (on n'utilise pas wayland.windowManager.mango), donc
    # on le recrée nous-mêmes. C'est lui qui débloque xdg-desktop-portal.service.
    systemd.user.targets.mango-session = {
      Unit = {
        Description = "mango compositor session";
        Documentation = [ "man:systemd.special(7)" ];
        BindsTo = [ "graphical-session.target" ];
        Wants = [ "graphical-session-pre.target" ];
        After = [ "graphical-session-pre.target" ];
      };
    };

    # ── Config files ─────────────────────────────────────────────────────────
    xdg.configFile."mango" = {
      source    = mangowcDir;
      recursive = true;
    };

    # mango.conf est généré par Nix : chemins absolus vers le nix store
    # + source absolu vers user.conf pour éviter tout conflit avec le récursif.
    xdg.configFile."mango/config.conf" = {
      force = true;
      text = ''
        source = ${mangowcDir}/cfg/environment.conf
        source = ${mangowcDir}/cfg/appearance.conf
        source = ${mangowcDir}/cfg/animations.conf
        source = ${mangowcDir}/cfg/input.conf
        source = ${mangowcDir}/cfg/layout.conf
        source = ${mangowcDir}/cfg/monitors.conf
        source = ${mangowcDir}/cfg/workspaces.conf
        source = ${mangowcDir}/cfg/rules.conf
        source = ${mangowcDir}/cfg/keybinds.conf

        # ── Terminal / navigateur / gestionnaire de fichiers (résolus depuis roudix.*) ──
        source = ${config.home.homeDirectory}/.config/mango/apps.conf

        source = ${mangowcDir}/cfg/autostart.conf
        source = ${mangowcDir}/cfg/misc.conf

        # ── User overrides (injected by Nix) ─────────────────────────────
        source = ${config.home.homeDirectory}/.config/mango/user.conf
      '';
    };

    # apps.conf est généré par Nix : override SUPER+Return / SUPER+E / SUPER+B
    # (définis dans keybinds.conf) + les env TERM/TERMINAL (définis dans environment.conf),
    # avec les commandes résolues depuis roudix.*. Sourcé après ces deux fichiers dans
    # config.conf donc les valeurs ci-dessous gagnent.
    # Note : SUPER+SHIFT,B (zen-twilight) reste géré à la main dans keybinds.conf,
    # ce n'est pas un "extra" généré ici.
    xdg.configFile."mango/apps.conf" = {
      force = true;
      text = ''
        # ── Généré par Nix depuis roudix.terminal / roudix.fileManager / roudix.browser ──
        env=TERM,${terminalCmd}
        env=TERMINAL,${terminalCmd}

        bind=SUPER,Return,spawn,${terminalCmd}
        bind=SUPER,E,spawn,${fileManagerCmd}
      '' + lib.optionalString (browserCmd != null) ''
        bind=SUPER,B,spawn,${browserCmd}
      '';
    };

    # ── User overrides file ───────────────────────────────────────────────────
    # Empty by default — the user fills it in home/local.nix.
    xdg.configFile."mango/user.conf" = {
      text = lib.mkDefault ''
        # Personal MangoWC overrides — edit this in home/local.nix
        # See home/local.nix.example for examples (monitors, keybinds, etc.)
      '';
    };

    home.file.".local/bin/screenshot.sh" = {
      executable = true;
      text = ''
        #!/bin/bash
        MODE=''${1:-zone}

        case "$MODE" in
            # Sélection manuelle de zone → annotation Satty
            zone)
                grim -g "$(slurp)" - | satty --filename -
                ;;
            # Output où est le curseur → annotation Satty
            output)
                grim -o "$(slurp -o -f '%o')" - | satty --filename -
                ;;
            # Output où est le curseur → clipboard direct
            screen)
                grim -o "$(slurp -o -f '%o')" - | wl-copy
                ;;
        esac
      '';
    };

    # ── Packages ─────────────────────────────────────────────────────────────
    home.packages = with pkgs; [
      mangowc
      awww
      xwayland-satellite
      playerctl
      wl-clipboard
      pwvucontrol
      kdePackages.qtmultimedia
      mpvpaper
      grim
      slurp
      satty
      rofi


      # Apps
      gnome-text-editor
      gnome-disk-utility
      mission-center
      loupe
      clapper
      gpu-screen-recorder

      # GTK theming
      nwg-look
      adw-gtk3
      papirus-icon-theme
      papirus-folders

      # Qt theming
      qt6Packages.qt6ct
      libsForQt5.qt5ct

      # Misc
      gvfs
      cava
    ]
    ++ lib.optionals (shellType == "noctalia") [
      inputs.noctalia.packages.${pkgs.stdenv.hostPlatform.system}.default
    ]
    ;
  };
}
