{ pkgs, inputs, config, lib, osConfig, dotfiles, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isUmbriel = osConfig.roudix.desktop.type == "umbriel";

  terminalCmd = osConfig.roudix.terminal or "ghostty";
  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";
  browserDefault = osConfig.roudix.browser.default or null;
  browserCmd     = osConfig.roudix.browser.command or null;
  browserList    = osConfig.roudix.browser.commands or [ ];
  extraBrowsers  = lib.filter (b: b.name != browserDefault) browserList;

  # Utiliser pkgs.formats.toml pour générer proprement
  tomlFormat = pkgs.formats.toml { };

  # Génération de la config TOML
  umbrielConfig = pkgs.writeText "umbriel-config.toml" (builtins.readFile (tomlFormat.generate "umbriel-settings" {
    general = {
      screenshot-path = "~/Pictures/umbriel-screenshots/from %Y-%m-%d %H-%M-%S.png";
      prefer-no-csd = true;
    };
    environment = {
      LD_PRELOAD = "";
      MOZ_ENABLE_WAYLAND = "1";
      XDG_SESSION_TYPE = "wayland";
      XDG_CURRENT_DESKTOP = "umbriel";
      XDG_SESSION_DESKTOP = "umbriel";
      MOZ_DBUS_REMOTE = "1";
      GDK_BACKEND = "wayland";
      QT_AUTO_SCREEN_SCALE_FACTOR = "1";
      QT_WAYLAND_FORCE_DPI = "physical";
      EGL_PLATFORM = "wayland";
      CLUTTER_BACKEND = "wayland";
      TERM = "ghostty";
      TERMINAL = "ghostty";
      _JAVA_AWT_WM_NONREPARENTING = "1";
      ELECTRON_OZONE_PLATFORM_HINT = "auto";
      QT_QPA_PLATFORMTHEME = "qt6ct";
      QT_QPA_PLATFORMTHEME_QT6 = "qt6ct";
      GTK_IM_MODULE = "simple";
    };
    layout = {
      gaps = 9;
      center-focused-column = "never";
      background-color = "transparent";
      preset-column-widths = [
        { proportion = 0.33333; }
        { proportion = 0.5; }
        { proportion = 0.66667; }
      ];
    };
    animations = {
      workspace-switch = {
        spring-damping-ratio = 1.0;
        spring-stiffness = 1000;
        epsilon = 0.0001;
      };
      window-open = {
        duration-ms = 200;
        curve = "ease-out-quad";
      };
      window-close = {
        duration-ms = 200;
        curve = "ease-out-cubic";
      };
      horizontal-view-movement = {
        spring-damping-ratio = 1.0;
        spring-stiffness = 900;
        epsilon = 0.0001;
      };
      window-movement = {
        spring-damping-ratio = 1.0;
        spring-stiffness = 800;
        epsilon = 0.0001;
      };
      window-resize = {
        spring-damping-ratio = 1.0;
        spring-stiffness = 1000;
        epsilon = 0.0001;
      };
      config-notification-open-close = {
        spring-damping-ratio = 0.6;
        spring-stiffness = 1200;
        epsilon = 0.001;
      };
      screenshot-ui-open = {
        duration-ms = 300;
        curve = "ease-out-quad";
      };
      overview-open-close = {
        spring-damping-ratio = 1.0;
        spring-stiffness = 900;
        epsilon = 0.0001;
      };
    };
    input = {
      keyboard = {
        layout = "us";
        variant = "intl";
        numlock = true;
      };
      touchpad = {
        tap = true;
        natural-scroll = true;
      };
      mouse = {
        accel-profile = "flat";
      };
      focus-follows-mouse = true;
      workspace-auto-back-and-forth = true;
    };
    cursor = {
      xcursor-theme = "Bibata-Modern-Ice";
      xcursor-size = 24;
      hide-when-typing = true;
      hide-after-inactive-ms = 1000;
    };
    blur = {
      passes = 2;
      offset = 3.0;
      noise = 0.03;
      saturation = 1.0;
    };
    output = {
      "HKC OVERSEAS LIMITED 24E4 0000000000001" = {
        mode = "1920x1080@165.001";
        scale = 1;
        transform = "normal";
        position = [0 0];
      };
      "Lenovo Group Limited Legion 27Q-10 UNA07260" = {
        mode = "2560x1440@240.000";
        scale = 1;
        transform = "normal";
        position = [1920 0];
        variable-refresh-rate = { on-demand = true; };
      };
    };
    keybinds = {
      "MOD+Return" = "spawn:${terminalCmd}";
      "MOD+E" = "spawn:${fileManagerCmd}";
    } // (lib.optionalAttrs (browserCmd != null) {
      "MOD+B" = "spawn:${browserCmd}";
    }) // (lib.listToAttrs (lib.imap1 (i: b: {
      name = "MOD+Ctrl+Alt+${toString i}";
      value = "spawn:${b.command}";
    }) extraBrowsers)) // {
      "MOD+D" = "spawn:noctalia msg panel-toggle launcher";
      "MOD+Shift+B" = "spawn:zen-twilight";
      "MOD+Alt+L" = "spawn:noctalia msg screen-lock";
      "Mod+Shift+Q" = "spawn:noctalia msg panel-toggle session";
      "XF86AudioRaiseVolume" = { command = "noctalia msg volume-up"; allow-when-locked = true; };
      "XF86AudioLowerVolume" = { command = "noctalia msg volume-down"; allow-when-locked = true; };
      "XF86AudioMute" = { command = "noctalia msg volume-mute"; allow-when-locked = true; };
      "XF86AudioMicMute" = { command = "noctalia msg mic-mute"; allow-when-locked = true; };
      "XF86AudioPlay" = { command = "playerctl play-pause"; allow-when-locked = true; };
      "XF86AudioPrev" = { command = "playerctl previous"; allow-when-locked = true; };
      "XF86AudioNext" = { command = "playerctl next"; allow-when-locked = true; };
      "MOD+Q" = "window-close";
      "MOD+Left" = "focus-column-left";
      "MOD+H" = "focus-column-left";
      "MOD+Right" = "focus-column-right";
      "MOD+L" = "focus-column-right";
      "MOD+Up" = "focus-window-up";
      "MOD+K" = "focus-window-up";
      "MOD+Down" = "focus-window-down";
      "MOD+J" = "focus-window-down";
      "MOD+Ctrl+Left" = "move-column-left";
      "MOD+Ctrl+H" = "move-column-left";
      "MOD+Ctrl+Right" = "move-column-right";
      "MOD+Ctrl+L" = "move-column-right";
      "MOD+Ctrl+Up" = "move-window-up";
      "MOD+Ctrl+K" = "move-window-up";
      "MOD+Ctrl+Down" = "move-window-down";
      "MOD+Ctrl+J" = "move-window-down";
      "MOD+WheelScrollDown" = { command = "focus-workspace-down"; cooldown-ms = 150; };
      "MOD+WheelScrollUp" = { command = "focus-workspace-up"; cooldown-ms = 150; };
      "MOD+Ctrl+WheelScrollDown" = { command = "move-column-to-workspace-down"; cooldown-ms = 150; };
      "MOD+Ctrl+WheelScrollUp" = { command = "move-column-to-workspace-up"; cooldown-ms = 150; };
      "MOD+1" = "focus-workspace 1";
      "MOD+2" = "focus-workspace 2";
      "MOD+3" = "focus-workspace 3";
      "MOD+4" = "focus-workspace 4";
      "MOD+5" = "focus-workspace 5";
      "MOD+6" = "focus-workspace 6";
      "MOD+7" = "focus-workspace 7";
      "MOD+8" = "focus-workspace 8";
      "MOD+9" = "focus-workspace 9";
      "MOD+Ctrl+1" = "move-column-to-workspace 1";
      "MOD+Ctrl+2" = "move-column-to-workspace 2";
      "MOD+Ctrl+3" = "move-column-to-workspace 3";
      "MOD+Ctrl+4" = "move-column-to-workspace 4";
      "MOD+Ctrl+5" = "move-column-to-workspace 5";
      "MOD+Ctrl+6" = "move-column-to-workspace 6";
      "MOD+Ctrl+7" = "move-column-to-workspace 7";
      "MOD+Ctrl+8" = "move-column-to-workspace 8";
      "MOD+Ctrl+9" = "move-column-to-workspace 9";
      "MOD+Tab" = "focus-workspace-previous";
      "Alt+Tab" = "spawn:noctalia msg window-switcher";
      "MOD+Ctrl+F" = "expand-column-to-available-width";
      "MOD+C" = "center-column";
      "MOD+Ctrl+C" = "center-visible-columns";
      "MOD+-" = "set-column-width -10%";
      "MOD+=" = "set-column-width +10%";
      "MOD+Shift+-" = "set-window-height -10%";
      "MOD+Shift+=" = "set-window-height +10%";
      "MOD+T" = "toggle-window-floating";
      "MOD+F" = "fullscreen-window";
      "MOD+W" = "toggle-column-tabbed-display";
      "Ctrl+Shift+1" = "screenshot";
      "Ctrl+Shift+2" = "screenshot-screen";
      "Ctrl+Shift+3" = "screenshot-window";
      "MOD+Escape" = { command = "toggle-keyboard-shortcuts-inhibit"; allow-inhibiting = false; };
      "Ctrl+Alt+Delete" = "quit";
      "MOD+Shift+R" = "spawn:noctalia msg config-reload";
      "MOD+Shift+P" = "power-off-monitors";
      "MOD+O" = { command = "toggle-overview"; repeat = false; };
    };
    geometry-corner-radius = 20;
    clip-to-geometry = true;
    window-rule = [
      {
        match = { app-id = "discord"; };
        open-on-workspace = "󰊗";
        default-column-width = { fixed = 1316; };
        default-window-height = { fixed = 1011; };
        default-floating-position = { x = 0; y = 0; relative-to = "top-left"; };
      }
      {
        match = { app-id = "Element"; };
        open-on-workspace = "󰊗";
        default-column-width = { fixed = 1316; };
        default-window-height = { fixed = 1011; };
        default-floating-position = { x = 0; y = 0; relative-to = "top-left"; };
      }
      {
        match = { app-id = "com.mitchellh.ghostty"; };
        open-floating = true;
        background-effect = { blur = true; xray = false; };
      }
      {
        match = { app-id = "org.telegram.desktop"; };
        open-on-workspace = "󰊗";
        default-column-width = { fixed = 555; };
        default-window-height = { fixed = 1011; };
        default-floating-position = { x = 0; y = 0; relative-to = "top-right"; };
      }
      {
        match = { app-id = "firefox"; };
        open-on-workspace = "󰈹";
        open-maximized = true;
      }
      {
        match = { title = "About Mozilla Firefox"; };
        open-on-workspace = "󰈹";
        open-floating = true;
      }
      {
        match = { app-id = "dev.zed.Zed"; };
        open-on-workspace = "󰊗";
        open-maximized = true;
      }
      {
        match = { app-id = "zen-twilight"; };
        open-on-workspace = "󰈹";
        open-maximized = true;
        draw-border-with-background = false;
        opacity = 0.95;
        background-effect = { blur = true; xray = false; };
      }
      {
        match = { title = "About Zen Twilight"; };
        open-on-workspace = "󰈹";
        open-floating = true;
        draw-border-with-background = false;
        opacity = 0.95;
        background-effect = { blur = true; xray = false; };
      }
      {
        match = { app-id = "brave-origin-beta"; };
        open-on-workspace = "󰈹";
        open-maximized = true;
      }
      {
        match = { app-id = "^org.gnome.Nautilus$"; title = "^Save As$"; };
        open-focused = true;
      }
      {
        match = { app-id = "com.mitchellh.ghostty"; };
        default-column-width = { fixed = 1505; };
        default-window-height = { fixed = 755; };
        open-floating = true;
      }
      {
        match = { app-id = "steam"; };
        open-on-workspace = "󰊗";
        open-maximized = true;
      }
      {
        match = { app-id = "openrgb"; };
        open-on-workspace = "󰊗";
      }
      {
        match = { app-id = "kitty"; };
        open-on-workspace = "󰊗";
        open-floating = true;
      }
      {
        match = { app-id = "org.gnome.Ptyxis"; };
        open-on-workspace = "󰊗";
      }
      {
        match = { app-id = "brave-browser"; };
        open-on-workspace = "󰊗";
        open-maximized = true;
      }
      {
        match = { app-id = "^(steam_app_.*)$"; };
        open-on-workspace = "󰊗";
        open-fullscreen = true;
      }
      {
        match = { app-id = "^heroic$"; };
        open-on-workspace = "󰊗";
        open-fullscreen = true;
      }
      {
        match = { app-id = "org.prismlauncher.PrismLauncher"; };
        open-on-workspace = "󰊗";
        open-maximized = true;
      }
      {
        match = { app-id = "Minecraft"; };
        open-on-workspace = "󰊗";
        open-fullscreen = true;
      }
      {
        match = { app-id = "^firefox$"; title = "^Picture-in-Picture$"; };
        open-floating = true;
      }
      {
        match = { app-id = "^zen$"; title = "^Picture-in-Picture$"; };
        open-floating = true;
      }
      {
        match = { app-id = "^brave$"; title = "^Picture-in-Picture$"; };
        open-floating = true;
      }
      {
        match = { app-id = "steam"; title = "^notificationtoasts_\d+_desktop$"; };
        default-floating-position = { x = 10; y = 10; relative-to = "bottom-right"; };
      }
      {
        match = { title = "Friends List"; };
        open-on-workspace = "󰊗";
        open-floating = true;
      }
      {
        match = { app-id = "^org\\.gnome\\.Nautilus$"; };
        exclude = {
          app-id = "^xdg-desktop-portal(-gtk)?$";
          title = "(?i)^(Open|Open File|Save As|Save File|Enregistrer|Enregistrer Sous|Ouvrir|Choisir un Fichier)$";
        };
        open-on-workspace = "󰊗";
        open-maximized = true;
      }
      {
        match = { app-id = "org.gnome.TextEditor"; };
        open-on-workspace = "󰊗";
      }
      {
        match = { app-id = "Spotify"; };
        open-on-workspace = "󰊗";
        open-maximized = true;
      }
      {
        match = { app-id = "com.kde.easyeffects"; };
        open-on-workspace = "󰊗";
      }
      {
        match = { app-id = "com.github.wwmm.easyeffects"; };
        open-on-workspace = "󰊗";
      }
    ];
    layer-rule = [
      {
        match = { namespace = "^noctalia-wallpaper*"; };
        place-within-backdrop = true;
      }
      {
        match = { namespace = "^noctalia-(bar-[^\"]+|notification|dock|panel|attached-panel|osd)$"; };
        background-effect = { xray = false; };
      }
      {
        match = { namespace = "noctalia-window-switcher"; };
        background-effect = { blur = true; xray = false; };
      }
    ];
    workspace = {
      "󰈹" = { open-on-output = "Lenovo Group Limited Legion 27Q-10 UNA07260"; };
      "󰊗" = { open-on-output = "Lenovo Group Limited Legion 27Q-10 UNA07260"; };
    };
  }));
