{ pkgs, inputs, config, lib, osConfig, dotfiles, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isUmbriel = shellType == "umbriel";

  terminalCmd = osConfig.roudix.terminal or "ghostty";
  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";
  browserDefault = osConfig.roudix.browser.default or null;
  browserCmd     = osConfig.roudix.browser.command or null;
  browserList    = osConfig.roudix.browser.commands or [ ];
  extraBrowsers  = lib.filter (b: b.name != browserDefault) browserList;
in
{
  config = lib.mkIf (osConfig.roudix.desktop.type == "umbriel") {

    # ── Umbriel ─────────────────────────────────────────────────────────────
    programs.umbriel = {
      enable = true;
      package = inputs.umbriel.packages.${pkgs.stdenv.hostPlatform.system}.default;
    };

    # ── Noctalia shell sur Umbriel (optionnel) ────────────────────────────
    programs.noctalia = lib.mkIf isUmbriel {
      enable = true;
      package = inputs.noctalia.packages.${pkgs.stdenv.hostPlatform.system}.default;
    };

    # ── Configuration Umbriel ──────────────────────────────────────────────
    xdg.configFile."umbriel" = {
      source    = "${dotfiles}/umbriel";
      recursive = true;
    };

    xdg.configFile."umbriel/config.toml" = {
      force = true;
      text = ''
        # Umbriel configuration TOML
        # Documentation: https://docs.noctalia.dev/umbriel/

        [general]
        screenshot-path = "~/Pictures/umbriel-screenshots/from %Y-%m-%d %H-%M-%S.png"
        prefer-no-csd = true

        [environment]
        LD_PRELOAD = ""
        MOZ_ENABLE_WAYLAND = "1"
        XDG_SESSION_TYPE = "wayland"
        XDG_CURRENT_DESKTOP = "umbriel"
        XDG_SESSION_DESKTOP = "umbriel"
        MOZ_DBUS_REMOTE = "1"
        GDK_BACKEND = "wayland"
        QT_AUTO_SCREEN_SCALE_FACTOR = "1"
        QT_WAYLAND_FORCE_DPI = "physical"
        EGL_PLATFORM = "wayland"
        CLUTTER_BACKEND = "wayland"
        TERM = "ghostty"
        TERMINAL = "ghostty"
        _JAVA_AWT_WM_NONREPARENTING = "1"
        ELECTRON_OZONE_PLATFORM_HINT = "auto"
        QT_QPA_PLATFORMTHEME = "qt6ct"
        QT_QPA_PLATFORMTHEME_QT6 = "qt6ct"
        GTK_IM_MODULE = "simple"

        [layout]
        gaps = 9
        center-focused-column = "never"
        background-color = "transparent"

        [[layout.preset-column-widths]]
        proportion = 0.33333

        [[layout.preset-column-widths]]
        proportion = 0.5

        [[layout.preset-column-widths]]
        proportion = 0.66667

        [animations.workspace-switch]
        spring-damping-ratio = 1.0
        spring-stiffness = 1000
        epsilon = 0.0001

        [animations.window-open]
        duration-ms = 200
        curve = "ease-out-quad"

        [animations.window-close]
        duration-ms = 200
        curve = "ease-out-cubic"

        [animations.horizontal-view-movement]
        spring-damping-ratio = 1.0
        spring-stiffness = 900
        epsilon = 0.0001

        [animations.window-movement]
        spring-damping-ratio = 1.0
        spring-stiffness = 800
        epsilon = 0.0001

        [animations.window-resize]
        spring-damping-ratio = 1.0
        spring-stiffness = 1000
        epsilon = 0.0001

        [animations.config-notification-open-close]
        spring-damping-ratio = 0.6
        spring-stiffness = 1200
        epsilon = 0.001

        [animations.screenshot-ui-open]
        duration-ms = 300
        curve = "ease-out-quad"

        [animations.overview-open-close]
        spring-damping-ratio = 1.0
        spring-stiffness = 900
        epsilon = 0.0001

        [input.keyboard]
        layout = "us"
        variant = "intl"
        numlock = true

        [input.touchpad]
        tap = true
        natural-scroll = true

        [input.mouse]
        accel-profile = "flat"

        focus-follows-mouse = true
        workspace-auto-back-and-forth = true

        [cursor]
        xcursor-theme = "Bibata-Modern-Ice"
        xcursor-size = 24
        hide-when-typing = true
        hide-after-inactive-ms = 1000

        [blur]
        passes = 2
        offset = 3.0
        noise = 0.03
        saturation = 1.0

        # ─── Outputs ──────────────────────────────────────────
        # Adapte avec tes écrans
        [output."HKC OVERSEAS LIMITED 24E4 0000000000001"]
        mode = "1920x1080@165.001"
        scale = 1
        transform = "normal"
        position = [0, 0]

        [output."Lenovo Group Limited Legion 27Q-10 UNA07260"]
        mode = "2560x1440@240.000"
        scale = 1
        transform = "normal"
        position = [1920, 0]
        variable-refresh-rate = { on-demand = true }

        # ─── Autostart ──────────────────────────────────────────
        [[autostart]]
        command = "noctalia"

        [[autostart]]
        command = "xwayland-satellite"

        [[autostart]]
        command = "swww-daemon"

        [[autostart]]
        command = "discord"

        [[autostart]]
        command = "openrgb"

        # ─── Keybinds ──────────────────────────────────────────
        # MOD = Super (touche Windows)

        [keybind."MOD+Return"]
        action = "spawn"
        command = "${terminalCmd}"
        hotkey-overlay-title = "Open Terminal: ${terminalCmd}"

        [keybind."MOD+E"]
        action = "spawn"
        command = "${fileManagerCmd}"
        hotkey-overlay-title = "File Manager: ${fileManagerCmd}"
      '' + lib.optionalString (browserCmd != null) ''
        [keybind."MOD+B"]
        action = "spawn"
        command = "${browserCmd}"
        hotkey-overlay-title = "Open Browser: ${browserCmd}"
      '' + lib.concatStrings (lib.imap1 (i: b: ''
        [keybind."MOD+Ctrl+Alt+${toString i}"]
        action = "spawn"
        command = "${b.command}"
        hotkey-overlay-title = "Open Browser: ${b.name}"
      '') extraBrowsers) + ''
        [keybind."MOD+D"]
        action = "spawn"
        command = "noctalia msg panel-toggle launcher"
        hotkey-overlay-title = "Open App Launcher: noctalia launcher"

        [keybind."MOD+Shift+B"]
        action = "spawn"
        command = "zen-twilight"
        hotkey-overlay-title = "Open Browser: Zen"

        [keybind."MOD+Alt+L"]
        action = "spawn"
        command = "noctalia msg screen-lock"
        hotkey-overlay-title = "Lock Screen: noctalia lock"

        [keybind."Mod+Shift+Q"]
        action = "spawn"
        command = "noctalia msg panel-toggle session"
        hotkey-overlay-title = "Power Menu"

        # ─── Audio ───
        [keybind."XF86AudioRaiseVolume"]
        action = "spawn"
        command = "noctalia msg volume-up"
        allow-when-locked = true

        [keybind."XF86AudioLowerVolume"]
        action = "spawn"
        command = "noctalia msg volume-down"
        allow-when-locked = true

        [keybind."XF86AudioMute"]
        action = "spawn"
        command = "noctalia msg volume-mute"
        allow-when-locked = true

        [keybind."XF86AudioMicMute"]
        action = "spawn"
        command = "noctalia msg mic-mute"
        allow-when-locked = true

        # ─── Media ───
        [keybind."XF86AudioPlay"]
        action = "spawn"
        command = "playerctl play-pause"
        allow-when-locked = true

        [keybind."XF86AudioPrev"]
        action = "spawn"
        command = "playerctl previous"
        allow-when-locked = true

        [keybind."XF86AudioNext"]
        action = "spawn"
        command = "playerctl next"
        allow-when-locked = true

        # ─── Window / Focus ───
        [keybind."MOD+Q"]
        action = "close-window"

        [keybind."MOD+Left"]
        action = "focus-column-left"

        [keybind."MOD+H"]
        action = "focus-column-left"

        [keybind."MOD+Right"]
        action = "focus-column-right"

        [keybind."MOD+L"]
        action = "focus-column-right"

        [keybind."MOD+Up"]
        action = "focus-window-up"

        [keybind."MOD+K"]
        action = "focus-window-up"

        [keybind."MOD+Down"]
        action = "focus-window-down"

        [keybind."MOD+J"]
        action = "focus-window-down"

        # ─── Move Windows ───
        [keybind."MOD+Ctrl+Left"]
        action = "move-column-left"

        [keybind."MOD+Ctrl+H"]
        action = "move-column-left"

        [keybind."MOD+Ctrl+Right"]
        action = "move-column-right"

        [keybind."MOD+Ctrl+L"]
        action = "move-column-right"

        [keybind."MOD+Ctrl+Up"]
        action = "move-window-up"

        [keybind."MOD+Ctrl+K"]
        action = "move-window-up"

        [keybind."MOD+Ctrl+Down"]
        action = "move-window-down"

        [keybind."MOD+Ctrl+J"]
        action = "move-window-down"

        # ─── Workspace Navigation ───
        [keybind."MOD+WheelScrollDown"]
        action = "focus-workspace-down"
        cooldown-ms = 150

        [keybind."MOD+WheelScrollUp"]
        action = "focus-workspace-up"
        cooldown-ms = 150

        [keybind."MOD+Ctrl+WheelScrollDown"]
        action = "move-column-to-workspace-down"
        cooldown-ms = 150

        [keybind."MOD+Ctrl+WheelScrollUp"]
        action = "move-column-to-workspace-up"
        cooldown-ms = 150

        # ─── Workspace Quick Switch ───
        [keybind."MOD+1"]
        action = "focus-workspace 1"

        [keybind."MOD+2"]
        action = "focus-workspace 2"

        [keybind."MOD+3"]
        action = "focus-workspace 3"

        [keybind."MOD+4"]
        action = "focus-workspace 4"

        [keybind."MOD+5"]
        action = "focus-workspace 5"

        [keybind."MOD+6"]
        action = "focus-workspace 6"

        [keybind."MOD+7"]
        action = "focus-workspace 7"

        [keybind."MOD+8"]
        action = "focus-workspace 8"

        [keybind."MOD+9"]
        action = "focus-workspace 9"

        [keybind."MOD+Ctrl+1"]
        action = "move-column-to-workspace 1"

        [keybind."MOD+Ctrl+2"]
        action = "move-column-to-workspace 2"

        [keybind."MOD+Ctrl+3"]
        action = "move-column-to-workspace 3"

        [keybind."MOD+Ctrl+4"]
        action = "move-column-to-workspace 4"

        [keybind."MOD+Ctrl+5"]
        action = "move-column-to-workspace 5"

        [keybind."MOD+Ctrl+6"]
        action = "move-column-to-workspace 6"

        [keybind."MOD+Ctrl+7"]
        action = "move-column-to-workspace 7"

        [keybind."MOD+Ctrl+8"]
        action = "move-column-to-workspace 8"

        [keybind."MOD+Ctrl+9"]
        action = "move-column-to-workspace 9"

        [keybind."MOD+Tab"]
        action = "focus-workspace-previous"

        [keybind."Alt+Tab"]
        action = "spawn"
        command = "noctalia msg window-switcher"

        # ─── Layout ───
        [keybind."MOD+Ctrl+F"]
        action = "expand-column-to-available-width"

        [keybind."MOD+C"]
        action = "center-column"

        [keybind."MOD+Ctrl+C"]
        action = "center-visible-columns"

        [keybind."MOD+-"]
        action = "set-column-width -10%"

        [keybind."MOD+="]
        action = "set-column-width +10%"

        [keybind."MOD+Shift+-"]
        action = "set-window-height -10%"

        [keybind."MOD+Shift+="]
        action = "set-window-height +10%"

        # ─── Modes ───
        [keybind."MOD+T"]
        action = "toggle-window-floating"

        [keybind."MOD+F"]
        action = "fullscreen-window"

        [keybind."MOD+W"]
        action = "toggle-column-tabbed-display"

        # ─── Screenshots ───
        [keybind."Ctrl+Shift+1"]
        action = "screenshot"

        [keybind."Ctrl+Shift+2"]
        action = "screenshot-screen"

        [keybind."Ctrl+Shift+3"]
        action = "screenshot-window"

        # ─── Emergency ───
        [keybind."MOD+Escape"]
        action = "toggle-keyboard-shortcuts-inhibit"
        allow-inhibiting = false

        # ─── Exit / Power ───
        [keybind."Ctrl+Alt+Delete"]
        action = "quit"

        [keybind."MOD+Shift+R"]
        action = "spawn"
        command = "noctalia msg config-reload"

        [keybind."MOD+Shift+P"]
        action = "power-off-monitors"

        [keybind."MOD+O"]
        action = "toggle-overview"
        repeat = false

        # ─── Window Rules ──────────────────────────────────────
        # Rayon de coin arrondi pour toutes les fenêtres
        geometry-corner-radius = 20
        clip-to-geometry = true

        [[window-rule]]
        match.app-id = "discord"
        open-on-workspace = "󰊗"
        default-column-width = { fixed = 1316 }
        default-window-height = { fixed = 1011 }
        default-floating-position = { x = 0, y = 0, relative-to = "top-left" }

        [[window-rule]]
        match.app-id = "Element"
        open-on-workspace = "󰊗"
        default-column-width = { fixed = 1316 }
        default-window-height = { fixed = 1011 }
        default-floating-position = { x = 0, y = 0, relative-to = "top-left" }

        [[window-rule]]
        match.app-id = "com.mitchellh.ghostty"
        open-floating = true
        background-effect = { blur = true, xray = false }

        [[window-rule]]
        match.app-id = "org.telegram.desktop"
        open-on-workspace = "󰊗"
        default-column-width = { fixed = 555 }
        default-window-height = { fixed = 1011 }
        default-floating-position = { x = 0, y = 0, relative-to = "top-right" }

        [[window-rule]]
        match.app-id = "firefox"
        open-on-workspace = "󰈹"
        open-maximized = true

        [[window-rule]]
        match.title = "About Mozilla Firefox"
        open-on-workspace = "󰈹"
        open-floating = true

        [[window-rule]]
        match.app-id = "dev.zed.Zed"
        open-on-workspace = "󰊗"
        open-maximized = true

        [[window-rule]]
        match.app-id = "zen-twilight"
        open-on-workspace = "󰈹"
        open-maximized = true
        draw-border-with-background = false
        opacity = 0.95
        background-effect = { blur = true, xray = false }

        [[window-rule]]
        match.title = "About Zen Twilight"
        open-on-workspace = "󰈹"
        open-floating = true
        draw-border-with-background = false
        opacity = 0.95
        background-effect = { blur = true, xray = false }

        [[window-rule]]
        match.app-id = "brave-origin-beta"
        open-on-workspace = "󰈹"
        open-maximized = true

        [[window-rule]]
        match.app-id = '^org.gnome.Nautilus$'
        match.title = '^Save As$'
        open-focused = true

        [[window-rule]]
        match.app-id = "com.mitchellh.ghostty"
        default-column-width = { fixed = 1505 }
        default-window-height = { fixed = 755 }
        open-floating = true

        [[window-rule]]
        match.app-id = "steam"
        open-on-workspace = "󰊗"
        open-maximized = true

        [[window-rule]]
        match.app-id = "openrgb"
        open-on-workspace = "󰊗"

        [[window-rule]]
        match.app-id = "kitty"
        open-on-workspace = "󰊗"
        open-floating = true

        [[window-rule]]
        match.app-id = "org.gnome.Ptyxis"
        open-on-workspace = "󰊗"

        [[window-rule]]
        match.app-id = "brave-browser"
        open-on-workspace = "󰊗"
        open-maximized = true

        [[window-rule]]
        match.app-id = "^(steam_app_.*)$"
        open-on-workspace = "󰊗"
        open-fullscreen = true

        [[window-rule]]
        match.app-id = "^heroic$"
        open-on-workspace = "󰊗"
        open-fullscreen = true

        [[window-rule]]
        match.app-id = "org.prismlauncher.PrismLauncher"
        open-on-workspace = "󰊗"
        open-maximized = true

        [[window-rule]]
        match.app-id = "Minecraft"
        open-on-workspace = "󰊗"
        open-fullscreen = true

        [[window-rule]]
        match.app-id = "^firefox$"
        match.title = "^Picture-in-Picture$"
        open-floating = true

        [[window-rule]]
        match.app-id = "^zen$"
        match.title = "^Picture-in-Picture$"
        open-floating = true

        [[window-rule]]
        match.app-id = "^brave$"
        match.title = "^Picture-in-Picture$"
        open-floating = true

        [[window-rule]]
        match.app-id = "steam"
        match.title = '^notificationtoasts_\d+_desktop$'
        default-floating-position = { x = 10, y = 10, relative-to = "bottom-right" }

        [[window-rule]]
        match.title = "Friends List"
        open-on-workspace = "󰊗"
        open-floating = true

        [[window-rule]]
        match.app-id = '^org\.gnome\.Nautilus$'
        exclude.app-id = '^xdg-desktop-portal(-gtk)?$'
        exclude.title = '(?i)^(Open|Open File|Save As|Save File|Enregistrer|Enregistrer Sous|Ouvrir|Choisir un Fichier)$'
        open-on-workspace = "󰊗"
        open-maximized = true

        [[window-rule]]
        match.app-id = "org.gnome.TextEditor"
        open-on-workspace = "󰊗"

        [[window-rule]]
        match.app-id = "Spotify"
        open-on-workspace = "󰊗"
        open-maximized = true

        [[window-rule]]
        match.app-id = "com.kde.easyeffects"
        open-on-workspace = "󰊗"

        [[window-rule]]
        match.app-id = "com.github.wwmm.easyeffects"
        open-on-workspace = "󰊗"

        # ─── Layer Rules ────────────────────────────────────────
        [[layer-rule]]
        match.namespace = "^noctalia-wallpaper*"
        place-within-backdrop = true

        [[layer-rule]]
        match.namespace = '^noctalia-(bar-[^\"]+|notification|dock|panel|attached-panel|osd)$'
        background-effect = { xray = false }

        [[layer-rule]]
        match.namespace = "noctalia-window-switcher"
        background-effect = { blur = true, xray = false }

        # ─── Workspace named ────────────────────────────────────
        [workspace."󰈹"]
        open-on-output = "Lenovo Group Limited Legion 27Q-10 UNA07260"

        [workspace."󰊗"]
        open-on-output = "Lenovo Group Limited Legion 27Q-10 UNA07260"

        [workspace."󰊗"]
        open-on-output = "HKC OVERSEAS LIMITED 24E4 0000000000001"

        [workspace."󰊗"]
        open-on-output = "Lenovo Group Limited Legion 27Q-10 UNA07260"

        [workspace."󰊗"]
        open-on-output = "Lenovo Group Limited Legion 27Q-10 UNA07260"

        [workspace."󰊗"]
        open-on-output = "Lenovo Group Limited Legion 27Q-10 UNA07260"

        [workspace."󰊗"]
        open-on-output = "HKC OVERSEAS LIMITED 24E4 0000000000001"

        [workspace."󰊗"]
        open-on-output = "HKC OVERSEAS LIMITED 24E4 0000000000001"
      '';
    };

    # ── Packages ─────────────────────────────────────────────────────────────
    home.packages = with pkgs; [
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
