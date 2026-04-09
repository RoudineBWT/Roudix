{ pkgs, inputs, username, ... }:
{
  home.username = username;
  home.homeDirectory = "/home/${username}";
  home.stateVersion = "25.11";

  imports = [
    ../modules/fastfetch.nix
    ../modules/fish.nix
    ../modules/bash.nix
    ../modules/git.nix
    ../modules/ssh.nix
    ../modules/spicetify.nix
    ../modules/gaming-home.nix
  ];

  # ── Easyeffects preset ───────────────────────────────────────────────────
  xdg.configFile."easyeffects" = {
    source = ../dotfiles/easyeffects;
    recursive = true;
  };

  home.packages = with pkgs; [
    # Common apps
    (pkgs.callPackage ../pkgs/roudix-switcher {})
    ghostty
    zed-editor
    btop
    ffmpeg
    nh
    nvd
    capitaine-cursors
    deluge-gtk
    (discord.override { withVencord = true; })
    (element-desktop.override { commandLineArgs = "--password-store=gnome-libsecret"; })
    openrgb-with-all-plugins
    rustdesk-flutter
    kodi-wayland
    inkscape
    gimp
    starship
    easyeffects
    rnnoise-plugin

       # OBS Studio
    (pkgs.wrapOBS {
      plugins = with pkgs.obs-studio-plugins; [
        obs-pipewire-audio-capture
        obs-vkcapture
      ];
    })

       # Flake packages
    inputs.zen-browser.packages.${pkgs.stdenv.hostPlatform.system}.twilight
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
