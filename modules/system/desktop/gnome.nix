{ config, lib, pkgs, inputs, roudixBranding, ... }:
let
  isGnome = config.roudix.desktop.type == "gnome";
  cfg = config.roudix.gnome;

  # ── Default enabled UUIDs ──────────────────────────────────────────────
  defaultEnabledUUIDs = [
    "appindicatorsupport@rgcjonas.gmail.com"
    "arcmenu@arcmenu.com"
    "caffeine@patapon.info"
    "dash-to-dock@micxgx.gmail.com"
    "dash-to-panel@jderose9.github.com"
    "gsconnect@andyholmes.github.io"
    "quick-settings-audio-panel@rayzeq.github.io"
    "rounded-window-corners@fxgn"
    "Vitals@CoreCoding.com"
  ];

  # Active UUIDs = defaults - disabled + extras
  activeUUIDs =
    (lib.filter (u: !builtins.elem u cfg.disabledExtensions) defaultEnabledUUIDs)
    ++ (map (e: e.extensionUuid or "") cfg.extraExtensions);

  # ── Dock favorites ─────────────────────────────────────────────────────
  # Desktop-file ids per installed browser / terminal. GNOME silently
  # ignores ids that don't exist, so a wrong guess just means "not pinned".
  browserDesktopIds = {
    "brave"                = [ "brave-browser.desktop" ];
    "brave-beta"           = [ "brave-browser-beta.desktop" ];
    "brave-nightly"        = [ "brave-browser-nightly.desktop" ];
    "brave-origin"         = [ "brave-origin.desktop" ];
    "brave-origin-beta"    = [ "brave-origin-beta.desktop" ];
    "brave-origin-nightly" = [ "brave-origin-nightly.desktop" ];
    "helium"               = [ "helium.desktop" "helium-browser.desktop" ];
    "vivaldi"              = [ "vivaldi-stable.desktop" ];
    "chromium"             = [ "chromium-browser.desktop" ];
    "ungoogled-chromium"   = [ "chromium-browser.desktop" ];
    "firefox"              = [ "firefox.desktop" ];
    "librewolf"            = [ "librewolf.desktop" ];
    "google-chrome"        = [ "google-chrome.desktop" ];
    "microsoft-edge"       = [ "microsoft-edge.desktop" ];
  };
  zenDesktopIds =
    if config.roudix.zen.variant == "beta"
    then [ "zen-beta.desktop" "zen.desktop" ]
    else [ "zen-twilight.desktop" "zen.desktop" ];
  terminalDesktopIds = {
    ghostty   = [ "com.mitchellh.ghostty.desktop" ];
    kitty     = [ "kitty.desktop" ];
    alacritty = [ "Alacritty.desktop" ];
    foot      = [ "foot.desktop" ];
    wezterm   = [ "org.wezfurlong.wezterm.desktop" ];
    ptyxis    = [ "org.gnome.Ptyxis.desktop" ];
    konsole   = [ "org.kde.konsole.desktop" ];
  };

  favoriteApps =
    [ "org.gnome.Nautilus.desktop" ]
    ++ lib.concatMap (b: browserDesktopIds.${b} or [ ]) config.roudix.browsers
    ++ lib.optionals config.roudix.zen.enable zenDesktopIds
    ++ terminalDesktopIds.${config.roudix.terminal} or [ ]
    ++ [
      "io.roudix.store.desktop"
      "org.gnome.Settings.desktop"
    ];

  # ── Roudix look & feel, as dconf DEFAULTS ─────────────────────────────
  # Written to the *system* dconf database (/etc/dconf/db/user.d), NOT to
  # the user's own database. dconf reads the user db first and falls back
  # to the system db only for keys the user never touched, so:
  #   - first login: the user gets exactly this look,
  #   - user changes a setting (Settings, Tweaks, extension prefs...): it
  #     goes to their own db and wins forever — a rebuild never touches it,
  #   - we change a default in a later Roudix update: only users who never
  #     changed that key pick it up.
  # (home-manager's `dconf.settings` is the opposite: it re-runs
  # `dconf load` on every switch and overwrites the user's choices.)
  gnomeDefaults = {
    "org/gnome/shell" = {
      always-show-log-out = true;
      enabled-extensions = activeUUIDs;
      # Pinned apps (Dash to Dock / Dash to Panel / overview): Files, the
      # browser(s) and terminal the user selected in Roudix, the Store and
      # Settings. A default like the rest: once the user pins/unpins
      # anything, their own list wins.
      favorite-apps = favoriteApps;
    };

    "org/gnome/desktop/background" = {
      picture-uri      = "file:///run/current-system/sw/share/backgrounds/roudix/roudix-light.png";
      picture-uri-dark = "file:///run/current-system/sw/share/backgrounds/roudix/roudix-dark.png";
      picture-options  = "zoom";
    };
    "org/gnome/desktop/screensaver" = {
      picture-uri = "file:///run/current-system/sw/share/backgrounds/roudix/roudix-dark.png";
    };
    "org/gnome/desktop/interface" = {
      color-scheme = "prefer-dark";
      icon-theme   = "Papirus-Dark";
      gtk-theme    = "adw-gtk3-dark";
      cursor-theme = "capitaine-cursors-white";
      cursor-size  = lib.gvariant.mkInt32 (24);
      gtk-enable-primary-paste = true;
    };

    # ── "Roudix" app folder ───────────────────────────────────────────────
    # Every Roudix app (Store, Customizer, Kernel Switcher, Scheduler,
    # Welcome) carries Categories=...;X-Roudix; in its .desktop file, and the
    # folder collects them by that category. folder-children replaces the
    # stock list, so GNOME's own default folders are repeated here.
    "org/gnome/desktop/app-folders" = {
      folder-children = [ "Utilities" "YaST" "Pardus" "Roudix" ];
    };
    "org/gnome/desktop/app-folders/folders/Roudix" = {
      name = "Roudix";
      translate = false;
      categories = [ "X-Roudix" ];
    };

    # ── ArcMenu ───────────────────────────────────────────────────────────
    "org/gnome/shell/extensions/arcmenu" = {
      custom-menu-button-icon = "/run/current-system/sw/share/icons/hicolor/scalable/apps/roudix-logo.svg";
      custom-menu-button-text = "Roudix";
      dash-to-panel-standalone = false;
      menu-button-appearance = "Icon_Text";
      menu-button-icon = "roudix-logo";
      menu-button-text = "Roudix";
      menu-layout = "gnome-overview";
      multi-monitor = true;
      search-entry-border-radius = lib.gvariant.mkTuple [ true (lib.gvariant.mkInt32 25) ];
      show-activities-button = false;
    };

    # ── Blur My Shell ─────────────────────────────────────────────────────
    "org/gnome/shell/extensions/blur-my-shell" = {
      settings-version = lib.gvariant.mkInt32 (2);
    };
    "org/gnome/shell/extensions/blur-my-shell/appfolder" = {
      brightness = 0.6;
      sigma = lib.gvariant.mkInt32 (30);
    };
    "org/gnome/shell/extensions/blur-my-shell/dash-to-dock" = {
      blur = true;
      brightness = 0.6;
      sigma = lib.gvariant.mkInt32 (30);
      static-blur = true;
      style-dash-to-dock = lib.gvariant.mkInt32 (0);
    };
    "org/gnome/shell/extensions/blur-my-shell/panel" = {
      brightness = 0.6;
      sigma = lib.gvariant.mkInt32 (30);
    };
    "org/gnome/shell/extensions/blur-my-shell/window-list" = {
      brightness = 0.6;
      sigma = lib.gvariant.mkInt32 (30);
    };

    # ── Caffeine ──────────────────────────────────────────────────────────
    "org/gnome/shell/extensions/caffeine" = {
      cli-toggle = false;
      indicator-position-max = lib.gvariant.mkInt32 (1);
    };

    # ── Dash to Dock ──────────────────────────────────────────────────────
    "org/gnome/shell/extensions/dash-to-dock" = {
      background-opacity = 0.8;
      dash-max-icon-size = lib.gvariant.mkInt32 (48);
      dock-position = "BOTTOM";
      height-fraction = 0.9;
      preferred-monitor = lib.gvariant.mkInt32 (-2);
      scroll-to-focused-application = true;
      show-mounts = false;
      show-trash = false;
    };

    # ── Dash to Panel ─────────────────────────────────────────────────────
    "org/gnome/shell/extensions/dash-to-panel" = {
      appicon-margin = lib.gvariant.mkInt32 (4);
      dot-position = "BOTTOM";
      hotkeys-overlay-combo = "TEMPORARILY";
      # "RHT-0x00000000" = the physical screen ID these settings were
      # tuned on by hand. dash-to-panel indexes EVERYTHING per screen,
      # with no generic "all screens" key — panel-element-positions-
      # monitors-sync exists on the "element order" side but has a known
      # bug (upstream #1173) and covers neither position, size, nor
      # anchors anyway. Workaround: also duplicate under key "0" — a
      # screen with no usable EDID (VM, most virtual display drivers)
      # generally falls back to an indexed ID rather than the real
      # hardware ID. Not 100% guaranteed on every config, but covers the
      # VM case without breaking anything on real hardware.
      panel-element-positions-monitors-sync = true;
      panel-anchors = ''{"RHT-0x00000000":"MIDDLE","0":"MIDDLE"}'';
      panel-element-positions = ''{"RHT-0x00000000":[{"element":"showAppsButton","visible":false,"position":"stackedTL"},{"element":"activitiesButton","visible":false,"position":"stackedTL"},{"element":"leftBox","visible":true,"position":"stackedTL"},{"element":"taskbar","visible":false,"position":"stackedTL"},{"element":"centerBox","visible":true,"position":"centerMonitor"},{"element":"dateMenu","visible":true,"position":"centerMonitor"},{"element":"rightBox","visible":true,"position":"stackedBR"},{"element":"systemMenu","visible":true,"position":"stackedBR"},{"element":"desktopButton","visible":true,"position":"stackedBR"}],"0":[{"element":"showAppsButton","visible":false,"position":"stackedTL"},{"element":"activitiesButton","visible":false,"position":"stackedTL"},{"element":"leftBox","visible":true,"position":"stackedTL"},{"element":"taskbar","visible":false,"position":"stackedTL"},{"element":"centerBox","visible":true,"position":"centerMonitor"},{"element":"dateMenu","visible":true,"position":"centerMonitor"},{"element":"rightBox","visible":true,"position":"stackedBR"},{"element":"systemMenu","visible":true,"position":"stackedBR"},{"element":"desktopButton","visible":true,"position":"stackedBR"}]}'';
      panel-positions = ''{"RHT-0x00000000":"TOP","0":"TOP"}'';
      panel-sizes = ''{"RHT-0x00000000":32,"0":32}'';
      stockgs-keep-dash = true;
      window-preview-title-position = "TOP";
    };

    # ── Quick Settings Audio Panel ────────────────────────────────────────
    "org/gnome/shell/extensions/quick-settings-audio-panel" = {
      version = lib.gvariant.mkInt32 (2);
    };

    # ── Rounded Window Corners Reborn ─────────────────────────────────────
    "org/gnome/shell/extensions/rounded-window-corners-reborn" = {
      settings-version = lib.gvariant.mkUint32 7;
    };
  };
