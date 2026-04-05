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
    starship
    nautilus
    gnome-text-editor
    (discord.override { withVencord = true; })
    (element-desktop.override { commandLineArgs = "--password-store=gnome-libsecret"; })
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
    rustdesk-flutter
    kodi-wayland

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

    # OBS Studio
    (pkgs.wrapOBS {
      plugins = with pkgs.obs-studio-plugins; [
        obs-pipewire-audio-capture
        obs-vkcapture
      ];
    })

    # Flake packages
    inputs.noctalia.packages.${pkgs.stdenv.hostPlatform.system}.default
    inputs.zen-browser.packages.${pkgs.stdenv.hostPlatform.system}.default
    inputs.firefox-nightly.packages.${pkgs.stdenv.hostPlatform.system}.firefox-nightly-bin
  ];
}
