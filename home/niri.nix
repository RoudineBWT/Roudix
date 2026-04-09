{ pkgs, inputs, config, lib, osConfig, dotfiles, ... }:
{
imports = [
  inputs.noctalia.homeModules.default
  ../modules/home/mangohud.nix
  ../modules/home/papirus-folders.nix
];

config = lib.mkIf (osConfig.roudix.desktop.type == "niri") {


  # ── Noctalia-shell ───────────────────────────────────────────────────────
  programs.noctalia-shell = {
    enable = true;
    package = null;
  };

  # ── Niri config ──────────────────────────────────────────────────────────
  xdg.configFile."niri" = {
    source = "${dotfiles}/niri";
    recursive = true;
  };

  # ── Packages ─────────────────────────────────────────────────────────────
  home.packages = with pkgs; [
    # Niri / Wayland tools
    awww
    xwayland-satellite
    playerctl
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
