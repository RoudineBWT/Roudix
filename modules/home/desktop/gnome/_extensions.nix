{ pkgs, ... }:
let

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

in
{
  # Packages only. Every setting (which extensions are enabled, ArcMenu,
  # dash-to-panel, blur-my-shell...) lives in modules/system/desktop/gnome.nix
  # as dconf defaults, so users can change them without a rebuild reverting it.
  home.packages = defaultExtensions;
}
