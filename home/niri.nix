{ pkgs, inputs, username, ... }:
{
  home.username = username;
  home.homeDirectory = "/home/${username}";
  home.stateVersion = "25.11";

  imports = [
    ./common.nix
    inputs.noctalia.homeModules.default
    ../modules/fastfetch.nix
    ../modules/mangohud.nix
    ../modules/fish.nix
    ../modules/bash.nix
    ../modules/gaming-home.nix
    ../modules/git.nix
    ../modules/ssh.nix
    ../modules/spicetify.nix
    ../modules/papirus-folders.nix
  ];

  # ── Noctalia-shell ───────────────────────────────────────────────────────
  programs.noctalia-shell = {
    enable = true;
    package = null;
  };

  # ── Niri config ──────────────────────────────────────────────────────────
  xdg.configFile."niri" = {
    source = ../dotfiles/niri;
    recursive = true;
  };

  # ── Easyeffects preset ───────────────────────────────────────────────────
  xdg.configFile."easyeffects" = {
    source = ../dotfiles/easyeffects;
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
}
