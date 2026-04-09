{ pkgs, inputs, config, lib, osConfig, ... }:
{
  imports = [
    inputs.noctalia.homeModules.default
    ../modules/mangohud.nix
    ../modules/papirus-folders.nix
  ];

  config = lib.mkIf (osConfig.roudix.desktop.type == "hyprland") {

  # ── Noctalia-shell ───────────────────────────────────────────────────────
  programs.noctalia-shell = {
    enable = true;
    package = null;
  };

  # ── Config files ─────────────────────────────────────────────
  xdg.configFile."hypr" = {
    source = ../dotfiles/hyprland;
    recursive = true;
  };

  # ── Packages ─────────────────────────────────────────────────
  home.packages = with pkgs; [
    wl-clipboard
    pwvucontrol
    kdePackages.qtmultimedia
    mpvpaper

    # Apps
    nautilus
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



  # Flake packages
  inputs.noctalia.packages.${pkgs.stdenv.hostPlatform.system}.default
   ];
 };
}