in
{
  config = lib.mkIf isUmbriel {
    # ── Pas de programs.umbriel (le module n'existe pas) ──────────────

    # ── Noctalia shell ──────────────────────────────────────────────────
    programs.noctalia = lib.mkIf (shellType == "noctalia") {
      enable = true;
      package = inputs.noctalia.packages.${pkgs.stdenv.hostPlatform.system}.default;
    };

    # ── Configuration Umbriel via xdg.configFile ────────────────────────
    xdg.configFile."umbriel/config.toml".source = umbrielConfig;

    # ── Packages ─────────────────────────────────────────────────────────
    home.packages = with pkgs; [
      inputs.umbriel.packages.${pkgs.stdenv.hostPlatform.system}.default
      inputs.xdg-desktop-portal-umbriel.packages.${pkgs.stdenv.hostPlatform.system}.default
      awww
      xwayland-satellite
      playerctl
      wl-clipboard
      pwvucontrol
      kdePackages.qtmultimedia
      mpvpaper
      gnome-text-editor
      gnome-disk-utility
      mission-center
      loupe
      clapper
      clapper-enhancers
      gpu-screen-recorder
      nwg-look
      adw-gtk3
      papirus-icon-theme
      papirus-folders
      qt6Packages.qt6ct
      libsForQt5.qt5ct
      gvfs
      cava
    ];
  };
}
