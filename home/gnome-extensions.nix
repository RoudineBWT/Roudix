{ osConfig, lib, pkgs, ... }:
let
  cfg = osConfig.roudix.gnome;

  # ── Default extensions (packages) ─────────────────────────────────────
  defaultExtensions = with pkgs.gnomeExtensions; [
    appindicator
    arcmenu
    bing-wallpaper-changer
    bluetooth-battery-meter
    blur-my-shell
    burn-my-windows
    caffeine
    dash-to-dock
    dash-to-panel
    gsconnect
    open-bar
    quick-settings-audio-panel
    rounded-window-corners-reborn
    tiling-shell
    vitals
  ];

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
in
{
  home.packages = defaultExtensions;

  dconf.settings = {
    "org/gnome/shell" = {
      enabled-extensions = activeUUIDs;
    };

    # ── ArcMenu ───────────────────────────────────────────────────────────
    "org/gnome/shell/extensions/arcmenu" = {
      custom-menu-button-icon = "/run/current-system/sw/share/icons/hicolor/scalable/apps/roudix-logo.svg";
      custom-menu-button-text = "Roudix";
      dash-to-panel-standalone = false;
      menu-button-appearance = "Icon_Text";
      menu-button-icon = "Custom_Icon";
      menu-layout = "GnomeOverview";
      multi-monitor = true;
      search-entry-border-radius = lib.hm.gvariant.mkTuple [ true 25 ];
      show-activities-button = false;
    };

    # ── Blur My Shell ─────────────────────────────────────────────────────
    "org/gnome/shell/extensions/blur-my-shell" = {
      settings-version = 2;
    };
    "org/gnome/shell/extensions/blur-my-shell/appfolder" = {
      brightness = 0.6;
      sigma = 30;
    };
    "org/gnome/shell/extensions/blur-my-shell/dash-to-dock" = {
      blur = true;
      brightness = 0.6;
      sigma = 30;
      static-blur = true;
      style-dash-to-dock = 0;
    };
    "org/gnome/shell/extensions/blur-my-shell/panel" = {
      brightness = 0.6;
      sigma = 30;
    };
    "org/gnome/shell/extensions/blur-my-shell/window-list" = {
      brightness = 0.6;
      sigma = 30;
    };

    # ── Caffeine ──────────────────────────────────────────────────────────
    "org/gnome/shell/extensions/caffeine" = {
      cli-toggle = false;
      indicator-position-max = 1;
    };

    # ── Dash to Dock ──────────────────────────────────────────────────────
    "org/gnome/shell/extensions/dash-to-dock" = {
      background-opacity = 0.8;
      dash-max-icon-size = 48;
      dock-position = "BOTTOM";
      height-fraction = 0.9;
      preferred-monitor = -2;
      scroll-to-focused-application = true;
      show-mounts = false;
      show-trash = false;
    };

    # ── Dash to Panel ─────────────────────────────────────────────────────
    "org/gnome/shell/extensions/dash-to-panel" = {
      appicon-margin = 4;
      dot-position = "BOTTOM";
      hotkeys-overlay-combo = "TEMPORARILY";
      panel-anchors = ''{"RHT-0x00000000":"MIDDLE"}'';
      panel-element-positions = ''{"RHT-0x00000000":[{"element":"showAppsButton","visible":false,"position":"stackedTL"},{"element":"activitiesButton","visible":false,"position":"stackedTL"},{"element":"leftBox","visible":true,"position":"stackedTL"},{"element":"taskbar","visible":false,"position":"stackedTL"},{"element":"centerBox","visible":true,"position":"centerMonitor"},{"element":"dateMenu","visible":true,"position":"centerMonitor"},{"element":"rightBox","visible":true,"position":"stackedBR"},{"element":"systemMenu","visible":true,"position":"stackedBR"},{"element":"desktopButton","visible":true,"position":"stackedBR"}]}'';
      panel-positions = ''{"RHT-0x00000000":"TOP"}'';
      panel-sizes = ''{"RHT-0x00000000":32}'';
      stockgs-keep-dash = true;
      window-preview-title-position = "TOP";
    };

    # ── Quick Settings Audio Panel ────────────────────────────────────────
    "org/gnome/shell/extensions/quick-settings-audio-panel" = {
      version = 2;
    };

    # ── Rounded Window Corners Reborn ─────────────────────────────────────
    "org/gnome/shell/extensions/rounded-window-corners-reborn" = {
      settings-version = lib.hm.gvariant.mkUint32 7;
    };
  };
}