in
{
  # ── User-facing options ────────────────────────────────────────────────
  options.roudix.gnome = {
    extraExtensions = lib.mkOption {
      type    = lib.types.listOf lib.types.package;
      default = [];
      description = "Additional GNOME extensions to install and enable.";
    };
    disabledExtensions = lib.mkOption {
      type    = lib.types.listOf lib.types.str;
      default = [];
      description = "UUIDs of default extensions to disable.";
    };
  };

  config = lib.mkIf isGnome {
    # ── Greeter & keyring ──────────────────────────────────────────────
    services.displayManager.gdm.enable = true;
    services.gnome.gnome-keyring.enable = true;
    security.pam.services.gdm.enableGnomeKeyring = true;
    services.desktopManager.gnome.enable = true;

    # See `gnomeDefaults` above: Roudix look & feel + "Log Out" always
    # visible (GNOME hides it on single-user/single-session installs; Ubuntu
    # has forced it on since 2017). All of it is a default, not a lock —
    # the user can change any of it and a rebuild will never revert it.
    programs.dconf.enable = true;
    programs.dconf.profiles.user.databases = [
      { settings = gnomeDefaults; }
    ];

    xdg.portal = {
      enable = true;
      extraPortals = with pkgs; [
        xdg-desktop-portal-gnome
        xdg-desktop-portal-gtk
      ];
      config.common.default = "gnome";
    };

    programs.nautilus-open-any-terminal = {
      enable = true;
      terminal = "ghostty";
    };

    environment.systemPackages = with pkgs; [
      (lib.hiPrio roudixBranding)
      gnome-tweaks
      gnome-extension-manager
      gtk3
      gsettings-desktop-schemas
      adw-gtk3
      papirus-icon-theme
      capitaine-cursors
    ] ++ cfg.extraExtensions;

    environment.gnome.excludePackages = with pkgs; [
      tali
       iagno
       hitori
       atomix
       yelp
       geary
       xterm
       totem

       epiphany
       packagekit

       gnome-tour
       gnome-software
       gnome-contacts
       gnome-user-docs
       gnome-packagekit
       gnome-font-viewer
       gnome-music

    ];
  };
}
