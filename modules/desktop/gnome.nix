{ config, lib, pkgs, inputs, ... }:
let
  isGnome = config.roudix.desktop.type == "gnome";
in
lib.mkIf isGnome {
  services.desktopManager.gnome.enable = true;

  nixpkgs.overlays = [
    (final: prev: {
      gnome = inputs.nixpkgsStaging.legacyPackages.${prev.system}.gnome;
    })
  ];

  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [
      xdg-desktop-portal-gnome
      xdg-desktop-portal-gtk
    ];
    config.common.default = "*";
  };

  environment.systemPackages = with pkgs; [
    gnome-tweaks
  ];

  environment.gnome.excludePackages = with pkgs; [
    tali iagno hitori atomix yelp geary xterm totem
    epiphany gnome-tour gnome-software gnome-contacts
    gnome-user-docs gnome-font-viewer gnome-music
  ];
}
