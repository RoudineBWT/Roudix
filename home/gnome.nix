{ osConfig, lib, pkgs, inputs, username, ... }:
let
  isGnome = osConfig.roudix.desktop.type == "gnome";
  cfg     = osConfig.roudix.gnome;

  # ── Default extensions ─────────────────────────────────────────────────
  defaultExtensions = with pkgs.gnomeExtensions; [
    caffeine
    gsconnect
    appindicator
    dash-to-dock
    bing-wallpaper-changer
    quick-settings-audio-panel
    blur-my-shell
    burn-my-windows
    tiling-shell
    vitals
    rounded-window-corners-reborn
    dash-to-panel
    open-bar
    arcmenu
    bluetooth-battery-meter
  ];

  # UUIDs of default extensions (for dconf enabled-extensions)
  defaultUUIDs = [
    "caffeine@patapon.info"
    "gsconnect@andyholmes.github.io"
    "appindicatorsupport@rgcjonas.gmail.com"
    "dash-to-dock@micxgx.gmail.com"
    "BingWallpaper@ineffable-gmail.com"
    "quick-settings-audio-panel@rayzeq.github.io"
    "blur-my-shell@aunetx"
    "burn-my-windows@schneegans.github.com"
    "tiling-shell@ferrarodomenico.com"
    "Vitals@CoreCoding.com"
    "rounded-window-corners@fxgn"
    "dash-to-panel@jderose9.github.com"
    "open-bar@neuromorph"
    "arcmenu@arcmenu.com"
    "bluetooth-battery-meter@maniacx.github.com"
  ];

  # Active UUIDs = defaults - disabled + extras
  activeUUIDs =
    (lib.filter (u: !builtins.elem u cfg.disabledExtensions) defaultUUIDs)
    ++ (map (e: e.extensionUuid or "") cfg.extraExtensions);
in
{
  imports = [
    ../modules/home/mangohud.nix
    ../modules/home/papirus-folders.nix
  ];

  config = lib.mkIf isGnome {
    home.packages = with pkgs; [
      papirus-icon-theme
      capitaine-cursors
    ] ++ defaultExtensions;

    home.pointerCursor = {
      name    = "capitaine-cursors-white";
      package = pkgs.capitaine-cursors;
      size    = 24;
      gtk.enable = true;
    };

    dconf.settings = {
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
        cursor-size  = 24;
      };
      "org/gnome/shell" = {
        enabled-extensions = activeUUIDs;
      };
      # ── ArcMenu ─────────────────────────────────────────────────────
      "org/gnome/shell/extensions/arcmenu" = {
        menu-button-icon        = "Custom_Icon";
        custom-menu-button-icon = "/run/current-system/sw/share/icons/hicolor/scalable/apps/roudix-logo.svg";
      };
    };
  };
}
