{ config, lib, pkgs, inputs, ... }:
let
  isGnome = config.roudix.desktop.type == "gnome";
in
lib.mkIf isGnome {
  # ── Greeter & keyring ───────────────────────────────────────────────────
  services.displayManager.gdm.enable = true;
  services.gnome.gnome-keyring.enable = true;
  security.pam.services.gdm.enableGnomeKeyring = true;
  security.polkit.enable = true;

  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [
      xdg-desktop-portal-gnome
      xdg-desktop-portal-gtk
    ];
    config.common.default = "*";
  };

  programs.nautilus-open-any-terminal = {
    enable = true;
    terminal = "ghostty";
  };

  environment.systemPackages = with pkgs; [
    gnome-tweaks
    gnome-extension-manager
    gtk3
    gsettings-desktop-schemas
    adw-gtk3
    gnomeExtensions.caffeine
           gnomeExtensions.gsconnect
           gnomeExtensions.appindicator
           gnomeExtensions.dash-to-dock
           gnomeExtensions.bing-wallpaper-changer
           gnomeExtensions.quick-settings-audio-panel
           gnomeExtensions.blur-my-shell
           gnomeExtensions.burn-my-windows
           gnomeExtensions.tiling-shell
           gnomeExtensions.vitals
           gnomeExtensions.rounded-window-corners-reborn
           gnomeExtensions.dash-to-panel
           gnomeExtensions.open-bar
           gnomeExtensions.arcmenu
           gnomeExtensions.bluetooth-battery-meter

  ];

  environment.gnome.excludePackages = with pkgs; [
    tali iagno hitori atomix yelp geary xterm totem
    epiphany gnome-tour gnome-software gnome-contacts
    gnome-user-docs gnome-font-viewer gnome-music
  ];
}
