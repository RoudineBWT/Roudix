{ pkgs, inputs, username, ... }:
{
  home.username = username;
  home.homeDirectory = "/home/${username}";
  home.stateVersion = "25.11";

  # ── Imports ──────────────────────────────────────────────────────────────
  imports = [
    inputs.noctalia.homeModules.default
    ./modules/fastfetch.nix
    ./modules/mangohud.nix
    ./modules/fish.nix
    ./modules/gaming-home.nix
    ./modules/git.nix
    ./modules/ssh.nix
  ];

  # ── Noctalia-shell ───────────────────────────────────────────────────────
  programs.noctalia-shell = {
    enable = true;
    package = null;
  };

  # ── Config Niri ──────────────────────────────────────────────────────────
  xdg.configFile."niri/config.kdl" = {
    source = ./niri/config.kdl;
  };

  # ── Packages home ────────────────────────────────────────────────────────
  home.packages = with pkgs; [
    # Niri / Wayland tools
    swww
    xwayland-satellite
    playerctl
    wl-clipboard
    pwvucontrol
    kdePackages.qtmultimedia
    mpvpaper

    # Apps
    ghostty
    starship
    nautilus
    zed-editor
    gnome-text-editor
    discord
    openrgb-with-all-plugins
    gnome-disk-utility
    mission-center
    loupe
    inkscape
    gimp
    clapper
    easyeffects
    rnnoise-plugin
    gpu-screen-recorder
    brave
    rustdesk

    # GTK theming
    nwg-look
    adw-gtk3
    papirus-icon-theme

    # Qt theming
    qt6Packages.qt6ct
    libsForQt5.qt5ct

    # Divers
    gvfs
    nh
    nvd
    ffmpeg
    capitaine-cursors
    btop
    cava

    # OBS Studio
    (pkgs.wrapOBS {
      plugins = with pkgs.obs-studio-plugins; [
        obs-pipewire-audio-capture
        obs-vkcapture
      ];
    })

    # Noctalia-shell
    inputs.noctalia.packages.${pkgs.stdenv.hostPlatform.system}.default
    # Zen Browser
    inputs.zen-browser.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];

  # ── Cursor ───────────────────────────────────────────────────────────────
  home.pointerCursor = {
    gtk.enable = true;
    x11.enable = true;
    package = pkgs.capitaine-cursors;
    name = "Capitaine Cursors White";
    size = 32;
  };

  programs.home-manager.enable = true;
}
